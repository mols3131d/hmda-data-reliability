"""Framework-independent runtime configuration for the data-plane adapter."""

from __future__ import annotations

import os
from collections.abc import Mapping

from project_pivot.data_operations import (
    DataOperationRequest,
    data_operation_request_from_environment,
)

_ENVIRONMENT_KEYS = {
    "database_path": "PROJECT_PIVOT_DUCKDB_PATH",
    "source_root": "PROJECT_PIVOT_SOURCE_ROOT",
    "source_year": "PROJECT_PIVOT_SOURCE_YEAR",
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
    """Build the final request from explicit runtime values and environment.

    Explicit non-``None`` values take precedence over supported environment
    values. ``DataOperationRequest`` performs the final validation after both
    sources are combined.
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
