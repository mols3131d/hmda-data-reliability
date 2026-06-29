"""MVP pipeline 실행 요청 모델."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MvpPipelineRunRequest(BaseModel):
    """로컬 MVP pipeline 실행 입력."""

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
    report_path: Path = Path("scratch/evaluation/pipeline_run_report.md")
    run_dbt_build: bool = True
    run_backfill: bool = False
    simulate_row_count_ratio: float = Field(default=0.25, gt=0, le=1)

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
