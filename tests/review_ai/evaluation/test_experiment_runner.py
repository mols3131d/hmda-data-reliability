"""Native Dataset 실행에 task만 연결하고 운영 계층을 다시 구현하지 않는다."""

from datetime import datetime
from types import SimpleNamespace

import pytest

from hmda_reliability.review_ai.contracts import AgenticReviewInput
from hmda_reliability.review_ai.evaluation import experiment
from hmda_reliability.review_ai.staged.evidence import StagedReviewResult
from tests.review_ai.conftest import NativeClient

pytestmark = pytest.mark.component


@pytest.fixture
def configured_runner(monkeypatch, null_spike_review_material, native_langfuse):
    material = null_spike_review_material
    payload = AgenticReviewInput(
        incident=material.detection.incident,
        evidence=[material.detection.evidence],
        draft=material.draft,
        project_revision="fixture-only",
    ).model_dump(mode="json", exclude={"project_revision"})
    requests = []
    outputs = []
    native_calls = []

    def run_experiment(**kwargs):
        native_calls.append(kwargs)
        output = kwargs["task"](
            item=SimpleNamespace(
                input=payload,
                expected_output={"oracle": "reviewer-only-secret"},
                metadata={"private_case_note": "excluded"},
            )
        )
        outputs.append(output)
        return SimpleNamespace(
            item_results=[SimpleNamespace(output=output, task_error=None)],
            format=lambda: "Native Dataset result: test-run",
        )

    def get_dataset(name, **kwargs):
        requests.append((name, kwargs))
        return SimpleNamespace(run_experiment=run_experiment)

    native_langfuse.get_dataset = get_dataset
    native_langfuse.flush = lambda: None
    monkeypatch.setenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "PRIVATE_PROVIDER_KEY")
    monkeypatch.setattr(experiment, "get_client", lambda: native_langfuse)
    monkeypatch.setattr(
        experiment.subprocess,
        "check_output",
        lambda args, **kw: "" if args[1] == "diff" else "revision-test\n",
    )
    return requests, native_calls, outputs


def test_native_dataset_owns_the_loop_without_bootstrap_or_annotation_api_calls(
    configured_runner, monkeypatch, capsys, tmp_path
):
    requests, calls, outputs = configured_runner
    seen = []

    def review(**kwargs):
        seen.append(kwargs)
        return StagedReviewResult(
            status="completed", workflow_id="sr-native", workflow_path=tmp_path
        )

    monkeypatch.setattr(experiment, "review_null_spike", review)
    assert (
        experiment.main(
            argv=[
                "--dataset",
                "managed-dataset",
                "--name",
                "test-run",
                "--dataset-version",
                "2026-10-30T00:00:00Z",
                "--prompt-label",
                "candidate",
            ]
        )
        == 0
    )

    assert requests == [
        (
            "managed-dataset",
            {"version": datetime.fromisoformat("2026-10-30T00:00:00Z")},
        )
    ]
    assert calls[0]["name"] == "test-run" and calls[0]["max_concurrency"] == 1
    assert len(seen) == 1
    assert seen[0]["project_revision"] == "revision-test"
    assert seen[0]["settings"].model == "test-model"
    assert seen[0]["settings"].max_output_tokens == 2048
    assert "expected_output" not in seen[0] and "metadata" not in seen[0]
    assert outputs == [
        {
            "status": "completed",
            "failure_code": None,
            "workflow_id": "sr-native",
            "output": None,
        }
    ]
    console = capsys.readouterr()
    assert "Native Dataset result: test-run" in console.out
    assert "PRIVATE_PROVIDER_KEY" not in console.out + console.err
    assert str(tmp_path) not in str(outputs)


def test_native_dataset_keeps_typed_core_failure_and_returns_nonzero(
    configured_runner, monkeypatch
):
    _, _, outputs = configured_runner
    monkeypatch.setattr(
        experiment,
        "review_null_spike",
        lambda **kw: StagedReviewResult(
            status="validation_failed", failure_code="stage_response_incomplete"
        ),
    )

    assert experiment.main(argv=["--name", "failed-run"]) == 1
    assert outputs[0]["status"] == "validation_failed"
    assert outputs[0]["failure_code"] == "stage_response_incomplete"


def test_missing_native_prompt_stops_before_dataset_execution(
    monkeypatch, native_langfuse: NativeClient
):
    def unavailable(*_args, **_kwargs):
        raise RuntimeError("PRIVATE_REMOTE_FAILURE")

    monkeypatch.setenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "PRIVATE_PROVIDER_KEY")
    monkeypatch.setattr(native_langfuse, "get_prompt", unavailable)
    monkeypatch.setattr(experiment, "get_client", lambda: native_langfuse)
    assert experiment.main(argv=[]) != 0
