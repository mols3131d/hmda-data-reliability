"""실제 모델 검증의 콘솔 표시. 검토 API는 timer와 출력에 관여하지 않는다."""

from __future__ import annotations

import math
import sys
import threading
import time
from collections.abc import Callable
from types import TracebackType
from typing import TextIO

from hmda_reliability.review_ai.staged.contracts import STAGE_IDS
from hmda_reliability.review_ai.staged.progress import StageProgress

_STAGE_LABELS = {
    "evidence_review": "근거 검토",
    "draft_critique": "초안 검토",
    "synthesis": "종합 검토",
}
_FAILURE_STATUSES = frozenset(
    {"input_rejected", "unavailable", "validation_failed", "provenance_failed"}
)


class LiveProgressReporter:
    """Provider 호출 대기만 표시하고 모든 종료 경로에서 보조 thread를 정리한다.

    대기 시간은 로컬 관측값이다. 내부 retry/backoff를 포함할 수 있으며
    provider가 처리한 비율이나 생성 토큰 수를 나타내지 않는다.
    """

    def __init__(
        self,
        *,
        stream: TextIO | None = None,
        heartbeat_seconds: float = 5.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if not math.isfinite(heartbeat_seconds) or heartbeat_seconds <= 0:
            raise ValueError("heartbeat interval must be finite and positive")
        self._stream = sys.stderr if stream is None else stream
        self._interval = heartbeat_seconds
        self._clock = clock
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._thread = threading.Thread(
            target=self._heartbeat, name="review-ai-progress", daemon=True
        )
        self._started = 0.0
        self._stage_started = 0.0
        self._waiting: StageProgress | None = None

    def __enter__(self) -> LiveProgressReporter:
        self._started = self._clock()
        try:
            self._thread.start()
        except Exception:
            self._stop.set()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._stop.set()
        if self._thread.ident is not None:
            self._thread.join()

    def __call__(self, event: StageProgress) -> None:
        with self._lock:
            if self._stop.is_set():
                return
            if event.phase == "stage_started":
                self._stage_started = self._clock()
                self._emit(f"{self._label(event)} 시작")
            elif event.phase == "provider_started":
                self._waiting = event
            elif event.phase == "provider_finished":
                self._waiting = None
            elif event.phase == "stage_finished":
                self._waiting = None
                status = (
                    event.status if event.status in _FAILURE_STATUSES else "unknown"
                )
                outcome = (
                    "수집·저장 완료"
                    if event.status == "completed"
                    else f"실패 ({status})"
                )
                self._emit(
                    f"{self._label(event)} {outcome} · {self._elapsed()}"
                    f" · 요청 {event.attempt_count}회"
                )

    def _heartbeat(self) -> None:
        try:
            while not self._stop.wait(self._interval):
                with self._lock:
                    if self._waiting is not None and not self._stop.is_set():
                        self._emit(
                            f"{self._label(self._waiting)} 응답 대기"
                            f" · {self._elapsed()}"
                        )
        except Exception:
            # 보조 thread의 관측 오류도 기본 traceback으로 유출하지 않는다.
            self._stop.set()

    def _elapsed(self) -> str:
        now = self._clock()
        return (
            f"단계 {max(0.0, now - self._stage_started):.1f}초"
            f" · 전체 {max(0.0, now - self._started):.1f}초"
        )

    @staticmethod
    def _label(event: StageProgress) -> str:
        return (
            f"단계 {STAGE_IDS.index(event.stage_id) + 1}/{len(STAGE_IDS)}"
            f" {_STAGE_LABELS[event.stage_id]}"
        )

    def _emit(self, text: str) -> None:
        try:
            print(text, file=self._stream, flush=True)
        except Exception:
            # 닫히거나 끊긴 콘솔 때문에 provider 결과와 로컬 증거를 잃지 않는다.
            self._stop.set()
