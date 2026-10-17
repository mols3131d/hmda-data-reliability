"""Detection threshold 설정 모델."""

from pydantic import BaseModel, ConfigDict, Field


class DetectionThresholds(BaseModel):
    """Volume/null은 양의 악화 기준이며 0은 어떤 양의 악화도 탐지한다.

    Freshness는 current의 절대 age가 최대 허용 나이 이상인지 판정한다.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    volume_drop_ratio: float = Field(default=0.5, ge=0.0, le=1.0)
    null_spike_delta: float = Field(default=0.1, ge=0.0, le=1.0)
    freshness_max_age_minutes: float = Field(default=60.0, ge=0.0)
