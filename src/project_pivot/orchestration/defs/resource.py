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
    run_dbt_build: bool = True

    def to_request(self) -> DataOperationRequest:
        """Dagster 설정을 데이터 작업 요청으로 변환한다."""

        return DataOperationRequest(
            database_path=Path(self.database_path),
            source_root=Path(self.source_root),
            source_year=self.source_year,
            source_file=self.source_file,
            run_dbt_build=self.run_dbt_build,
        )
