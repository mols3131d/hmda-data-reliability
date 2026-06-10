"""승인된 backfill 실행 요청 모델."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from project_pivot.reliability.contracts import Approval
from project_pivot.reliability.profiling import ProfileSnapshotRequest
from project_pivot.taxi_data.ingestion import YELLOW_TRIPDATA_TABLE


class ApprovedBackfillRequest(BaseModel):
    """Approval gate 이후 partition overwrite와 validation 입력."""

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    approval: Approval
    parquet_paths: tuple[Path, ...] = Field(min_length=1)
    partition_date: date
    profile_request: ProfileSnapshotRequest
    table_name: str = YELLOW_TRIPDATA_TABLE

    @field_validator("parquet_paths", mode="before")
    @classmethod
    def _coerce_parquet_paths(cls, value: object) -> tuple[Path, ...]:
        if isinstance(value, str | Path):
            return (Path(value),)
        if isinstance(value, list | tuple):
            return tuple(Path(path) for path in value)
        msg = "parquet_paths는 path 목록이어야 합니다."
        raise ValueError(msg)

    @field_validator("table_name")
    @classmethod
    def _validate_table_name(cls, value: str) -> str:
        if not value.strip():
            msg = "table_name은 비어 있을 수 없습니다."
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def _validate_profile_partition(self) -> ApprovedBackfillRequest:
        if self.profile_request.partition != self.partition_date:
            msg = "profile_request.partition은 partition_date와 같아야 합니다."
            raise ValueError(msg)
        if self.profile_request.table_name != self.table_name:
            msg = "profile_request.table_name은 table_name과 같아야 합니다."
            raise ValueError(msg)
        return self


def approved_backfill_request(
    *,
    approval: Approval,
    parquet_paths: tuple[Path, ...],
    partition_date: date,
    profile_request: ProfileSnapshotRequest,
    table_name: str = YELLOW_TRIPDATA_TABLE,
) -> ApprovedBackfillRequest:
    """명시 인자로 approved backfill 요청을 만든다."""

    return ApprovedBackfillRequest(
        approval=approval,
        parquet_paths=parquet_paths,
        partition_date=partition_date,
        profile_request=profile_request,
        table_name=table_name,
    )
