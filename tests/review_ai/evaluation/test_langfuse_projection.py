"""Synthetic projection boundaries; no live provider or Langfuse project."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import time
from copy import deepcopy
from datetime import UTC, datetime
from queue import Queue
from types import SimpleNamespace
from typing import Any, cast

import pytest

from hmda_reliability.review_ai.contracts import (
    AgenticReviewInput,
    AgenticReviewOutput,
    AgenticReviewValidation,
    PromptIdentity,
)
from hmda_reliability.review_ai.evaluation import RubricCriterion, review_output_digest
from hmda_reliability.review_ai.evaluation import langfuse as projection
from hmda_reliability.review_ai.evidence import (
    AgenticInvocationEvidence,
    SanitizedAgenticReviewConfiguration,
)
from hmda_reliability.review_ai.prompt import (
    build_canonical_input,
    render_canonical_input,
    render_review_prompt,
)
from scripts.run_agentic_review_live import _build_null_spike_material


@pytest.fixture
def record() -> AgenticInvocationEvidence:
    incident, evidence, draft = _build_null_spike_material()
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
        target_column=review_input.target_column,
        deterministic_facts=review_input.deterministic_facts,
        review_summary="Inspect the income evidence.",
        evidence_used=[evidence.evidence_id],
        findings=[],
        uncertainties=[],
        advisory_recommendation="needs_human_review",
    )
    return AgenticInvocationEvidence(
        invocation_id="inv-test",
        recorded_at=datetime(2026, 9, 26, tzinfo=UTC),
        status="accepted",
        configuration=SanitizedAgenticReviewConfiguration(
            base_url="https://provider.invalid",
            model="test-model",
            timeout_seconds=5,
            max_retries=0,
            temperature=0,
            max_output_tokens=1024,
            max_prompt_bytes=65536,
            max_output_bytes=32768,
        ),
        prompt_identity=PromptIdentity(),
        prompt_digest=render_review_prompt(
            review_input, max_prompt_bytes=65536
        ).prompt_digest,
        project_revision="revision-123",
        incident_id=incident.incident_id,
        evidence_refs=(evidence.evidence_id,),
        canonical_input=build_canonical_input(review_input),
        parsed_output=output,
        validation=AgenticReviewValidation(status="accepted", violations=[]),
        latency_ms=123,
        attempt_count=1,
        trace_id="private-provider-trace",
    )


@pytest.fixture
def valid_annotation(record):
    payload = projection.project_invocation(
        record, expected_input=record.canonical_input
    )
    target = {
        key: payload["metadata"][key]
        for key in ("invocation_id", "output_digest", "rubric_id")
    }
    scores = [
        {"criterion": criterion.value, "score": 1, "rationale": "Test rationale."}
        for criterion in RubricCriterion
    ]
    return payload, target, scores


@pytest.mark.unit
def test_projection_keeps_exact_context_and_output_without_provider_secrets(record):
    incident, evidence, draft = _build_null_spike_material()
    expected_input = build_canonical_input(
        AgenticReviewInput(
            incident=incident,
            evidence=[evidence],
            draft=draft,
            prompt_identity=record.prompt_identity,
            project_revision=record.project_revision,
        )
    )
    expected_input = dict(reversed(expected_input.items()))
    payload = projection.project_invocation(record, expected_input=expected_input)
    assert payload["input"] == record.canonical_input
    assert payload["output"] == record.parsed_output.model_dump(mode="json")
    assert payload["metadata"]["prompt_digest"] == record.prompt_digest
    assert payload["metadata"]["output_digest"] == review_output_digest(
        record.parsed_output
    )
    assert payload["metadata"]["recorded_latency_ms"] == 123
    assert payload["metadata"]["rubric_id"] == "rubric_v1"
    encoded = json.dumps(payload)
    assert "provider.invalid" not in encoded
    assert "private-provider-trace" not in encoded
    assert "base_url" not in encoded


@pytest.mark.unit
def test_mismatched_input_and_oversize_are_rejected_without_truncation(record):
    with pytest.raises(ValueError):
        projection.project_invocation(record, expected_input={})
    large = record.model_copy(update={"project_revision": "x" * 66000})
    with pytest.raises(ValueError):
        projection.project_invocation(large, expected_input=record.canonical_input)


@pytest.mark.integration
def test_projection_rejects_boolean_integer_mismatch_with_recomputed_digest(
    record, tmp_path, monkeypatch, capsys
):
    from hmda_reliability.review_ai.contracts import AgenticReviewResult
    from scripts import run_agentic_review_live as harness

    modified_input = deepcopy(record.canonical_input)
    draft = modified_input["draft"]
    draft["requires_approval"] = int(draft["requires_approval"])
    prompt = render_canonical_input(
        modified_input,
        record.prompt_identity,
        max_prompt_bytes=record.configuration.max_prompt_bytes,
    )
    modified = record.model_copy(
        update={
            "canonical_input": modified_input,
            "prompt_digest": prompt.prompt_digest,
        }
    )
    persisted = AgenticInvocationEvidence.model_validate_json(
        modified.model_dump_json()
    )

    assert persisted.canonical_input == record.canonical_input
    assert persisted.prompt_digest != record.prompt_digest
    with pytest.raises(ValueError, match="record does not match synthetic input"):
        projection.project_invocation(persisted, expected_input=record.canonical_input)

    path = tmp_path / "invocation.json"
    path.write_text(persisted.model_dump_json(), encoding="utf-8")
    before = path.read_bytes()
    result = AgenticReviewResult(
        status="accepted",
        output=persisted.parsed_output,
        validation=persisted.validation,
        invocation_id=persisted.invocation_id,
        invocation_path=path,
    )
    # 출처 검증이 설정 전체를 대조하므로 fixture에 기록된 호출 조건을 명시한다.
    env = {
        **_environment(),
        "HMDA_AGENTIC_REVIEW_LIVE": "true",
        "HMDA_AGENTIC_REVIEW_MODE": "structured",
        "HMDA_AGENTIC_REVIEW_BASE_URL": "https://provider.invalid",
        "HMDA_AGENTIC_REVIEW_API_KEY": "provider-secret",
        "HMDA_AGENTIC_REVIEW_MODEL": "test-model",
        "HMDA_AGENTIC_REVIEW_TIMEOUT_SECONDS": "5",
        "HMDA_AGENTIC_REVIEW_MAX_RETRIES": "0",
        "HMDA_AGENTIC_REVIEW_PROJECT_REVISION": "revision-123",
    }

    def forbidden(*args, **kwargs):
        pytest.fail("mismatched synthetic input must not be exported")

    monkeypatch.setattr(projection, "export_projection", forbidden)
    assert harness.main(env=env, reviewer=lambda **kwargs: result) == 0
    assert path.read_bytes() == before
    captured = capsys.readouterr()
    assert "Langfuse projection: projection_failed" in captured.err
    assert json.loads(captured.out)["status"] == "accepted"


@pytest.mark.unit
@pytest.mark.parametrize("status", ["unavailable", "validation_failed"])
def test_failed_record_excludes_input_output_and_free_text(record, status):
    failed = record.model_copy(
        update={"status": type(record.status)(status), "failure_code": "secret-error"}
    )
    payload = projection.project_invocation(
        failed, expected_input=record.canonical_input
    )
    assert set(payload) == {"metadata"}
    assert payload["metadata"] == {
        "invocation_id": "inv-test",
        "project_revision": "revision-123",
        "status": status,
    }


@pytest.mark.unit
def test_annotation_requires_exact_target_and_each_valid_score_once(valid_annotation):
    payload, target, scores = valid_annotation
    assert projection.annotation_complete(payload, target=target, scores=scores)
    assert not projection.annotation_complete(
        payload, target={**target, "output_digest": "wrong"}, scores=scores
    )
    assert not projection.annotation_complete(
        payload, target=target, scores=scores[:-1]
    )
    assert not projection.annotation_complete(
        payload, target=target, scores=[scores[0]] * 5
    )
    for value in (-1, 3, True, 1.0, "1"):
        invalid = [{**scores[0], "score": value}, *scores[1:]]
        assert not projection.annotation_complete(
            payload, target=target, scores=invalid
        )
    assert not projection.annotation_complete(
        payload, target=target, scores=[{**scores[0], "rationale": " "}, *scores[1:]]
    )


@pytest.mark.unit
def test_annotation_rejects_unsupported_rubric_even_when_target_matches(
    valid_annotation,
):
    payload, target, scores = valid_annotation
    payload["metadata"]["rubric_id"] = "rubric_v2"
    target["rubric_id"] = "rubric_v2"

    assert not projection.annotation_complete(payload, target=target, scores=scores)


@pytest.mark.unit
def test_annotation_rejects_digest_that_only_matches_modified_metadata(
    valid_annotation,
):
    payload, target, scores = valid_annotation
    payload["metadata"]["output_digest"] = "sha256:" + "0" * 64
    target["output_digest"] = payload["metadata"]["output_digest"]

    assert not projection.annotation_complete(payload, target=target, scores=scores)


@pytest.mark.unit
def test_annotation_rejects_changed_output(valid_annotation):
    payload, target, scores = valid_annotation
    payload["output"]["review_summary"] = "A different accepted output."

    assert not projection.annotation_complete(payload, target=target, scores=scores)


@pytest.mark.unit
def test_annotation_rejects_output_changed_by_model_coercion(valid_annotation):
    payload, target, scores = valid_annotation
    payload["output"]["deterministic_facts"]["baseline_null_rate"] = "0.01"

    assert not projection.annotation_complete(payload, target=target, scores=scores)


@pytest.mark.unit
@pytest.mark.parametrize("output", [None, {"review_summary": "incomplete"}])
def test_annotation_rejects_missing_or_malformed_output(valid_annotation, output):
    payload, target, scores = valid_annotation
    payload["output"] = output

    assert not projection.annotation_complete(payload, target=target, scores=scores)


@pytest.mark.unit
def test_annotation_rejects_non_mapping_score(valid_annotation):
    payload, target, scores = valid_annotation
    invalid_scores = [None, *scores[1:]]

    assert not projection.annotation_complete(
        payload, target=target, scores=cast(Any, invalid_scores)
    )


@pytest.mark.unit
def test_disabled_does_not_start_child(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("disabled integration must not start a process")

    monkeypatch.setattr(subprocess, "run", forbidden)
    assert projection.export_projection({}, env={}) == "disabled"


@pytest.mark.unit
@pytest.mark.parametrize(
    "failure, expected",
    [
        (OSError("secret"), "export_failed"),
        (subprocess.TimeoutExpired("worker", 0.01), "timeout"),
    ],
)
def test_child_failures_return_sanitized_status(monkeypatch, failure, expected):
    def fail(*args, **kwargs):
        raise failure

    monkeypatch.setattr(subprocess, "run", fail)
    assert projection.export_projection({}, env=_environment()) == expected


def _environment():
    return {
        "HMDA_LANGFUSE_EXPORT": "true",
        "LANGFUSE_BASE_URL": "https://langfuse.invalid",
        "LANGFUSE_PUBLIC_KEY": "pk-test",
        "LANGFUSE_SECRET_KEY": "sk-test",
    }


@pytest.mark.unit
def test_child_receives_only_selected_environment_and_bounded_payload(
    monkeypatch, record
):
    payload = projection.project_invocation(
        record, expected_input=record.canonical_input
    )
    calls = []

    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args[0], 0)

    monkeypatch.setattr(subprocess, "run", capture)
    environment = {
        **_environment(),
        "PROVIDER_API_KEY": "must-not-leak",
        "OTEL_RESOURCE_ATTRIBUTES": "secret=value",
    }
    assert (
        projection.export_projection(payload, env=environment) == "submitted_unverified"
    )
    args, kwargs = calls[0]
    child_module = "hmda_reliability.review_ai.evaluation.langfuse"
    assert args[0] == [sys.executable, "-m", child_module]
    assert importlib.util.find_spec(child_module) is not None
    assert kwargs["timeout"] == 5
    assert "PROVIDER_API_KEY" not in kwargs["env"]
    assert "OTEL_RESOURCE_ATTRIBUTES" not in kwargs["env"]
    assert "sk-test" not in str(args)
    assert "sk-test" not in kwargs["input"]
    assert kwargs["stdout"] == subprocess.DEVNULL
    assert kwargs["stderr"] == subprocess.DEVNULL


@pytest.mark.unit
def test_media_like_output_stays_exact_and_child_disables_sdk_media(
    monkeypatch, record
):
    media_like_summary = "data:image/png;base64,AA=="
    output = record.parsed_output.model_copy(
        update={"review_summary": media_like_summary}
    )
    record = record.model_copy(update={"parsed_output": output})
    payload = projection.project_invocation(
        record, expected_input=record.canonical_input
    )
    calls = []

    def capture(*args, **kwargs):
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args[0], 0)

    monkeypatch.setattr(subprocess, "run", capture)
    environment = {
        **_environment(),
        "LANGFUSE_MEDIA_UPLOAD_ENABLED": "true",
    }
    assert projection.export_projection(payload, env=environment) == (
        "submitted_unverified"
    )

    _, kwargs = calls[0]
    child_payload = json.loads(kwargs["input"])
    assert kwargs["env"]["LANGFUSE_MEDIA_UPLOAD_ENABLED"] == "false"
    assert child_payload["output"] == output.model_dump(mode="json")
    assert child_payload["metadata"]["output_digest"] == review_output_digest(output)


@pytest.mark.integration
def test_pinned_langfuse_media_processor_keeps_data_uri_when_disabled(monkeypatch):
    media_manager_module = pytest.importorskip("langfuse._task_manager.media_manager")
    monkeypatch.setenv("LANGFUSE_MEDIA_UPLOAD_ENABLED", "false")
    queue = Queue()
    manager = media_manager_module.MediaManager(
        api_client=object(), httpx_client=object(), media_upload_queue=queue
    )
    output = {"review_summary": "data:image/png;base64,AA=="}

    processed = manager._find_and_process_media(
        data=output,
        trace_id="0" * 32,
        observation_id=None,
        field="output",
    )

    assert processed == output
    assert queue.empty()


@pytest.mark.unit
@pytest.mark.parametrize("timeout", ["nan", "inf", "0", "-1", "61", "bad"])
def test_invalid_timeout_never_starts_child(monkeypatch, timeout):
    def forbidden(*args, **kwargs):
        pytest.fail("invalid configuration must not start a process")

    monkeypatch.setattr(subprocess, "run", forbidden)
    assert (
        projection.export_projection(
            {}, env={**_environment(), "HMDA_LANGFUSE_TIMEOUT_SECONDS": timeout}
        )
        == "invalid_config"
    )


@pytest.mark.component
def test_real_stalled_child_is_terminated(monkeypatch):
    real_run = subprocess.run

    def stalled_child(args, **kwargs):
        return real_run([sys.executable, "-c", "import time; time.sleep(30)"], **kwargs)

    monkeypatch.setattr(subprocess, "run", stalled_child)
    started = time.monotonic()
    assert (
        projection.export_projection(
            {}, env={**_environment(), "HMDA_LANGFUSE_TIMEOUT_SECONDS": "0.1"}
        )
        == "timeout"
    )
    assert time.monotonic() - started < 3


@pytest.mark.component
@pytest.mark.parametrize(
    "export_status", ["timeout", "export_failed", "submitted_unverified", "raise"]
)
def test_harness_export_failure_preserves_result_and_record(
    tmp_path, monkeypatch, capsys, record, export_status
):
    from hmda_reliability.review_ai.contracts import AgenticReviewResult
    from scripts import run_agentic_review_live as harness

    path = tmp_path / "invocation.json"
    path.write_text(record.model_dump_json(), encoding="utf-8")
    before = path.read_bytes()
    result = AgenticReviewResult(
        status="accepted",
        output=record.parsed_output,
        validation=record.validation,
        invocation_id=record.invocation_id,
        invocation_path=path,
    )
    # 외부 투영 실패를 검증하려면 CLI 설정부터 fixture 호출 기록과 일치해야 한다.
    env = {
        **_environment(),
        "HMDA_AGENTIC_REVIEW_LIVE": "true",
        "HMDA_AGENTIC_REVIEW_MODE": "structured",
        "HMDA_AGENTIC_REVIEW_BASE_URL": "https://provider.invalid",
        "HMDA_AGENTIC_REVIEW_API_KEY": "provider-secret",
        "HMDA_AGENTIC_REVIEW_MODEL": "test-model",
        "HMDA_AGENTIC_REVIEW_TIMEOUT_SECONDS": "5",
        "HMDA_AGENTIC_REVIEW_MAX_RETRIES": "0",
        "HMDA_AGENTIC_REVIEW_PROJECT_REVISION": "revision-123",
    }

    def export(*args, **kwargs):
        if export_status == "raise":
            raise RuntimeError("private-sdk-error")
        return export_status

    monkeypatch.setattr(projection, "export_projection", export)
    assert harness.main(env=env, reviewer=lambda **kwargs: result) == 0
    assert path.read_bytes() == before
    expected = "projection_failed" if export_status == "raise" else export_status
    captured = capsys.readouterr()
    assert f"Langfuse projection: {expected}" in captured.err
    assert "private-sdk-error" not in captured.err


@pytest.mark.unit
@pytest.mark.parametrize("stage", ["init", "export", "flush", "shutdown"])
def test_sdk_failure_is_visible_to_child_exit(monkeypatch, stage):
    from opentelemetry.sdk import trace

    def fail_at(current):
        if current == stage:
            raise RuntimeError("private-sdk-error")

    class Client:
        def __init__(self, **kwargs):
            fail_at("init")

        def start_observation(self, **kwargs):
            fail_at("export")
            return SimpleNamespace(end=lambda: None)

        def flush(self):
            fail_at("flush")

        def shutdown(self):
            fail_at("shutdown")

    monkeypatch.setitem(sys.modules, "langfuse", SimpleNamespace(Langfuse=Client))
    monkeypatch.setattr(
        trace, "TracerProvider", lambda **kwargs: SimpleNamespace(shutdown=lambda: None)
    )
    for key, value in _environment().items():
        monkeypatch.setenv(key, value)
    with pytest.raises(RuntimeError, match="private-sdk-error"):
        projection._send_to_langfuse({"metadata": {"status": "unavailable"}})
