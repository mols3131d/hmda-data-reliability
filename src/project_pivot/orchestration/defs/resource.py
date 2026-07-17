"""데이터 작업 설정용 Dagster resource."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dagster import ConfigurableResource

from project_pivot.data_operations import DataOperationRequest


class DataOperationsResource(ConfigurableResource[Any]):
    """Dagster 설정을 데이터 작업 요청으로 변환한다."""

    database_path: str = "data/project_pivot.duckdb"
    source_root: str = "data/raw/hmda"
    source_year: int = 2025
    source_file: str | None = None
    report_path: str = "scratch/evaluation/dagster_data_operations_report.md"
    run_dbt_build: bool = True
    run_backfill: bool = False
    simulate_row_count_ratio: float = 0.25

    def to_request(self) -> DataOperationRequest:
        """Dagster 설정을 데이터 작업 요청으로 변환한다."""

        return DataOperationRequest(
            database_path=Path(self.database_path),
            source_root=Path(self.source_root),
            source_year=self.source_year,
            source_file=self.source_file,
            report_path=Path(self.report_path),
            run_dbt_build=self.run_dbt_build,
            run_backfill=self.run_backfill,
            simulate_row_count_ratio=self.simulate_row_count_ratio,
        )
