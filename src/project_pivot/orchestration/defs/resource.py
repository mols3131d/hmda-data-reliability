"""Dagster resource for Pipeline pipeline configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dagster import ConfigurableResource

from project_pivot.pipeline import PipelineRunRequest


class PipelineDagsterResource(ConfigurableResource[Any]):
    """Dagster에서 Pipeline pipeline request를 만드는 config resource."""

    database_path: str = "data/project_pivot.duckdb"
    source_root: str = "data/raw/hmda"
    source_year: int = 2025
    source_file: str | None = None
    report_path: str = "scratch/evaluation/dagster_pipeline_report.md"
    run_dbt_build: bool = True
    run_backfill: bool = False
    simulate_row_count_ratio: float = 0.25

    def to_request(self) -> PipelineRunRequest:
        """Dagster config를 pipeline request로 변환한다."""

        return PipelineRunRequest(
            database_path=Path(self.database_path),
            source_root=Path(self.source_root),
            source_year=self.source_year,
            source_file=self.source_file,
            report_path=Path(self.report_path),
            run_dbt_build=self.run_dbt_build,
            run_backfill=self.run_backfill,
            simulate_row_count_ratio=self.simulate_row_count_ratio,
        )
