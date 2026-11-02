"""진행 관측이 단계 순서, 원문 보존과 실패 결과를 바꾸지 않는 경계."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import FrozenInstanceError, fields
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from hmda_reliability.review_ai.staged import service as staged_service
from hmda_reliability.review_ai.staged.contracts import STAGE_IDS
from hmda_reliability.review_ai.staged.store import StagedReviewStore
from hmda_reliability.review_ai.store import (
    InvocationEvidenceWriteError,
    InvocationResponseStore,
)
from hmda_reliability.runtime_ai import RuntimeAISettings
from hmda_reliability.runtime_ai.provider import (
    ProviderResponseTooLargeError,
    ProviderUnavailableError,
)

from .conftest import NullSpikeReviewMaterial
from .test_staged_service import TEXTS, TextProvider, response

if TYPE_CHECKING:
    from hmda_reliability.review_ai.staged.progress import StageProgress

pytestmark = pytest.mark.component


def _run(
    material: NullSpikeReviewMaterial,
    artifact_root: Path,
    provider: TextProvider,
    on_progress: Callable[[StageProgress], None],
):
    return staged_service.review_null_spike_staged(
        incident=material.detection.incident,
        evidence=[material.detection.evidence],
        draft=material.draft,
        project_revision="revision-under-test",
        settings=RuntimeAISettings(
            base_url="http://localhost:11434/v1",
            api_key="PRIVATE_PROGRESS_SECRET",
            model="PRIVATE_PROGRESS_MODEL",
            max_retries=0,
        ),
        provider=provider,
        artifact_root=artifact_root,
        workflow_id_factory=lambda: "sr-progress",
        on_progress=on_progress,
    )


def test_progress_event_is_immutable_and_contains_only_execution_metadata() -> None:
    from hmda_reliability.review_ai.staged.progress import StageProgress

    event = StageProgress(stage_id="evidence_review", phase="stage_started")

    assert [field.name for field in fields(event)] == [
        "stage_id",
        "phase",
        "status",
        "attempt_count",
    ]
    assert event.status is None and event.attempt_count == 0
    protected_attribute = fields(event)[1].name
    with pytest.raises(FrozenInstanceError):
        setattr(event, protected_attribute, "stage_finished")


def test_progress_order_matches_response_arrival_and_persisted_checkpoint(
    null_spike_review_material: NullSpikeReviewMaterial, tmp_path: Path
) -> None:
    observations: list[tuple[StageProgress, bool, bool]] = []

    def observe(event: StageProgress) -> None:
        observations.append(
            (
                event,
                InvocationResponseStore(tmp_path)
                .path_for(f"sr-progress-{event.stage_id}")
                .exists(),
                StagedReviewStore(tmp_path)
                .stage_path("sr-progress", event.stage_id)
                .exists(),
            )
        )

    result = _run(
        null_spike_review_material,
        tmp_path,
        TextProvider([response(text) for text in TEXTS]),
        observe,
    )

    assert result.status == "completed"
    assert [
        (event.stage_id, event.phase, event.status, event.attempt_count)
        for event, _, _ in observations
    ] == [
        (stage_id, phase, status, attempts)
        for stage_id in STAGE_IDS
        for phase, status, attempts in [
            ("stage_started", None, 0),
            ("provider_started", None, 0),
            ("provider_finished", None, 1),
            ("stage_finished", "completed", 1),
        ]
    ]
    assert [
        (raw_exists, checkpoint_exists)
        for event, raw_exists, checkpoint_exists in observations
        if event.phase == "provider_finished"
    ] == [(False, False)] * 3
    assert [
        (raw_exists, checkpoint_exists)
        for event, raw_exists, checkpoint_exists in observations
        if event.phase == "stage_finished"
    ] == [(True, True)] * 3


@pytest.mark.parametrize(
    ("failure", "expected_status", "attempt_count"),
    [
        (
            ProviderUnavailableError(
                failure_code="provider_timeout", attempt_count=2, latency_ms=3
            ),
            "unavailable",
            2,
        ),
        (
            ProviderResponseTooLargeError(
                attempt_count=1,
                latency_ms=3,
                actual_bytes=32769,
                max_bytes=32768,
                usage=None,
                trace_id=None,
            ),
            "validation_failed",
            1,
        ),
    ],
)
def test_provider_failure_ends_wait_and_reports_final_stage_status(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
    failure: Exception,
    expected_status: str,
    attempt_count: int,
) -> None:
    events: list[StageProgress] = []
    provider = TextProvider([failure])

    result = _run(null_spike_review_material, tmp_path, provider, events.append)

    assert result.status == expected_status and len(provider.calls) == 1
    assert [(event.phase, event.status, event.attempt_count) for event in events] == [
        ("stage_started", None, 0),
        ("provider_started", None, 0),
        ("provider_finished", None, attempt_count),
        ("stage_finished", expected_status, attempt_count),
    ]


@pytest.mark.parametrize("operation", ["write_raw", "write_checkpoint"])
def test_stage_finished_reports_storage_failure_after_response_arrival(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
) -> None:
    def fail(*args, **kwargs):
        raise InvocationEvidenceWriteError("PRIVATE_STORAGE_EXCEPTION")

    target, name = (
        (InvocationResponseStore, "write")
        if operation == "write_raw"
        else (StagedReviewStore, "write_stage")
    )
    monkeypatch.setattr(target, name, fail)
    events: list[StageProgress] = []
    provider = TextProvider([response(TEXTS[0])])

    result = _run(null_spike_review_material, tmp_path, provider, events.append)

    assert result.status == "provenance_failed" and len(provider.calls) == 1
    assert [event.phase for event in events] == [
        "stage_started",
        "provider_started",
        "provider_finished",
        "stage_finished",
    ]
    assert events[-1].status == result.stages[0].status == "provenance_failed"
    assert events[-1].attempt_count == 1
    if operation == "write_checkpoint":
        assert result.stages[0].response_path is not None
        assert result.stages[0].response_path.read_text(encoding="utf-8") == TEXTS[0]


def test_observer_exceptions_do_not_change_result_or_raw_preservation(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    events: list[StageProgress] = []

    def fail(event: StageProgress) -> None:
        events.append(event)
        raise RuntimeError("PRIVATE_OBSERVER_EXCEPTION")

    result = _run(
        null_spike_review_material,
        tmp_path,
        TextProvider([response(text) for text in TEXTS]),
        fail,
    )

    assert result.status == "completed" and len(events) == 12
    assert result.output is not None
    assert [answer.text for answer in result.output.stages] == list(TEXTS)
    for stage, text in zip(result.stages, TEXTS, strict=True):
        assert stage.response_path is not None
        assert stage.response_path.read_text(encoding="utf-8") == text
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""


def test_unexpected_provider_error_ends_wait_before_propagating(
    null_spike_review_material: NullSpikeReviewMaterial, tmp_path: Path
) -> None:
    events: list[StageProgress] = []
    provider = TextProvider(
        [response(TEXTS[0]), RuntimeError("unexpected-provider-error")]
    )

    with pytest.raises(RuntimeError, match="unexpected-provider-error"):
        _run(null_spike_review_material, tmp_path, provider, events.append)

    assert len(provider.calls) == 2
    assert [(event.stage_id, event.phase) for event in events][-3:] == [
        ("draft_critique", "stage_started"),
        ("draft_critique", "provider_started"),
        ("draft_critique", "provider_finished"),
    ]
    assert events[-1].attempt_count == 0
    assert (
        InvocationResponseStore(tmp_path)
        .path_for("sr-progress-evidence_review")
        .read_text(encoding="utf-8")
        == TEXTS[0]
    )
