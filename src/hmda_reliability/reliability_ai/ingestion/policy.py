"""적재 판정은 확인된 근거로 계산하고, 모델 권고를 허용된 후속 조치로 제한한다."""

from __future__ import annotations

import json
from typing import Any

from hmda_reliability.reliability_ai.ingestion.airflow import STAGES
from hmda_reliability.runtime_ai.contracts import ToolCall, ToolDefinition


def initial_handoff(mode: str, initial: dict[str, Any]) -> tuple[str, str | None]:
    if mode == "prepare":
        state = initial["status"]
        if state == "ready":
            return state, "continue_load"
        if state == "blocked":
            if sum(bool(s["missing_columns"]) for s in initial["sources"]) > 1:
                return state, None
            return state, "correct_input"
        return state, "request_confirmation"
    stages = initial["stages"]
    if any(s["state"] in ("failed", "upstream_failed") for s in stages):
        return "reviewed", None
    if any(s["state"] == "unknown" for s in stages):
        return "needs_human", "request_confirmation"
    if all(s["state"] in ("success", "skipped") for s in stages):
        return "reviewed", "none" if stages[0][
            "input_match"
        ] == "matched" else "request_confirmation"
    return "reviewed", "inspect_execution"


def tool_definitions(mode: str, initial: dict[str, Any]) -> tuple[ToolDefinition, ...]:
    fields = (
        {"read_stage_result": ("stage", list(STAGES))}
        if mode == "review_run"
        else {
            "list_sources": None,
            "inspect_input_partition": None,
            "inspect_source": (
                "source_id",
                [s["source_id"] for s in initial["sources"]],
            ),
        }
    )
    tools = []
    for name, arg in fields.items():
        props = {arg[0]: {"type": "string", "enum": arg[1]}} if arg else {}
        tools.append(
            ToolDefinition.model_validate(
                {
                    "function": {
                        "name": name,
                        "description": "Read a scoped ingestion observation.",
                        "parameters": {
                            "type": "object",
                            "properties": props,
                            "required": list(props),
                            "additionalProperties": False,
                        },
                    }
                }
            )
        )
    return tuple(tools)


def lookup(
    call: ToolCall, tools: tuple[ToolDefinition, ...], initial: dict[str, Any]
) -> tuple[str, dict[str, Any]]:
    name = call.function.name
    arguments = json.loads(call.function.arguments)
    spec = next((t.function.parameters for t in tools if t.function.name == name), None)
    if (
        spec is None
        or not isinstance(arguments, dict)
        or set(arguments) != set(spec["required"])
    ):
        raise ValueError("invalid_tool_request")
    for field, value in arguments.items():
        if value not in spec["properties"][field]["enum"]:
            raise ValueError("out_of_scope")
    if name == "read_stage_result":
        value = next(s for s in initial["stages"] if s["stage"] == arguments["stage"])
    elif name == "inspect_source":
        item = next(
            s for s in initial["sources"] if s["source_id"] == arguments["source_id"]
        )
        value = {k: v for k, v in item.items() if k != "name"}
    elif name == "list_sources":
        value = {
            "sources": [
                {"source_id": s["source_id"], "format": s["format"]}
                for s in initial["sources"]
            ]
        }
    else:
        value = {k: initial[k] for k in ("parse_status", "row_count")}
    key = json.dumps([name, arguments], sort_keys=True)
    return key, value


def advisory(
    content: str, mode: str, status: str, evidence: set[str]
) -> dict[str, Any]:
    proposal = json.loads(content)
    if not isinstance(proposal, dict) or set(proposal) != {
        "next_action",
        "evidence_ids",
        "hypotheses",
    }:
        raise ValueError("invalid_advisory")
    refs = proposal["evidence_ids"]
    if (
        not isinstance(refs, list)
        or not refs
        or any(not isinstance(ref, str) or ref not in evidence for ref in refs)
    ):
        raise ValueError("unknown_evidence")
    actions = (
        {"inspect_execution", "request_confirmation", "none"}
        if mode == "review_run"
        else {
            "ready": {"continue_load", "request_confirmation"},
            "blocked": {"correct_input", "request_confirmation"},
            "needs_human": {"request_confirmation"},
        }[status]
    )
    if (
        proposal["next_action"] not in actions
        or (mode == "review_run" and proposal["next_action"] == "none")
        or not isinstance(proposal["hypotheses"], list)
        or not all(isinstance(h, str) for h in proposal["hypotheses"])
    ):
        raise ValueError("invalid_advisory")
    return proposal
