"""도구 기반 단일 에이전트 인시던트 조사 서비스 모듈."""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from hmda_reliability.reliability_ai.contracts import AgenticReviewInput
from hmda_reliability.reliability_ai.investigation.contracts import (
    InvestigationResult,
    InvestigationTurnRecord,
    ToolCallRecord,
)
from hmda_reliability.reliability_ai.investigation.tools import ToolRegistry
from hmda_reliability.reliability_ai.prompt import canonical_json_bytes
from hmda_reliability.reliability_ai.settings import ReliabilityAISettings
from hmda_reliability.reliability_ai.store import (
    InvocationEvidenceStoreError,
    InvocationResponseStore,
    write_review_json,
)
from hmda_reliability.runtime_ai.contracts import ChatMessage, ProviderResponse
from hmda_reliability.runtime_ai.provider import (
    OpenAICompatibleAdapter,
    ProviderResponseTooLargeError,
    ProviderUnavailableError,
)
from hmda_reliability.runtime_ai.settings import RuntimeAISettings

_SYSTEM_PROMPT = """당신은 HMDA 데이터 신뢰성 인시던트를 조사하는 에이전트입니다.
제공된 정보와 조치 초안을 검토하고, 필요한 경우 도구를 호출해 증거를 확인하세요.
조사가 완료되면 다음 JSON 형식으로 최종 보고서를 반환하세요:
{
  "facts": {"column": "...", "observed_issue": "..."},
  "findings": [{"topic": "...", "description": "...", "evidence_refs": ["..."]}],
  "hypotheses": [
    {"hypothesis": "...", "status": "supported|rejected|uncertain", "rationale": "..."}
  ],
  "uncertainties": [{"topic": "...", "description": "...", "needed_evidence": "..."}]
}
주의:
- 확인되지 않은 사실을 추측으로 단정하지 마세요.
- 도구 호출 결과와 인시던트 데이터에 근거해서만 판단하세요.
- 데이터베이스 변경이나 승인 권한이 없으므로 직접 수정을 시도하지 마세요.
"""


def investigate_incident(
    review_input: AgenticReviewInput,
    *,
    settings: RuntimeAISettings,
    ai_settings: ReliabilityAISettings | None = None,
    provider: OpenAICompatibleAdapter | None = None,
    tool_registry: ToolRegistry | None = None,
    allowed_tools: tuple[str, ...] | None = None,
    dbt_artifact_paths: tuple[Path, Path] | None = None,
    artifact_root: Path = Path(".local/artifacts"),
    clock: Callable[[], float] = time.monotonic,
) -> InvestigationResult:
    """도구 호출을 동적으로 수행하며 인시던트의 원인, 증거, 불확실성을 조사한다."""
    active_ai_settings = ai_settings or ReliabilityAISettings()
    adapter = provider or OpenAICompatibleAdapter(settings, clock=clock)
    registry = tool_registry or ToolRegistry.from_review_input(
        review_input,
        allowed_tools=allowed_tools,
        dbt_artifact_paths=dbt_artifact_paths,
    )
    tools = tuple(
        definition
        for definition in registry.definitions
        if allowed_tools is None or definition.function.name in allowed_tools
    )
    tool_names = {definition.function.name for definition in tools}

    started_at = clock()
    deadline = started_at + active_ai_settings.workflow_budget_seconds
    incident = review_input.incident

    initial_user_message = json.dumps(
        {
            "incident": {
                "incident_id": incident.incident_id,
                "incident_type": incident.incident_type,
                "asset_name": incident.asset_name,
                "partition": incident.partition,
                "severity": incident.severity.value,
                "status": incident.status.value,
                "evidence_refs": incident.evidence_refs,
            },
            "draft_summary": review_input.draft.rca_summary,
            "recommended_actions": review_input.draft.recommended_actions,
        },
        ensure_ascii=False,
    )

    messages: list[ChatMessage] = [
        ChatMessage(role="system", content=_SYSTEM_PROMPT),
        ChatMessage(role="user", content=initial_user_message),
    ]

    all_tool_records: list[ToolCallRecord] = []
    executed_call_fingerprints: set[str] = set()
    turns: list[InvestigationTurnRecord] = []

    invocation_id = f"inv-{uuid.uuid4().hex}"
    store = InvocationResponseStore(artifact_root)
    response_paths: list[Path] = []
    max_turns = active_ai_settings.max_tool_calls + 2

    def finish(
        status: str,
        failure_code: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> InvestigationResult:
        common = {
            "incident_id": incident.incident_id,
            "invocation_id": invocation_id,
            "tool_calls": tuple(all_tool_records),
            "response_paths": tuple(response_paths),
            "turns": tuple(turns),
        }
        try:
            result = InvestigationResult.model_validate(
                {
                    **common,
                    "status": status,
                    "failure_code": failure_code,
                    **(payload or {}),
                }
            )
        except ValidationError:
            result = InvestigationResult.model_validate(
                {
                    **common,
                    "status": "error",
                    "failure_code": "invalid_investigation_output",
                }
            )
        try:
            result.model_dump(mode="json")
        except (ValueError, RecursionError):
            safe_records: list[ToolCallRecord] = []
            for record in all_tool_records:
                try:
                    record.model_dump(mode="json")
                except (ValueError, RecursionError):
                    record = record.model_copy(
                        update={
                            "arguments": {},
                            "result": {
                                "error": "unserializable_tool_record",
                                "raw_evidence": "investigation turns",
                            },
                            "status": "error",
                        }
                    )
                safe_records.append(record)
            result = InvestigationResult.model_validate(
                {
                    **common,
                    "tool_calls": tuple(safe_records),
                    "status": "error",
                    "failure_code": "invalid_investigation_output",
                }
            )
            result.model_dump(mode="json")
        manifest_path = (
            artifact_root
            / "reliability-ai"
            / "investigations"
            / f"{invocation_id}.json"
        )
        result = result.model_copy(update={"manifest_path": manifest_path})
        try:
            write_review_json(
                manifest_path,
                {
                    "project_revision": review_input.project_revision,
                    "input_digest": "sha256:"
                    + hashlib.sha256(
                        canonical_json_bytes(review_input.model_dump(mode="json"))
                    ).hexdigest(),
                    "evidence_refs": list(incident.evidence_refs),
                    "runtime_configuration": settings.sanitized_configuration(),
                    "ai_configuration": active_ai_settings.sanitized_configuration(),
                    "allowed_tools": sorted(tool_names),
                    "result": result.model_dump(mode="json"),
                },
                max_record_bytes=active_ai_settings.max_prompt_bytes
                + settings.max_output_bytes * (max_turns + 1) * 4
                + 65_536,
            )
        except (InvocationEvidenceStoreError, ValueError):
            return result.model_copy(
                update={
                    "status": "error",
                    "failure_code": "manifest_persistence_failed",
                    "manifest_path": None,
                }
            )
        return result

    for turn in range(max_turns):
        remaining_budget = max(0.0, deadline - clock())
        if remaining_budget <= 0:
            return finish("budget_exhausted", "workflow_budget_exhausted")

        if (
            len(
                canonical_json_bytes(
                    [message.model_dump(mode="json") for message in messages]
                )
            )
            > active_ai_settings.max_prompt_bytes
        ):
            return finish("budget_exhausted", "prompt_budget_exhausted")

        available_tools = (
            tools if len(all_tool_records) < active_ai_settings.max_tool_calls else ()
        )
        turn_start = clock()
        remaining_budget = max(0.0, deadline - turn_start)
        if remaining_budget <= 0:
            return finish("budget_exhausted", "workflow_budget_exhausted")
        try:
            response: ProviderResponse = adapter.invoke(
                tuple(messages),
                output_format="text",
                budget_seconds=remaining_budget,
                tools=available_tools or None,
                tool_choice="auto" if available_tools else "none",
            )
        except ProviderUnavailableError as exc:
            return finish("error", exc.failure_code)
        except ProviderResponseTooLargeError:
            return finish("error", "provider_response_too_large")

        turn_latency = max(0.0, (clock() - turn_start) * 1000)
        turns.append(
            InvestigationTurnRecord(
                turn=turn,
                role="assistant",
                content=response.content,
                tool_calls=tuple(
                    call.model_dump(mode="json") for call in response.tool_calls
                ),
                latency_ms=turn_latency,
            )
        )
        try:
            response_paths.append(
                store.write(
                    f"{invocation_id}-{turn}",
                    response.content,
                    max_response_bytes=settings.max_output_bytes,
                )
            )
        except InvocationEvidenceStoreError:
            return finish("error", "response_persistence_failed")

        if clock() >= deadline:
            return finish("budget_exhausted", "workflow_budget_exhausted")

        if response.tool_calls:
            assistant_msg = ChatMessage(
                role="assistant",
                content=response.content,
                tool_calls=response.tool_calls,
            )
            messages.append(assistant_msg)
            for call in response.tool_calls:
                if len(all_tool_records) >= active_ai_settings.max_tool_calls:
                    return finish("budget_exhausted", "tool_call_budget_exhausted")
                if clock() >= deadline:
                    return finish("budget_exhausted", "workflow_budget_exhausted")
                if call.function.name not in tool_names:
                    return finish("error", "tool_not_allowed")
                try:
                    arguments = json.loads(call.function.arguments or "{}")
                    fingerprint = (
                        f"{call.function.name}:"
                        f"{canonical_json_bytes(arguments).decode('utf-8')}"
                    )
                except RecursionError:
                    return finish("error", "invalid_investigation_output")
                except ValueError:
                    fingerprint = (
                        f"{call.function.name}:{call.function.arguments.strip()}"
                    )
                if fingerprint in executed_call_fingerprints:
                    return finish("tool_cycle_detected", "duplicate_tool_call_cycle")
                executed_call_fingerprints.add(fingerprint)

                if clock() >= deadline:
                    return finish("budget_exhausted", "workflow_budget_exhausted")
                record, tool_output = registry.execute(call)
                all_tool_records.append(record)
                turns.append(
                    InvestigationTurnRecord(
                        turn=turn,
                        role="tool",
                        tool_call_id=call.id,
                        content=tool_output,
                        latency_ms=record.latency_ms,
                    )
                )
                messages.append(
                    ChatMessage(
                        role="tool",
                        tool_call_id=call.id,
                        content=tool_output,
                    )
                )

            if len(all_tool_records) >= active_ai_settings.max_tool_calls:
                messages.append(
                    ChatMessage(
                        role="user",
                        content=(
                            "도구 호출 한도에 도달했습니다. "
                            "현재까지 확인된 정보로 최종 JSON 보고서를 작성하세요."
                        ),
                    )
                )

            continue

        try:
            parsed_data = _parse_investigation_payload(response.content)
        except (ValueError, RecursionError):
            return finish("error", "invalid_investigation_output")
        return finish(
            "completed",
            payload={
                field: parsed_data.get(field, {} if field == "facts" else [])
                for field in ("facts", "findings", "hypotheses", "uncertainties")
            },
        )

    return finish("budget_exhausted", "max_turns_exceeded")


def _parse_investigation_payload(content: str) -> dict[str, Any]:
    """최종 JSON 객체를 파싱하고 비정형 응답은 거부한다."""
    text = content.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("investigation output must be a JSON object")
    return data
