"""Dagster resource for MVP pipeline configuration."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from dagster import ConfigurableResource

from project_pivot.pipeline import MvpPipelineRunRequest


class MvpPipelineDagsterResource(ConfigurableResource[Any]):
    """Dagster에서 MVP pipeline request를 만드는 config resource."""

    database_path: str = "data/project_pivot.duckdb"
    source_root: str = "data/raw/tlc"
    year: int = 2024
    partition_date: str = "2024-01-15"
    report_path: str = "scratch/evaluation/dagster_pipeline_report.md"
    run_dbt_build: bool = True
    run_backfill: bool = False
    simulate_row_count_ratio: float = 0.25

    def to_request(self) -> MvpPipelineRunRequest:
        """Dagster config를 pipeline request로 변환한다."""

        return MvpPipelineRunRequest(
            database_path=Path(self.database_path),
            source_root=Path(self.source_root),
            year=self.year,
            partition_date=date.fromisoformat(self.partition_date),
            report_path=Path(self.report_path),
            run_dbt_build=self.run_dbt_build,
            run_backfill=self.run_backfill,
            simulate_row_count_ratio=self.simulate_row_count_ratio,
        )
