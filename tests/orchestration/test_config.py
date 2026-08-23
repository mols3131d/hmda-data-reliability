"""Tests for the framework-independent orchestration runtime adapter."""

from pathlib import Path

import pytest

from hmda_reliability.data_operations import DataOperationRequest
from hmda_reliability.orchestration.config import data_operation_request_from_runtime

pytestmark = pytest.mark.unit


def test_runtime_adapter_returns_request_defaults() -> None:
    request = data_operation_request_from_runtime({}, environment={})

    assert request == DataOperationRequest()


def test_runtime_adapter_applies_environment_values() -> None:
    request = data_operation_request_from_runtime(
        {},
        environment={
            "PROJECT_PIVOT_DUCKDB_PATH": "scratch/environment.duckdb",
            "PROJECT_PIVOT_SOURCE_ROOT": "scratch/environment-hmda",
            "PROJECT_PIVOT_SOURCE_YEAR": "2024",
        },
    )

    assert request.database_path == Path("scratch/environment.duckdb")
    assert request.source_root == Path("scratch/environment-hmda")
    assert request.source_year == 2024


def test_runtime_adapter_applies_explicit_values() -> None:
    request = data_operation_request_from_runtime(
        {
            "database_path": "scratch/configured.duckdb",
            "source_root": "scratch/configured-hmda",
            "source_year": 2024,
            "source_file": "loans.csv",
            "run_dbt_build": False,
        },
        environment={},
    )

    assert request.database_path == Path("scratch/configured.duckdb")
    assert request.source_root == Path("scratch/configured-hmda")
    assert request.source_year == 2024
    assert request.source_file == "loans.csv"
    assert request.run_dbt_build is False


def test_runtime_adapter_prefers_explicit_values_over_environment() -> None:
    request = data_operation_request_from_runtime(
        {"database_path": "scratch/configured.duckdb"},
        environment={
            "PROJECT_PIVOT_DUCKDB_PATH": "scratch/environment.duckdb",
        },
    )

    assert request.database_path == Path("scratch/configured.duckdb")


def test_valid_explicit_value_masks_invalid_environment_value() -> None:
    request = data_operation_request_from_runtime(
        {"source_year": 2025},
        environment={"PROJECT_PIVOT_SOURCE_YEAR": "not-a-year"},
    )

    assert request.source_year == 2025


def test_runtime_adapter_rejects_invalid_explicit_year() -> None:
    with pytest.raises(ValueError, match="source_year"):
        data_operation_request_from_runtime(
            {"source_year": 1999},
            environment={},
        )


@pytest.mark.parametrize("field", ["database_path", "source_root"])
def test_runtime_adapter_rejects_empty_explicit_path(field: str) -> None:
    with pytest.raises(ValueError, match=field):
        data_operation_request_from_runtime({field: ""}, environment={})


def test_runtime_adapter_rejects_empty_source_file() -> None:
    with pytest.raises(ValueError, match="source_file"):
        data_operation_request_from_runtime({"source_file": ""}, environment={})
