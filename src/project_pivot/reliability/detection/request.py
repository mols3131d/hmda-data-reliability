"""Detection 요청 모델."""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from project_pivot.reliability.contracts import ProfileSnapshot
from project_pivot.reliability.detection.thresholds import DetectionThresholds


class DetectionRequest(BaseModel):
    """baseline/current profile 비교 요청."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    baseline: ProfileSnapshot
    current: ProfileSnapshot
    owner: str = "data-platform"
    thresholds: DetectionThresholds = Field(default_factory=DetectionThresholds)

    @field_validator("owner")
    @classmethod
    def _validate_owner(cls, value: str) -> str:
        if not value.strip():
            msg = "owner는 비어 있을 수 없습니다."
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def _validate_snapshot_pair(self) -> Self:
        if self.baseline.asset_name != self.current.asset_name:
            msg = "baseline과 current asset_name은 같아야 합니다."
            raise ValueError(msg)
        return self
