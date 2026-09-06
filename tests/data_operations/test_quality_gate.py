"""Data Operations quality gate composition tests."""

from __future__ import annotations

import importlib
from pathlib import Path

import duckdb
import pytest

from hmda_reliability.data_operations import DataOperationRequest, evaluate_quality_gate
from hmda_reliability.reliability import QualityGateError

pytestmark = pytest.mark.integration

_ACCEPTED_2025_INCOME_NULL_RATE = 0.16168766279822375


def _make_db_with_partition(tmp_path: Path, null_rate: float) -> Path:
    db_path = tmp_path / "quality_gate.duckdb"
    null_count = int(1000 * null_rate)

    with duckdb.connect(str(db_path)) as connection:
        connection.execute("CREATE SCHEMA raw")
        connection.execute(
            f"""
            CREATE TABLE raw.hmda_loans AS
            SELECT
                2025 AS activity_year,
                'CA' AS state_code,
                '001' AS county_code,
                1 AS loan_purpose,
                1 AS action_taken,
                200000 AS loan_amount,
                CASE
                    WHEN row_number() OVER () <= {null_count} THEN NULL
                    ELSE 80000
                END AS income,
                'year_2025.csv' AS source_file,
                2025 AS source_year
            FROM range(1000)
            """
        )

    return db_path


def _add_partition(database_path: Path, year: int, null_rate: float) -> None:
    null_count = int(1000 * null_rate)
    with duckdb.connect(str(database_path)) as connection:
        connection.execute(
            f"""
            INSERT INTO raw.hmda_loans
            SELECT
                {year} AS activity_year,
                'CA' AS state_code,
                '001' AS county_code,
                1 AS loan_purpose,
                1 AS action_taken,
                200000 AS loan_amount,
                CASE
                    WHEN row_number() OVER () <= {null_count} THEN NULL
                    ELSE 80000
                END AS income,
                'year_{year}.csv' AS source_file,
                {year} AS source_year
            FROM range(1000)
            """
        )


def test_evaluate_quality_gate_accepts_2025_normal_profile(tmp_path: Path) -> None:
    request = DataOperationRequest(
        database_path=_make_db_with_partition(
            tmp_path,
            null_rate=_ACCEPTED_2025_INCOME_NULL_RATE,
        ),
        source_year=2025,
    )

    evaluate_quality_gate(request)


def test_evaluate_quality_gate_blocks_spike_above_2025_profile(
    tmp_path: Path,
) -> None:
    request = DataOperationRequest(
        database_path=_make_db_with_partition(
            tmp_path,
            null_rate=_ACCEPTED_2025_INCOME_NULL_RATE + 0.051,
        ),
        source_year=2025,
    )

    with pytest.raises(QualityGateError, match=r"null_spike\(income\)"):
        evaluate_quality_gate(request)


def test_evaluate_quality_gate_profiles_requested_partition(tmp_path: Path) -> None:
    request = DataOperationRequest(
        database_path=_make_db_with_partition(tmp_path, null_rate=0.4),
        source_year=2025,
    )

    with pytest.raises(QualityGateError, match=r"null_spike\(income\)"):
        evaluate_quality_gate(request)


def test_evaluate_quality_gate_blocks_dirty_non_requested_partition(
    tmp_path: Path,
) -> None:
    database_path = _make_db_with_partition(
        tmp_path,
        null_rate=_ACCEPTED_2025_INCOME_NULL_RATE,
    )
    _add_partition(database_path, year=2026, null_rate=0.4)
    request = DataOperationRequest(database_path=database_path, source_year=2025)

    with pytest.raises(QualityGateError, match="source_year=2026"):
        evaluate_quality_gate(request)


@pytest.mark.parametrize(
    ("raw_table_name", "partition_column"),
    [
        ("raw.clean_loans", "activity_year"),
        ("raw.hmda_loans", "source_year"),
    ],
)
def test_evaluate_quality_gate_rejects_noncanonical_dbt_source(
    tmp_path: Path,
    raw_table_name: str,
    partition_column: str,
) -> None:
    database_path = _make_db_with_partition(tmp_path, null_rate=0.4)
    with duckdb.connect(str(database_path)) as connection:
        connection.execute(
            "CREATE TABLE raw.clean_loans AS SELECT * FROM raw.hmda_loans"
        )
        connection.execute("UPDATE raw.clean_loans SET income = 80000")
    request = DataOperationRequest(
        database_path=database_path,
        raw_table_name=raw_table_name,
        partition_column=partition_column,
        source_year=2025,
    )

    with pytest.raises(ValueError, match="canonical dbt source"):
        evaluate_quality_gate(request)


def test_evaluate_quality_gate_blocks_absent_requested_partition(
    tmp_path: Path,
) -> None:
    request = DataOperationRequest(
        database_path=_make_db_with_partition(
            tmp_path,
            null_rate=_ACCEPTED_2025_INCOME_NULL_RATE,
        ),
        source_year=2026,
    )

    with pytest.raises(QualityGateError, match="source_year=2026.*empty_partition"):
        evaluate_quality_gate(request)


def test_evaluate_quality_gate_blocks_null_partition_discriminator(
    tmp_path: Path,
) -> None:
    database_path = _make_db_with_partition(
        tmp_path,
        null_rate=_ACCEPTED_2025_INCOME_NULL_RATE,
    )
    with duckdb.connect(str(database_path)) as connection:
        connection.execute(
            """
            INSERT INTO raw.hmda_loans
            SELECT
                NULL AS activity_year,
                'CA' AS state_code,
                '001' AS county_code,
                1 AS loan_purpose,
                1 AS action_taken,
                200000 AS loan_amount,
                80000 AS income,
                'missing_year.csv' AS source_file,
                2026 AS source_year
            """
        )
    request = DataOperationRequest(database_path=database_path, source_year=2025)

    with pytest.raises(QualityGateError, match="missing_partition_discriminator"):
        evaluate_quality_gate(request)


def test_quality_gate_composition_has_no_airflow_dependency() -> None:
    quality_gate = importlib.import_module(
        "hmda_reliability.data_operations.quality_gate"
    )
    module_file = quality_gate.__file__ or ""

    source = Path(module_file).read_text()
    assert "from airflow" not in source
    assert "import airflow" not in source
