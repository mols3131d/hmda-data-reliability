from __future__ import annotations

import io
import threading
from typing import cast

import pytest

from hmda_reliability.review_ai.evaluation.progress import LiveProgressReporter
from hmda_reliability.review_ai.staged.evidence import StagedReviewStatus
from hmda_reliability.review_ai.staged.progress import StageProgress

pytestmark = pytest.mark.component


class WaitingConsole(io.StringIO):
    def __init__(self) -> None:
        super().__init__()
        self.waiting = threading.Event()

    def write(self, text: str) -> int:
        result = super().write(text)
        if "응답 대기" in text:
            self.waiting.set()
        return result


def test_heartbeat_is_visible_before_the_provider_call_finishes() -> None:
    console = WaitingConsole()
    with LiveProgressReporter(stream=console, heartbeat_seconds=0.01) as report:
        report(StageProgress(stage_id="evidence_review", phase="stage_started"))
        report(StageProgress(stage_id="evidence_review", phase="provider_started"))
        assert console.waiting.wait(timeout=2), "blocked call must show a heartbeat"
        assert "수집·저장 완료" not in console.getvalue()
        report(StageProgress(stage_id="evidence_review", phase="provider_finished"))
        report(
            StageProgress(
                stage_id="evidence_review",
                phase="stage_finished",
                status="completed",
                attempt_count=2,
            )
        )
    log = console.getvalue()
    assert "단계 1/3 근거 검토 시작" in log
    assert "응답 대기" in log and "전체" in log and "초" in log
    assert "수집·저장 완료" in log and "요청 2회" in log
    assert not any(t.name == "review-ai-progress" for t in threading.enumerate())


@pytest.mark.parametrize(
    "status",
    ["input_rejected", "unavailable", "validation_failed", "provenance_failed"],
)
def test_stage_failure_is_never_reported_as_completion(
    status: StagedReviewStatus,
) -> None:
    console = io.StringIO()
    with LiveProgressReporter(stream=console) as report:
        report(StageProgress(stage_id="draft_critique", phase="stage_started"))
        report(
            StageProgress(
                stage_id="draft_critique", phase="stage_finished", status=status
            )
        )
    assert "단계 2/3 초안 검토 실패" in console.getvalue()
    assert status in console.getvalue()
    assert "수집·저장 완료" not in console.getvalue()


def test_unrecognized_status_is_never_copied_to_the_console() -> None:
    console = io.StringIO()
    with LiveProgressReporter(stream=console) as report:
        report(
            StageProgress(
                stage_id="draft_critique",
                phase="stage_finished",
                status=cast(StagedReviewStatus, "PRIVATE_UNRECOGNIZED_STATUS"),
            )
        )

    assert "PRIVATE_UNRECOGNIZED_STATUS" not in console.getvalue()
    assert "실패 (unknown)" in console.getvalue()


def test_exception_stops_the_waiting_reporter_without_printing_exception_text() -> None:
    console = WaitingConsole()
    with (
        pytest.raises(RuntimeError, match="PRIVATE_EXCEPTION"),
        LiveProgressReporter(stream=console, heartbeat_seconds=0.01) as report,
    ):
        report(StageProgress(stage_id="synthesis", phase="stage_started"))
        report(StageProgress(stage_id="synthesis", phase="provider_started"))
        assert console.waiting.wait(timeout=2)
        raise RuntimeError("PRIVATE_EXCEPTION")
    assert "PRIVATE_EXCEPTION" not in console.getvalue()
    assert not any(t.name == "review-ai-progress" for t in threading.enumerate())


def test_broken_progress_stream_does_not_interrupt_collection() -> None:
    class BrokenConsole(io.StringIO):
        def write(self, text: str) -> int:
            raise OSError("PRIVATE_STREAM_FAILURE")

    with LiveProgressReporter(stream=BrokenConsole()) as report:
        report(StageProgress(stage_id="synthesis", phase="stage_started"))
        report(StageProgress(stage_id="synthesis", phase="provider_started"))
        report(StageProgress(stage_id="synthesis", phase="provider_finished"))
    assert not any(t.name == "review-ai-progress" for t in threading.enumerate())


@pytest.mark.parametrize("failure_site", ["stream", "clock"])
def test_heartbeat_exception_is_stopped_without_thread_traceback(
    monkeypatch: pytest.MonkeyPatch,
    failure_site: str,
) -> None:
    attempts = threading.Event()
    unhandled: list[BaseException | None] = []

    class FailingHeartbeatConsole(io.StringIO):
        def write(self, text: str) -> int:
            if failure_site == "stream" and "응답 대기" in text:
                attempts.set()
                raise RuntimeError("PRIVATE_HEARTBEAT_CONSOLE_FAILURE")
            return super().write(text)

    def observed_clock() -> float:
        if failure_site == "clock" and threading.current_thread().name == (
            "review-ai-progress"
        ):
            attempts.set()
            raise RuntimeError("PRIVATE_HEARTBEAT_CLOCK_FAILURE")
        return 10.0

    def record_unhandled(error: threading.ExceptHookArgs) -> None:
        unhandled.append(error.exc_value)

    monkeypatch.setattr(threading, "excepthook", record_unhandled)
    console = FailingHeartbeatConsole()
    with LiveProgressReporter(
        stream=console, heartbeat_seconds=0.01, clock=observed_clock
    ) as report:
        report(StageProgress(stage_id="evidence_review", phase="stage_started"))
        report(StageProgress(stage_id="evidence_review", phase="provider_started"))
        assert attempts.wait(timeout=2), "heartbeat must exercise the failing observer"
        report(StageProgress(stage_id="evidence_review", phase="provider_finished"))

    assert unhandled == []
    assert "PRIVATE_HEARTBEAT" not in console.getvalue()
    assert not any(t.name == "review-ai-progress" for t in threading.enumerate())


def test_progress_does_not_suppress_keyboard_interrupt() -> None:
    class InterruptedConsole(io.StringIO):
        def write(self, text: str) -> int:
            raise KeyboardInterrupt

    with (
        pytest.raises(KeyboardInterrupt),
        LiveProgressReporter(stream=InterruptedConsole()) as report,
    ):
        report(StageProgress(stage_id="evidence_review", phase="stage_started"))

    assert not any(t.name == "review-ai-progress" for t in threading.enumerate())


def test_unavailable_thread_only_disables_progress(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    console = io.StringIO()
    reporter = LiveProgressReporter(stream=console)

    def fail_to_start() -> None:
        raise RuntimeError("PRIVATE_CANNOT_START_THREAD")

    monkeypatch.setattr(reporter._thread, "start", fail_to_start)
    with reporter as report:
        report(StageProgress(stage_id="evidence_review", phase="stage_started"))
        report(StageProgress(stage_id="evidence_review", phase="provider_started"))
        report(StageProgress(stage_id="evidence_review", phase="provider_finished"))
        report(
            StageProgress(
                stage_id="evidence_review", phase="stage_finished", status="completed"
            )
        )

    assert console.getvalue() == ""
    assert not any(t.name == "review-ai-progress" for t in threading.enumerate())


def test_heartbeat_only_runs_between_provider_boundary_events() -> None:
    console = WaitingConsole()
    with LiveProgressReporter(stream=console, heartbeat_seconds=0.01) as report:
        report(StageProgress(stage_id="evidence_review", phase="stage_started"))
        assert not console.waiting.wait(timeout=0.05)
        report(StageProgress(stage_id="evidence_review", phase="provider_started"))
        assert console.waiting.wait(timeout=2)
        report(StageProgress(stage_id="evidence_review", phase="provider_finished"))
        console.waiting.clear()
        assert not console.waiting.wait(timeout=0.05)


def test_default_heartbeat_waits_five_seconds(monkeypatch: pytest.MonkeyPatch) -> None:
    intervals: list[float] = []
    reporter = LiveProgressReporter(stream=io.StringIO())

    def observed_wait(timeout: float) -> bool:
        intervals.append(timeout)
        return True

    monkeypatch.setattr(reporter._stop, "wait", observed_wait)
    with reporter:
        pass
    assert intervals == [5.0]


def test_reported_elapsed_time_uses_the_local_monotonic_clock() -> None:
    now = 10.0
    console = io.StringIO()
    with LiveProgressReporter(stream=console, clock=lambda: now) as report:
        now = 12.0
        report(StageProgress(stage_id="synthesis", phase="stage_started"))
        now = 15.5
        report(
            StageProgress(
                stage_id="synthesis", phase="stage_finished", status="completed"
            )
        )
    assert "단계 3.5초 · 전체 5.5초" in console.getvalue()
