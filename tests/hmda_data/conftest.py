"""HMDA 데이터 테스트용 pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from hmda_reliability.data_platform.duckdb import DuckDBConnectionManager
from hmda_reliability.data_platform.sql import quote_string_literal


def _write_hmda_source(path: Path, query: str) -> Path:
    file_format = "CSV, HEADER" if path.suffix == ".csv" else "PARQUET"
    with DuckDBConnectionManager() as connection:
        connection.execute(
            f"COPY ({query}) TO ? (FORMAT {file_format})",
            [path.as_posix()],
        )
    return path


@pytest.fixture(
    params=[
        ("csv", "csv"),
        ("parquet", "parquet"),
        ("csv", "parquet"),
        ("parquet", "csv"),
    ],
    ids=["csv-csv", "parquet-parquet", "csv-parquet", "parquet-csv"],
)
def mixed_schema_source_paths(
    request: pytest.FixtureRequest,
    tmp_path: Path,
) -> tuple[Path, Path]:
    """정상 원천과 income/county_code가 없는 원천을 같은 연도로 만든다."""

    valid_format, missing_format = request.param
    valid_path = _write_hmda_source(
        tmp_path / f"valid_2025.{valid_format}",
        """
        SELECT 2025 AS activity_year, 1 AS loan_purpose, 1 AS action_taken,
               111000 AS loan_amount, 80 AS income,
               'TX' AS state_code, '48113' AS county_code
        """,
    )
    missing_path = _write_hmda_source(
        tmp_path / f"missing_2025.{missing_format}",
        """
        SELECT 2025 AS activity_year, 31 AS loan_purpose, 3 AS action_taken,
               222000 AS loan_amount, 'NY' AS state_code
        """,
    )
    return valid_path, missing_path


@pytest.fixture
def nullable_mixed_source_paths(tmp_path: Path) -> tuple[Path, Path]:
    csv_path = _write_hmda_source(
        tmp_path / "nullable_csv_2025.csv",
        """
        SELECT 2025 AS activity_year, 1 AS loan_purpose, 1 AS action_taken,
               111000 AS loan_amount, CAST(NULL AS INTEGER) AS income,
               'TX' AS state_code, '48113' AS county_code
        """,
    )
    parquet_path = _write_hmda_source(
        tmp_path / "nullable_parquet_2025.parquet",
        """
        SELECT 2025 AS activity_year, 31 AS loan_purpose, 3 AS action_taken,
               222000 AS loan_amount, CAST(NULL AS INTEGER) AS income,
               'NY' AS state_code, '36061' AS county_code
        """,
    )
    return csv_path, parquet_path


@pytest.fixture
def hmda_csv_path(tmp_path: Path) -> Path:
    """테스트용 HMDA CSV 파일을 생성한다."""

    path = tmp_path / "year_2025.csv"
    path.write_text(
        "\n".join(
            [
                "activity_year,loan_purpose,action_taken,loan_amount,income,state_code,county_code",
                "2025,1,1,350000,120,CA,06001",
                "2025,31,3,420000,95,NY,36061",
            ]
        ),
        encoding="utf-8",
    )
    return path


@pytest.fixture
def hmda_parquet_path(tmp_path: Path) -> Path:
    """테스트용 HMDA Parquet 파일을 생성한다."""

    path = tmp_path / "hmda_2024.parquet"
    target_path = quote_string_literal(str(path))
    with DuckDBConnectionManager() as connection:
        connection.execute(
            f"""
            COPY (
                SELECT
                    2024 AS activity_year,
                    1 AS loan_purpose,
                    2 AS action_taken,
                    250000 AS loan_amount,
                    88 AS income,
                    'TX' AS state_code,
                    '48113' AS county_code
            )
            TO {target_path}
            (FORMAT PARQUET)
            """
        )
    return path
