"""HMDA 합성 데이터 지표 생성 및 검증 테스트."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import duckdb
import pytest

from project_pivot.hmda_data import (
    DuckDBConnectionManager,
    freshness_delay,
    null_spike,
    row_count_drop,
    schema_drift,
)
from project_pivot.hmda_data.errors import SyntheticCaseError


def test_synthetic_cases_expose_expected_defect_statistics(
    tmp_path: Path,
    hmda_csv_path: Path,
) -> None:
    """HMDA 이상 파일이 기대 통계를 드러내는지 검증한다."""

    case_root = tmp_path / "cases"
    stale_observed_at = datetime(2025, 1, 1, tzinfo=UTC)

    with DuckDBConnectionManager() as connection:
        row_drop_path = row_count_drop(
            connection,
            [hmda_csv_path],
            case_root,
            sample_fraction=0.5,
        )
        null_path = null_spike(
            connection,
            [hmda_csv_path],
            case_root,
            null_fraction=0.5,
            sample_fraction=1,
        )
        drift_path = schema_drift(
            connection,
            [hmda_csv_path],
            case_root,
            sample_fraction=1,
        )
        freshness_path = freshness_delay(
            connection,
            [hmda_csv_path],
            case_root,
            observed_at=stale_observed_at,
            sample_fraction=1,
        )

        row_drop_count = _row_count(connection, row_drop_path)
        null_ratio = _null_ratio(connection, null_path, "income")
        drift_type = _column_type(connection, drift_path, "loan_amount")
        freshness_gap = _freshness_gap(
            connection,
            freshness_path,
            stale_observed_at + timedelta(days=45),
        )

    assert row_drop_count == 1
    assert null_ratio >= 0.5
    assert drift_type == "VARCHAR"
    assert freshness_gap > timedelta(days=30)


def test_synthetic_case_rejects_missing_columns(
    tmp_path: Path,
    hmda_csv_path: Path,
) -> None:
    """원천에 없는 컬럼 요청은 합성 데이터 예외로 실패한다."""

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(SyntheticCaseError, match="필요한 컬럼"),
    ):
        null_spike(
            connection,
            [hmda_csv_path],
            tmp_path / "cases",
            target_column="missing_column",
        )


def _row_count(
    connection: duckdb.DuckDBPyConnection,
    case_path: Path,
) -> int:
    row = connection.execute(
        "SELECT count(*) FROM read_parquet(?)",
        [str(case_path)],
    ).fetchone()
    assert row is not None
    return int(row[0])


def _null_ratio(
    connection: duckdb.DuckDBPyConnection,
    case_path: Path,
    column_name: str,
) -> float:
    row = connection.execute(
        f"""
        SELECT avg(CASE WHEN "{column_name}" IS NULL THEN 1.0 ELSE 0.0 END)
        FROM read_parquet(?)
        """,
        [str(case_path)],
    ).fetchone()
    assert row is not None
    return float(row[0])


def _column_type(
    connection: duckdb.DuckDBPyConnection,
    case_path: Path,
    column_name: str,
) -> str:
    rows = connection.execute(
        "DESCRIBE SELECT * FROM read_parquet(?) LIMIT 0",
        [str(case_path)],
    ).fetchall()
    return next(str(row[1]) for row in rows if row[0] == column_name)


def _freshness_gap(
    connection: duckdb.DuckDBPyConnection,
    case_path: Path,
    loaded_at: datetime,
) -> timedelta:
    row = connection.execute(
        "SELECT max(observed_at) FROM read_parquet(?)",
        [str(case_path)],
    ).fetchone()
    assert row is not None
    observed_at = row[0]
    assert isinstance(observed_at, datetime)
    return loaded_at - observed_at
