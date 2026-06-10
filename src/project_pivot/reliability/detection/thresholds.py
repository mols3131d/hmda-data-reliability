"""Detection threshold 설정 모델."""

from pydantic import BaseModel, ConfigDict, Field


class DetectionThresholds(BaseModel):
    """기본 profile comparison threshold."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    volume_drop_ratio: float = Field(default=0.5, ge=0.0, le=1.0)
    null_spike_delta: float = Field(default=0.1, ge=0.0, le=1.0)
    freshness_delay_minutes: float = Field(default=60.0, ge=0.0)
