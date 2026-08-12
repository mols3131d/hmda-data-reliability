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
    """명시된 Dagster field만 Data Operations request에 override한다."""

    database_path: str | None = None
    source_root: str | None = None
    source_year: int | None = None
    source_file: str | None = None
    run_dbt_build: bool | None = None

    def to_request(self) -> DataOperationRequest:
        """Dagster config를 우선해 최종 ``DataOperationRequest``를 만든다.

        명시되지 않은 field는 지원 environment 값 또는 request 기본값을 유지하며,
        반환값에는 ``DataOperationRequest`` validation을 다시 적용한다.
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
        # 같은 field의 명시 config가 있으면 environment 값을 먼저 숨긴다.
        # 그렇지 않으면 사용되지 않을 잘못된 값도 request 생성에서 실패할 수 있다.
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
