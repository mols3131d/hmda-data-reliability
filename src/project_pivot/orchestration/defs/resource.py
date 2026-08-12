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
    """Dagster config override를 ``DataOperationRequest`` contract에 투영한다.

    각 field가 ``None``이면 지원되는 environment 값 또는 request 기본값을 유지한다.
    명시된 값은 동일 field의 environment 값보다 우선한다.
    """

    database_path: str | None = None
    source_root: str | None = None
    source_year: int | None = None
    source_file: str | None = None
    run_dbt_build: bool | None = None

    def to_request(self) -> DataOperationRequest:
        """명시 config > 지원 environment > request 기본값 순서로 요청을 만든다.

        최종 값은 ``DataOperationRequest``를 다시 생성해 동일한 validation을 적용한다.
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
        # 명시 config가 가리는 environment 값은 먼저 제거한다. 그렇지 않으면
        # 사용되지 않을 잘못된 environment 값도 request 생성 단계에서 실패할 수 있다.
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
