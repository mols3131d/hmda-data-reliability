"""본문과 설정을 포함하지 않는 선택적 단계 관측 계약."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from hmda_reliability.review_ai.staged.contracts import StageId
from hmda_reliability.review_ai.staged.evidence import StagedReviewStatus


@dataclass(frozen=True)
class StageProgress:
    stage_id: StageId
    phase: Literal[
        "stage_started", "provider_started", "provider_finished", "stage_finished"
    ]
    status: StagedReviewStatus | None = None
    attempt_count: int = 0


type ProgressCallback = Callable[[StageProgress], None]
