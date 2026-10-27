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
from hmda_reliability.review_ai.evidence import AgenticInvocationEvidence
from hmda_reliability.review_ai.prompt import render_canonical_input
from hmda_reliability.runtime_ai import provider as provider_module
from scripts import run_agentic_review_live as live_module
from tests.review_ai.test_live_harness import _live_environment

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    ("http_status", "failure_code", "attempts"),
    [
        (200, None, 1),
        (400, "provider_client_error", 1),
        (500, "provider_server_error", 2),
    ],
)
def test_harness_connects_reliability_review_sdk_and_persisted_provenance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    http_status: int,
    failure_code: str | None,
    attempts: int,
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
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": output.model_dump_json(),
                        },
                        "finish_reason": "stop",
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
    assert exit_code == (0 if http_status == 200 else 1), captured.err
    assert result.status == ("accepted" if http_status == 200 else "unavailable")
    assert result.failure_code == failure_code
    assert result.invocation_path is not None
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
    if http_status == 200:
        assert result.output == output == record.parsed_output
        assert record.trace_id == "cross-domain-request"
    else:
        assert result.output is None and record.parsed_output is None
    assert "live-test-secret" not in persisted + captured.out + captured.err
