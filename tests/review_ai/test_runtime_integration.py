"""Reliability material → Review AI → actual SDK → local provenance integration."""

from __future__ import annotations

import json
from functools import partial
from pathlib import Path

import httpx
import pytest
from openai import OpenAI

from hmda_reliability.review_ai import (
    AgenticReviewInput,
    AgenticReviewOutput,
    AgenticReviewResult,
    PromptIdentity,
)
from hmda_reliability.review_ai.evaluation import langfuse as projection
from hmda_reliability.review_ai.evidence import AgenticInvocationEvidence
from hmda_reliability.review_ai.prompt import render_canonical_input
from hmda_reliability.runtime_ai import provider as provider_module
from scripts import run_agentic_review_live as live_module
from tests.review_ai.test_live_harness import _live_environment

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    (
        "http_status",
        "failure_code",
        "attempts",
        "finish_reason",
        "response_case",
        "diagnostic_kind",
    ),
    [
        (200, None, 1, "stop", "valid", None),
        (200, None, 1, "length", "valid", None),
        (200, None, 1, [], "valid", None),
        (200, None, 1, {}, "valid", None),
        (
            200,
            "response_schema_invalid",
            1,
            "stop",
            "array_type",
            "schema_validation_failed",
        ),
        (
            200,
            "response_schema_invalid",
            1,
            "length",
            "truncated",
            "json_syntax_invalid",
        ),
        (
            200,
            "response_schema_invalid",
            1,
            "length",
            "content_null",
            "response_content_empty",
        ),
        (
            200,
            "response_schema_invalid",
            1,
            "stop",
            "choices_empty",
            "response_content_empty",
        ),
        (400, "provider_client_error", 1, "stop", "valid", None),
        (500, "provider_server_error", 2, "stop", "valid", None),
    ],
)
def test_harness_connects_reliability_review_sdk_and_persisted_provenance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    http_status: int,
    failure_code: str | None,
    attempts: int,
    finish_reason: object,
    response_case: str,
    diagnostic_kind: str | None,
) -> None:
    """HTTP만 통제하고 실제 review·retry·store와 CLI 검증을 연결한다."""
    environment = _live_environment(tmp_path)
    environment["HMDA_AGENTIC_REVIEW_MAX_RETRIES"] = "1"
    incident, evidence, draft = live_module._build_null_spike_material()
    review_input = AgenticReviewInput(
        incident=incident,
        evidence=[evidence],
        draft=draft,
        prompt_identity=PromptIdentity(),
        project_revision="revision-123",
    )
    output = AgenticReviewOutput(
        incident_id=incident.incident_id,
        incident_type="null_spike",
        target_column="income",
        deterministic_facts=review_input.deterministic_facts,
        review_summary="The supplied evidence describes an income null spike.",
        evidence_used=[evidence.evidence_id],
        findings=[],
        uncertainties=[],
        advisory_recommendation="needs_human_review",
    )
    payloads: list[dict[str, object]] = []
    response_content = output.model_dump_json()
    if response_case == "array_type":
        invalid_output = output.model_dump(mode="json")
        invalid_output["uncertainties"] = "PRIVATE_RESPONSE_VALUE"
        response_content = json.dumps(invalid_output)
    elif response_case == "truncated":
        response_content = '{"review_summary":"PRIVATE_RESPONSE_VALUE'
    projected: list[dict[str, object]] = []
    if response_case in {"array_type", "truncated"}:
        environment["HMDA_LANGFUSE_EXPORT"] = "true"

        def capture_projection(payload: dict[str, object], **kwargs: object) -> str:
            projected.append(payload)
            return "submitted_unverified"

        monkeypatch.setattr(projection, "export_projection", capture_projection)

    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
        payloads.append(json.loads(request.content))
        if http_status != 200:
            return httpx.Response(http_status, json={"error": {"message": "fixture"}})
        return httpx.Response(
            200,
            headers={"x-request-id": "cross-domain-request"},
            json={
                "id": "cross-domain-completion",
                "object": "chat.completion",
                "created": 0,
                "model": "local-model",
                "choices": []
                if response_case == "choices_empty"
                else [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": None
                            if response_case == "content_null"
                            else response_content,
                        },
                        "finish_reason": finish_reason,
                    }
                ],
            },
        )

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        monkeypatch.setattr(
            provider_module, "OpenAI", partial(OpenAI, http_client=client)
        )
        exit_code = live_module.main(env=environment)

    captured = capsys.readouterr()
    result = AgenticReviewResult.model_validate_json(captured.out)
    expected_status = (
        "unavailable"
        if http_status != 200
        else "validation_failed"
        if failure_code
        else "accepted"
    )
    assert exit_code == (0 if expected_status == "accepted" else 1), captured.err
    assert result.status == expected_status
    assert result.failure_code == failure_code
    assert result.invocation_path is not None
    if http_status == 200:
        assert result.response_path is not None
        assert result.response_path == (
            tmp_path
            / "artifacts"
            / "agentic-review"
            / "responses"
            / f"{result.invocation_id}.txt"
        )
        expected_body = (
            ""
            if response_case in {"content_null", "choices_empty"}
            else response_content
        )
        assert result.response_path.read_bytes() == expected_body.encode("utf-8")
    else:
        assert result.response_path is None
        assert not (tmp_path / "artifacts" / "agentic-review" / "responses").exists()
    persisted = result.invocation_path.read_text(encoding="utf-8")
    record = AgenticInvocationEvidence.model_validate_json(persisted)
    assert record.status == result.status
    assert record.failure_code == failure_code
    assert record.attempt_count == len(payloads) == attempts
    assert record.project_revision == "revision-123"
    assert record.configuration.model == "local-model"
    replay = render_canonical_input(
        record.canonical_input,
        record.prompt_identity,
        max_prompt_bytes=record.configuration.max_prompt_bytes,
    )
    assert record.prompt_digest == replay.prompt_digest
    assert (
        payloads
        == [
            {
                "model": "local-model",
                "temperature": 0,
                "max_tokens": 512,
                "response_format": {"type": "json_object"},
                "stream": False,
                "messages": [
                    message.model_dump(mode="json") for message in replay.messages
                ],
            }
        ]
        * attempts
    )
    assert [message.role for message in replay.messages] == ["system", "user"]
    if expected_status == "accepted":
        assert result.output == output == record.parsed_output
    else:
        assert result.output is None and record.parsed_output is None
    if http_status == 200:
        assert record.trace_id == "cross-domain-request"
        assert record.response_metadata is not None
        assert record.response_metadata.finish_reason == (
            None
            if response_case == "choices_empty"
            else finish_reason
            if finish_reason in ("stop", "length")
            else "unknown"
        )
    if diagnostic_kind is None:
        assert record.response_diagnostics is None
    else:
        assert record.response_diagnostics is not None
        assert record.response_diagnostics.kind == diagnostic_kind
    assert "PRIVATE_RESPONSE_VALUE" not in persisted + captured.out + captured.err
    assert "live-test-secret" not in persisted + captured.out + captured.err
    if response_case in {"array_type", "truncated"}:
        assert len(projected) == 1
        assert set(projected[0]) == {"metadata"}
        encoded_projection = json.dumps(projected[0])
        assert "PRIVATE_RESPONSE_VALUE" not in encoded_projection
        assert "response_path" not in encoded_projection
