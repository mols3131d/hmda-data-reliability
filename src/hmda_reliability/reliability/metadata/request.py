"""Table metadata evidence 요청 모델."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TableMetadataEvidenceRequest(BaseModel):
    """DuckDB table metadata를 Evidence로 변환하는 입력."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    asset_name: str
    table_name: str
    partition: str = "table"
    observed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("asset_name", "table_name", "partition")
    @classmethod
    def _validate_non_empty(cls, value: str) -> str:
        if not value.strip():
            msg = "값은 비어 있을 수 없습니다."
            raise ValueError(msg)
        return value
