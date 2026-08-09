"""데이터 작업 설정용 Dagster resource."""

from __future__ import annotations

import os
from typing import Any

from dagster import ConfigurableResource

from project_pivot.data_operations import (
    DataOperationRequest,
    data_operation_request_from_environment,
)


class DataOperationsResource(ConfigurableResource[Any]):
    """Dagster 설정을 데이터 작업 요청으로 변환한다."""

    database_path: str | None = None
    source_root: str | None = None
    source_year: int | None = None
    source_file: str | None = None
    run_dbt_build: bool | None = None

    def to_request(self) -> DataOperationRequest:
        """Dagster 설정을 데이터 작업 요청으로 변환한다."""

        overrides = {
            field: value
            for field, value in (
                (
                    "database_path",
                    self.database_path,
                ),
                (
                    "source_root",
                    self.source_root,
                ),
                ("source_year", self.source_year),
                ("source_file", self.source_file),
                ("run_dbt_build", self.run_dbt_build),
            )
            if value is not None
        }
        environment = os.environ.copy()
        for field, key in (
            ("database_path", "PROJECT_PIVOT_DUCKDB_PATH"),
            ("source_root", "PROJECT_PIVOT_SOURCE_ROOT"),
            ("source_year", "PROJECT_PIVOT_SOURCE_YEAR"),
        ):
            if field in overrides:
                environment.pop(key, None)

        request = data_operation_request_from_environment(environment)
        values = request.model_dump()
        values.update(overrides)
        return DataOperationRequest(**values)
