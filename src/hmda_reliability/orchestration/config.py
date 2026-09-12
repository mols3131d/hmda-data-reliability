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

    Precedence & Validation Rules:
        - `_SUPPORTED_OVERRIDES` 필드 중 non-None 명시적 값이 환경 변수보다 우선한다.
        - 명시적 값이 제공된 환경 변수 키는 base 환경에서 사전에 제거한다.
        - 결합된 값은 `DataOperationRequest` 모델 검증을 통해 유효한 요청으로 변환된다.

    Returns:
        DataOperationRequest: 유효성이 검증된 불변 요청 객체.
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
