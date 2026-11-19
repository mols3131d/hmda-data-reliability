import json
from importlib.resources import files
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from langfuse.api import Prompt_Chat
from langfuse.model import ChatPromptClient

from hmda_reliability.data_operations.request import DataOperationRequest
from hmda_reliability.reliability_ai.ingestion import (
    investigate_ingestion,
    replay_ingestion,
)
from hmda_reliability.runtime_ai.contracts import ProviderResponse, ToolCall

pytestmark = pytest.mark.component


def response(*calls: ToolCall, **output: Any) -> ProviderResponse:
    return ProviderResponse(
        content=json.dumps(output) if output else "",
        tool_calls=calls,
        attempt_count=1,
        latency_ms=2,
    )


def tool(name: str = "inspect_source", **args: Any) -> ToolCall:
    return ToolCall.model_validate(
        {"id": "prop-1", "function": {"name": name, "arguments": json.dumps(args)}}
    )


def setup_review(tmp_path: Path) -> DataOperationRequest:
    raw = tmp_path / "raw"
    raw.mkdir()
    for year in (2024, 2025):
        (raw / f"{year}.csv").write_text("activity_year\n2025\n")
    return DataOperationRequest(source_root=raw)


def native_client() -> MagicMock:
    client = MagicMock()
    instructions = (
        files("hmda_reliability.reliability_ai.prompt")
        .joinpath("ingestion.md")
        .read_text(encoding="utf-8")
    )
    client.get_prompt.return_value = ChatPromptClient(
        Prompt_Chat(
            name="hmda-reliability-ai/ingestion",
            version=11,
            prompt=[
                {"role": "system", "content": instructions},
                {"role": "user", "content": "{{canonical_input}}"},
            ],
            config={},
            labels=["test"],
            tags=[],
        )
    )
    return client


def test_rule_shortcut_and_replay_do_not_fetch_prompt(tmp_path):
    raw = tmp_path / "source"
    raw.mkdir()
    client = MagicMock()
    provider = MagicMock()
    result = investigate_ingestion(
        "prepare",
        request=DataOperationRequest(source_root=raw),
        artifact_root=tmp_path,
        client=client,
        provider=provider,
    )
    assert (result["status"], result["next_action"], result["termination"]) == (
        "blocked",
        "correct_input",
        "completed",
    )
    client.get_prompt.assert_not_called()
    provider.invoke.assert_not_called()
    raw.rmdir()
    replay = replay_ingestion(result["investigation_id"], artifact_root=tmp_path)
    assert (
        replay["status"] == result["status"]
        and replay["next_action"] == result["next_action"]
    )
    assert replay["investigation_id"] != result["investigation_id"]


def test_observed_tool_is_bound_to_model_followup_and_offline_replay(tmp_path):
    req = setup_review(tmp_path)
    provider = MagicMock()

    def invoke(messages, **kwargs):
        if messages[-1].role == "tool":
            assert messages[-1].tool_call_id == "prop-1"
            assert json.loads(messages[-1].content)["value"]["source_id"] == "source-2"
            return response(
                next_action="correct_input",
                evidence_ids=["prop-1"],
                hypotheses=["columns missing"],
            )
        return response(tool(source_id="source-2"))

    provider.invoke.side_effect = invoke
    client = native_client()
    result = investigate_ingestion(
        "prepare", request=req, artifact_root=tmp_path, client=client, provider=provider
    )
    assert (
        result["status"],
        result["termination"],
        result["advisory"]["evidence_ids"],
    ) == ("blocked", "completed", ["prop-1"])
    assert provider.invoke.call_count == 2
    client.get_prompt.assert_called_once()
    replay = replay_ingestion(result["investigation_id"], artifact_root=tmp_path)
    assert replay["advisory"] == result["advisory"]
    d = tmp_path / "ingestion" / result["investigation_id"]
    (d / "event-1.json").write_text("{}")
    assert (
        replay_ingestion(result["investigation_id"], artifact_root=tmp_path)[
            "termination"
        ]
        == "corrupt_evidence"
    )


@pytest.mark.parametrize(
    "message",
    [
        response(tool(source_id="outside")),
        response(tool(source_id="source-1"), tool(source_id="source-2")),
        response(next_action="continue_load", evidence_ids=["initial"], hypotheses=[]),
    ],
)
def test_invalid_proposals_stop_before_lookup(tmp_path, message):
    req = setup_review(tmp_path)
    provider = MagicMock()
    provider.invoke.return_value = message
    result = investigate_ingestion(
        "prepare",
        request=req,
        artifact_root=tmp_path,
        client=native_client(),
        provider=provider,
    )
    assert result["status"] == "blocked"
    assert (
        result["termination"] != "completed"
        and result["next_action"] == "request_confirmation"
    )
    assert result["observation_ids"] == []
    provider.invoke.assert_called_once()


@pytest.mark.parametrize(
    "metadata",
    [
        {"finish_reason": "length", "content_state": "text", "content_bytes": 4},
        {
            "finish_reason": "content_filter",
            "content_state": "text",
            "content_bytes": 4,
        },
        None,
    ],
)
def test_truncated_or_malformed_advice_stops(tmp_path, metadata):
    from hmda_reliability.runtime_ai.contracts import ProviderResponseMetadata

    req = setup_review(tmp_path)
    provider = MagicMock()
    answer = response(
        next_action="correct_input", evidence_ids=["initial"], hypotheses=[]
    )
    update = (
        {"response_metadata": ProviderResponseMetadata.model_validate(metadata)}
        if metadata
        else {"raw_tool_calls": "malformed"}
    )
    provider.invoke.return_value = answer.model_copy(update=update)
    result = investigate_ingestion(
        "prepare",
        request=req,
        artifact_root=tmp_path,
        client=native_client(),
        provider=provider,
    )
    assert result["termination"] != "completed" and result["advisory"] is None


@pytest.mark.parametrize("synthetic", [False, True])
def test_observation_failure_preserves_local_result_and_call_count(tmp_path, synthetic):
    request = setup_review(tmp_path)
    provider = MagicMock()
    provider.invoke.return_value = response(
        next_action="correct_input",
        evidence_ids=["initial"],
        hypotheses=["LOCAL_ONLY_BODY"],
    )
    client = native_client()
    client.flush.side_effect = RuntimeError("offline")
    result = investigate_ingestion(
        "prepare",
        request=request,
        client=client,
        provider=provider,
        artifact_root=tmp_path,
        synthetic=synthetic,
    )
    assert (
        result["termination"] == "completed"
        and result["observation"]["status"] == "submission_failed"
    )
    provider.invoke.assert_called_once()
    assert ("input" in client.start_observation.call_args.kwargs) == synthetic
    assert "LOCAL_ONLY_BODY" not in str(client.mock_calls) and str(
        request.source_root
    ) not in str(client.mock_calls)
    replay = replay_ingestion(result["investigation_id"], artifact_root=tmp_path)
    assert replay["advisory"] == result["advisory"]


def test_run_review_model_uses_failed_stage_evidence(tmp_path):
    from hmda_reliability.reliability_ai.ingestion import RunRef

    reader = MagicMock()

    def stage_result(run, stage, prepared, **_):
        return {
            "stage": stage,
            "state": "failed" if stage == "quality_gate" else "success",
            "try_number": 1,
            "data_update": "unknown",
            "input_match": "unknown",
        }

    reader.read.side_effect = stage_result
    provider = MagicMock()
    provider.invoke.side_effect = [
        response(tool("read_stage_result", stage="quality_gate")),
        response(
            next_action="inspect_execution",
            evidence_ids=["prop-1"],
            hypotheses=["check the gate"],
        ),
    ]
    result = investigate_ingestion(
        "review_run",
        run=RunRef(run_id="manual__test"),
        reader=reader,
        provider=provider,
        client=native_client(),
        artifact_root=tmp_path,
    )
    assert (
        result["status"] == "reviewed" and result["next_action"] == "inspect_execution"
    )
    message = provider.invoke.call_args.args[0][-1]
    assert (
        message.tool_call_id == "prop-1"
        and json.loads(message.content)["value"]["state"] == "failed"
    )
    assert (
        replay_ingestion(result["investigation_id"], artifact_root=tmp_path)[
            "next_action"
        ]
        == "inspect_execution"
    )


def test_foreign_observation_is_excluded_from_followup(tmp_path, monkeypatch):
    from hmda_reliability.reliability_ai.ingestion import service

    source = setup_review(tmp_path)
    provider = MagicMock()
    provider.invoke.return_value = response(tool(source_id="source-1"))
    real = service._Events.boundary

    def substitute(self, kind, get):
        if kind == "lookup":
            observation = get()
            return real(
                self, kind, lambda: {**observation, "proposal_id": "another-proposal"}
            )
        return real(self, kind, get)

    monkeypatch.setattr(service._Events, "boundary", substitute)
    result = investigate_ingestion(
        "prepare",
        request=source,
        provider=provider,
        client=native_client(),
        artifact_root=tmp_path,
    )
    assert result["termination"] == "observation_mismatch"
    assert result["observation_ids"] == []
    provider.invoke.assert_called_once()
