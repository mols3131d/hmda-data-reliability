"""Profile snapshot 계산 요청 모델."""

from __future__ import annotations

from datetime import UTC, date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

type ProfilePartition = date | int | str


class ProfileSnapshotRequest(BaseModel):
    """DuckDB asset partition profile 계산 입력."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    asset_name: str
    table_name: str
    partition_column: str
    partition: ProfilePartition
    profile_columns: tuple[str, ...] = Field(default_factory=tuple)
    freshness_column: str | None = None
    observed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator(
        "asset_name",
        "table_name",
        "partition_column",
        "freshness_column",
    )
    @classmethod
    def _validate_optional_identifier(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            msg = "값은 비어 있을 수 없습니다."
            raise ValueError(msg)
        return value

    @field_validator("profile_columns")
    @classmethod
    def _validate_profile_columns(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        empty_columns = [column for column in value if not column.strip()]
        if empty_columns:
            msg = "profile_columns는 빈 컬럼명을 포함할 수 없습니다."
            raise ValueError(msg)
        return value
