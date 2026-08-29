"""데이터 플레인 어댑터를 위한 프레임워크 독립적 런타임 설정 모듈."""

from __future__ import annotations

import os
from collections.abc import Mapping

from hmda_reliability.data_operations import (
    DataOperationRequest,
    data_operation_request_from_environment,
)

_ENVIRONMENT_KEYS = {
    "database_path": "HMDA_RELIABILITY_DUCKDB_PATH",
    "source_root": "HMDA_RELIABILITY_SOURCE_ROOT",
    "source_year": "HMDA_RELIABILITY_SOURCE_YEAR",
}
_SUPPORTED_OVERRIDES = frozenset(
    {
        "database_path",
        "source_root",
        "source_year",
        "source_file",
        "run_dbt_build",
    }
)


def data_operation_request_from_runtime(
    overrides: Mapping[str, object],
    environment: Mapping[str, str] | None = None,
) -> DataOperationRequest:
    """명시적 런타임 오버라이드와 환경 변수를 조합하여 최종 요청 객체를 생성한다.

    명시적인 non-None 값은 환경 변수 값보다 우선순위를 갖는다.
    두 소스가 결합된 후 `DataOperationRequest`에서 최종 유효성 검증을 수행한다.
    """

    explicit = {
        field: value
        for field, value in overrides.items()
        if field in _SUPPORTED_OVERRIDES and value is not None
    }
    environment_values = dict(os.environ if environment is None else environment)
    for field, key in _ENVIRONMENT_KEYS.items():
        if field in explicit:
            environment_values.pop(key, None)

    request = data_operation_request_from_environment(environment_values)
    values = request.model_dump()
    values.update(explicit)
    return DataOperationRequest(**values)
