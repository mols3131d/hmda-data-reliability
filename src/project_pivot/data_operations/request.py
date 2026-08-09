"""HMDA loans 데이터 작업 요청 모델."""

from __future__ import annotations

import os
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DataOperationRequest(BaseModel):
    """현재 hmda_loans 데이터셋 처리를 위한 데이터 작업 입력."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    database_path: Path = Path("data/project_pivot.duckdb")
    source_root: Path = Path("data/raw/hmda")
    source_year: int = Field(default=2025, ge=2000, le=2100)
    source_file: str | None = None
    asset_name: str = "source.project_pivot.raw.hmda_loans"
    raw_table_name: str = "raw.hmda_loans"
    partition_column: str = "activity_year"
    profile_columns: tuple[str, ...] = ("loan_amount", "income")
    freshness_column: str | None = None
    observed_at: datetime | None = None
    dbt_project_dir: Path = Path("dbt")
    dbt_profiles_dir: Path = Path("dbt")
    dbt_manifest_path: Path = Path("dbt/target/manifest.json")
    dbt_run_results_path: Path = Path("dbt/target/run_results.json")
    run_dbt_build: bool = True

    @field_validator("database_path", "source_root", mode="before")
    @classmethod
    def _validate_non_empty_path(cls, value: Path | str) -> Path | str:
        if isinstance(value, str) and not value.strip():
            msg = "경로는 비어 있을 수 없습니다."
            raise ValueError(msg)
        return value

    @field_validator(
        "asset_name",
        "raw_table_name",
        "partition_column",
        "freshness_column",
        "source_file",
    )
    @classmethod
    def _validate_non_empty(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            msg = "값은 비어 있을 수 없습니다."
            raise ValueError(msg)
        return value

    @field_validator("profile_columns", mode="before")
    @classmethod
    def _coerce_profile_columns(cls, value: object) -> tuple[str, ...]:
        if isinstance(value, str):
            return (value,)
        if isinstance(value, list | tuple):
            return tuple(str(item) for item in value)
        msg = "profile_columns는 문자열 목록이어야 합니다."
        raise ValueError(msg)

    @field_validator("profile_columns")
    @classmethod
    def _validate_profile_columns(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value:
            msg = "profile_columns는 비어 있을 수 없습니다."
            raise ValueError(msg)
        invalid_columns = [column for column in value if not column.strip()]
        if invalid_columns:
            msg = "profile_columns는 빈 컬럼명을 포함할 수 없습니다."
            raise ValueError(msg)
        return value


def data_operation_request_from_environment(
    environment: Mapping[str, str] | None = None,
) -> DataOperationRequest:
    """지원되는 pipeline environment override로 실행 request를 생성한다."""

    values = os.environ if environment is None else environment
    overrides = {
        field: values[key]
        for key, field in (
            ("PROJECT_PIVOT_DUCKDB_PATH", "database_path"),
            ("PROJECT_PIVOT_SOURCE_ROOT", "source_root"),
            ("PROJECT_PIVOT_SOURCE_YEAR", "source_year"),
        )
        if key in values
    }
    return DataOperationRequest(**overrides)
