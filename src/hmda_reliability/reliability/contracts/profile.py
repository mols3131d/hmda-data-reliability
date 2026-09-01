"""프로파일 스냅샷 계약 모델 정의 모듈."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import Field, field_validator, model_validator

from hmda_reliability.reliability.contracts.base import ReliabilityContract


class FreshnessMeasurementStatus(StrEnum):
    """프로파일 Freshness 측정 가용성 상태."""

    MEASURED = "measured"
    UNAVAILABLE = "unavailable"


class ProfileSnapshot(ReliabilityContract):
    """파티션에 대한 결정론적 프로파일 스냅샷 계약."""

    snapshot_id: str
    asset_name: str
    partition: str
    observed_at: datetime
    row_count: int = Field(ge=0)
    null_rates: dict[str, float] = Field(default_factory=dict)
    schema_hash: str
    freshness_at: datetime | None
    freshness_status: FreshnessMeasurementStatus
    metric_values: dict[str, float] = Field(default_factory=dict)

    @field_validator("observed_at", "freshness_at")
    @classmethod
    def _normalize_timestamp(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def _validate_profile(self) -> "ProfileSnapshot":
        invalid_columns = [
            column
            for column, null_rate in self.null_rates.items()
            if null_rate < 0 or null_rate > 1
        ]
        if invalid_columns:
            joined_columns = ", ".join(sorted(invalid_columns))
            raise ValueError(f"null_rates must be between 0 and 1: {joined_columns}")
        if (
            self.freshness_status is FreshnessMeasurementStatus.MEASURED
            and self.freshness_at is None
        ):
            msg = "measured freshness에는 freshness_at이 필요합니다."
            raise ValueError(msg)
        if (
            self.freshness_status is FreshnessMeasurementStatus.UNAVAILABLE
            and self.freshness_at is not None
        ):
            msg = "unavailable freshness에는 freshness_at을 제공할 수 없습니다."
            raise ValueError(msg)
        return self
