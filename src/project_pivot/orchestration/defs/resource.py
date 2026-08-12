"""Dagster config를 Data Operations request로 연결하는 resource."""

from __future__ import annotations

import os
from typing import Any

from dagster import ConfigurableResource

from project_pivot.data_operations import (
    DataOperationRequest,
    data_operation_request_from_environment,
)


class DataOperationsResource(ConfigurableResource[Any]):
    """``None``이 아닌 Dagster field만 Data Operations request에 override한다."""

    database_path: str | None = None
    source_root: str | None = None
    source_year: int | None = None
    source_file: str | None = None
    run_dbt_build: bool | None = None

    def to_request(self) -> DataOperationRequest:
        """Dagster config를 우선해 최종 ``DataOperationRequest``를 만든다.

        명시하지 않은 field는 지원 environment 값 또는 request 기본값을 유지하고,
        최종 request는 ``DataOperationRequest`` validation을 따른다.
        """

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
        # 명시 config가 가린 잘못된 environment 값이 선행 request 생성을
        # 실패시키지 않게 한다.
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
