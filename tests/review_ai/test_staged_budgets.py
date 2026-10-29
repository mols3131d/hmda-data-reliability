"""가짜 시계로 실행 예산과 늦은 원문의 보존을 검증한다."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from hmda_reliability.review_ai.staged import service
from hmda_reliability.review_ai.staged.evidence import StagedReviewManifest
from hmda_reliability.review_ai.staged.settings import StagedExecutionSettings
from hmda_reliability.runtime_ai.contracts import ChatMessage, ProviderResponse
from hmda_reliability.runtime_ai.settings import RuntimeAISettings

from .conftest import NullSpikeReviewMaterial


class Clock:
    now = 0.0

    def __call__(self) -> float:
        return self.now


class TimedProvider:
    def __init__(self, clock: Clock, durations: list[float]) -> None:
        self.clock = clock
        self.durations = durations
        self.budgets: list[float | None] = []

    def invoke(
        self,
        messages: tuple[ChatMessage, ...],
        *,
        output_format: str = "json_object",
        budget_seconds: float | None = None,
    ) -> ProviderResponse:
        assert output_format == "text"
        self.budgets.append(budget_seconds)
        duration = self.durations[len(self.budgets) - 1]
        self.clock.now += duration
        return ProviderResponse(
            content=f"  단계 {len(self.budgets)} 원문\n",
            attempt_count=1,
            latency_ms=duration * 1000,
        )


def run(
    material: NullSpikeReviewMaterial,
    tmp_path: Path,
    clock: Clock,
    provider: TimedProvider,
    *,
    stage: float = 10,
    workflow: float = 25,
):
    return service.review_null_spike_staged(
        incident=material.detection.incident,
        evidence=[material.detection.evidence],
        draft=material.draft,
        project_revision="timing-test",
        settings=RuntimeAISettings(
            base_url="http://localhost:11434/v1",
            api_key="test-secret",
            model="fake",
            max_retries=0,
        ),
        execution_settings=StagedExecutionSettings(
            stage_budget_seconds=stage, workflow_budget_seconds=workflow
        ),
        provider=provider,
        clock=clock,
        artifact_root=tmp_path,
        workflow_id_factory=lambda: "sr-clock",
    )


@pytest.mark.component
@pytest.mark.parametrize(
    ("stage", "workflow", "failure"),
    [(10, 25, "stage_budget_exhausted"), (20, 10, "workflow_budget_exhausted")],
)
def test_late_answer_is_saved_before_budget_failure(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
    stage: float,
    workflow: float,
    failure: str,
) -> None:
    clock = Clock()
    provider = TimedProvider(clock, [11])
    result = run(
        null_spike_review_material,
        tmp_path,
        clock,
        provider,
        stage=stage,
        workflow=workflow,
    )
    assert result.status == "unavailable" and result.failure_code == failure
    assert result.output is None and result.output_path is None
    assert provider.budgets == [10]
    record = result.stages[0]
    assert record.attempt_count == 1 and record.elapsed_ms == 11_000
    assert record.response_path is not None
    assert record.response_path.read_bytes() == "  단계 1 원문\n".encode()
    manifest = StagedReviewManifest.model_validate_json(
        result.workflow_path.read_bytes()
    )
    assert manifest.execution_settings is not None
    assert manifest.execution_settings.stage_budget_seconds == stage
    assert manifest.elapsed_ms == 11_000


@pytest.mark.component
def test_remaining_workflow_budget_caps_later_stage(
    null_spike_review_material: NullSpikeReviewMaterial, tmp_path: Path
) -> None:
    clock = Clock()
    provider = TimedProvider(clock, [8, 8, 8])
    result = run(null_spike_review_material, tmp_path, clock, provider)
    assert result.status == "completed"
    assert provider.budgets == [10, 10, 9]
    assert [record.budget_seconds for record in result.stages] == [10, 10, 9]
    assert [record.elapsed_ms for record in result.stages] == [8000, 8000, 8000]


@pytest.mark.component
def test_checkpoint_delay_can_exhaust_workflow_before_next_call(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = Clock()
    provider = TimedProvider(clock, [1])
    original = service.StagedReviewStore.write_stage

    def delayed_write(self, workflow_id, record):
        result = original(self, workflow_id, record)
        clock.now += 30
        return result

    monkeypatch.setattr(service.StagedReviewStore, "write_stage", delayed_write)
    result = run(null_spike_review_material, tmp_path, clock, provider)
    assert result.status == "unavailable"
    assert result.failure_code == "workflow_budget_exhausted"
    assert provider.budgets == [10]
    first, second = result.stages
    assert first.status == "completed" and first.response_path.is_file()
    assert second.stage_id == "draft_critique" and second.attempt_count == 0
    assert second.response_path is None and second.record_path.is_file()
    assert json.loads(result.workflow_path.read_bytes())["physical_attempts"] == 1


@pytest.mark.component
def test_output_persistence_delay_does_not_admit_completed_result(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = Clock()
    provider = TimedProvider(clock, [1, 1, 1])
    original = service.StagedReviewStore.write_output

    def delayed_write(self, *args, **kwargs):
        result = original(self, *args, **kwargs)
        clock.now += 30
        return result

    monkeypatch.setattr(service.StagedReviewStore, "write_output", delayed_write)
    result = run(null_spike_review_material, tmp_path, clock, provider)
    assert result.status == "unavailable"
    assert result.failure_code == "workflow_budget_exhausted"
    assert result.output is None
    assert result.output_path.is_file()
    assert all(record.response_path.is_file() for record in result.stages)


@pytest.mark.unit
@pytest.mark.parametrize("value", [0, -1, float("inf"), float("nan")])
def test_invalid_execution_budgets_are_rejected(value: float) -> None:
    with pytest.raises(ValidationError):
        StagedExecutionSettings(stage_budget_seconds=value)
    with pytest.raises(ValidationError):
        StagedExecutionSettings(workflow_budget_seconds=value)
