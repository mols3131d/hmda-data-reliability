"""호출 시점의 native generation과 로컬 원문 우선 보존을 연결한다."""

import json

import pytest

from hmda_reliability.review_ai.store import (
    InvocationEvidenceWriteError,
    InvocationResponseStore,
)
from hmda_reliability.runtime_ai.contracts import ProviderUsage
from hmda_reliability.runtime_ai.provider import (
    ProviderResponseTooLargeError,
    ProviderUnavailableError,
)
from tests.review_ai.conftest import NativeClient, NativeObservation
from tests.review_ai.test_staged_service import (
    TEXTS,
    TextProvider,
    response,
    run_review,
)

pytestmark = pytest.mark.component


def test_generation_wraps_call_and_exports_output_after_raw_is_saved(
    native_langfuse: NativeClient, null_spike_review_material, tmp_path, monkeypatch
):
    original_update = NativeObservation.update
    observed_outputs = []

    def update_after_save(self, **values):
        if values.get("output") is not None:
            raw = list((tmp_path / "agentic-review" / "responses").glob("*.txt"))
            assert values["output"] in [path.read_text() for path in raw]
            observed_outputs.append(values["output"])
        original_update(self, **values)

    monkeypatch.setattr(NativeObservation, "update", update_after_save)

    class ObservedProvider(TextProvider):
        def invoke(self, messages, **kwargs):
            assert sum(item.active for item in native_langfuse.observations) == 1
            return super().invoke(messages, **kwargs)

    usage = ProviderUsage(prompt_tokens=13, completion_tokens=5, total_tokens=18)
    provider = ObservedProvider(
        [response(text).model_copy(update={"usage": usage}) for text in TEXTS]
    )
    result = run_review(null_spike_review_material, tmp_path, provider)

    assert result.status == "completed" and len(native_langfuse.observations) == 3
    assert observed_outputs == list(TEXTS)
    for index, span in enumerate(native_langfuse.observations):
        state = dict(span.values)
        for update in span.updates:
            state.update(update)
        assert state["as_type"] == "generation"
        assert state["input"] == [
            message.model_dump(mode="json") for message in provider.calls[index]
        ]
        assert state["output"] == TEXTS[index]
        assert state["model"] == "test-model"
        assert state["usage_details"] == {"input": 13, "output": 5, "total": 18}
        assert state["prompt"] is native_langfuse.prompts[result.stages[index].stage_id]
        assert not span.active
    assert [stage.prompt_version for stage in result.stages] == [7, 7, 7]
    assert [stage.prompt_name for stage in result.stages] == [
        f"hmda-review-ai/{stage.stage_id}" for stage in result.stages
    ]
    manifest = json.loads(result.workflow_path.read_text())
    assert [stage["prompt_version"] for stage in manifest["stages"]] == [7, 7, 7]
    assert len(native_langfuse.prompt_requests) == 3


def test_validation_failure_keeps_raw_and_marks_generation_error(
    native_langfuse: NativeClient, null_spike_review_material, tmp_path
):
    provider = TextProvider(
        [response(TEXTS[0]), response("잘린 한국어 원문", "length")]
    )

    result = run_review(null_spike_review_material, tmp_path, provider)

    assert result.status == "validation_failed" and len(provider.calls) == 2
    assert result.stages[1].response_path.read_text() == "잘린 한국어 원문"
    updates = native_langfuse.observations[-1].updates
    assert any(update.get("output") == "잘린 한국어 원문" for update in updates)
    assert any(update.get("level") == "ERROR" for update in updates)


@pytest.mark.parametrize("failure_at", ["start", "enter", "update", "exit"])
def test_observation_failure_preserves_core_output_and_raw(
    native_langfuse: NativeClient,
    null_spike_review_material,
    tmp_path,
    monkeypatch,
    failure_at,
    capsys,
):
    def unavailable(*_args, **_kwargs):
        raise RuntimeError("PRIVATE_OBSERVATION_FAILURE")

    if failure_at == "start":
        monkeypatch.setattr(
            native_langfuse, "start_as_current_observation", unavailable
        )
    else:
        monkeypatch.setattr(
            NativeObservation,
            {"enter": "__enter__", "exit": "__exit__", "update": "update"}[failure_at],
            unavailable,
        )
    provider = TextProvider([response(text) for text in TEXTS])

    result = run_review(null_spike_review_material, tmp_path, provider)

    assert result.status == "completed" and len(provider.calls) == 3
    assert [answer.text for answer in result.output.stages] == list(TEXTS)
    assert [record.response_path.read_text() for record in result.stages] == list(TEXTS)
    captured = capsys.readouterr()
    assert "PRIVATE_OBSERVATION_FAILURE" not in captured.out + captured.err


def test_prompt_failure_has_no_local_fallback_or_model_call(
    native_langfuse: NativeClient,
    null_spike_review_material,
    tmp_path,
    monkeypatch,
):
    def unavailable(*_args, **_kwargs):
        raise RuntimeError("PRIVATE_PROMPT_FAILURE")

    monkeypatch.setattr(native_langfuse, "get_prompt", unavailable)
    provider = TextProvider([])

    result = run_review(null_spike_review_material, tmp_path, provider)

    assert result.status == "unavailable"
    assert result.failure_code == "prompt_unavailable"
    assert provider.calls == [] and result.stages == ()
    assert result.output is None
    assert "PRIVATE_PROMPT_FAILURE" not in result.model_dump_json()


@pytest.mark.parametrize(
    "stage_id,completed_count", [("draft_critique", 1), ("synthesis", 2)]
)
def test_later_invalid_native_prompt_stops_typed_and_preserves_prior_raw(
    native_langfuse: NativeClient,
    null_spike_review_material,
    tmp_path,
    stage_id,
    completed_count,
):
    prompt = native_langfuse.prompts[stage_id]
    prompt.prompt = [item for item in prompt.prompt if item["type"] != "placeholder"]
    provider = TextProvider([response(text) for text in TEXTS[:completed_count]])

    result = run_review(null_spike_review_material, tmp_path, provider)

    assert result.status == "input_rejected" and result.failure_code == "prompt_invalid"
    assert len(provider.calls) == completed_count
    assert result.stages[-1].stage_id == stage_id
    assert result.stages[-1].attempt_count == 0
    assert [record.response_path.read_text() for record in result.stages[:-1]] == list(
        TEXTS[:completed_count]
    )
    assert result.workflow_path.is_file()


@pytest.mark.parametrize(
    "failure_at,expected_status,expected_code",
    [
        ("timeout", "unavailable", "provider_timeout"),
        ("too_large", "validation_failed", "response_too_large"),
        ("raw_save", "provenance_failed", "stage_response_write_failed"),
    ],
)
def test_failed_call_keeps_native_input_and_known_usage_without_exporting_output(
    native_langfuse: NativeClient,
    null_spike_review_material,
    tmp_path,
    monkeypatch,
    failure_at,
    expected_status,
    expected_code,
):
    usage = ProviderUsage(prompt_tokens=13, completion_tokens=5, total_tokens=18)
    expected_usage = {"input": 13, "output": 5, "total": 18}
    input_at_call = []
    usage_at_storage = []

    def generation_state():
        observation = native_langfuse.observations[-1]
        state = dict(observation.values)
        for update in observation.updates:
            state.update(update)
        return state

    class ObservedProvider(TextProvider):
        def invoke(self, messages, **kwargs):
            assert native_langfuse.observations[-1].active
            input_at_call.append(generation_state().get("input"))
            return super().invoke(messages, **kwargs)

    failure_or_response = (
        ProviderUnavailableError(
            failure_code="provider_timeout", attempt_count=1, latency_ms=1
        )
        if failure_at == "timeout"
        else ProviderResponseTooLargeError(
            attempt_count=1,
            latency_ms=1,
            actual_bytes=32769,
            max_bytes=32768,
            usage=usage,
            trace_id=None,
        )
        if failure_at == "too_large"
        else response(TEXTS[0]).model_copy(update={"usage": usage})
    )
    if failure_at == "raw_save":

        def unavailable_storage(*_args, **_kwargs):
            usage_at_storage.append(generation_state().get("usage_details"))
            raise InvocationEvidenceWriteError("PRIVATE_STORAGE_FAILURE")

        monkeypatch.setattr(InvocationResponseStore, "write", unavailable_storage)
    provider = ObservedProvider([failure_or_response])

    result = run_review(null_spike_review_material, tmp_path, provider)

    assert result.status == expected_status and result.failure_code == expected_code
    assert len(provider.calls) == len(native_langfuse.observations) == 1
    expected_input = [message.model_dump(mode="json") for message in provider.calls[0]]
    state = generation_state()
    assert input_at_call == [expected_input]
    assert state["input"] == expected_input
    assert state.get("output") is None and state["level"] == "ERROR"
    assert result.output is None and result.stages[0].response_path is None
    assert result.workflow_path.is_file()
    if failure_at == "timeout":
        assert state.get("usage_details") is None
    else:
        assert state["usage_details"] == expected_usage
        assert result.stages[0].usage == usage
    if failure_at == "raw_save":
        assert usage_at_storage == [expected_usage]
