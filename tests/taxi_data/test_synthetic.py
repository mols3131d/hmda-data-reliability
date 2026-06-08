"""합성 데이터(Synthetic Cases) 지표 생성 및 검증 테스트."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import duckdb
import pytest

from project_pivot.taxi_data import (
    DuckDBConnectionManager,
    freshness_delay,
    null_spike,
    row_count_drop,
    schema_drift,
    write_normal_case,
)
from project_pivot.taxi_data.errors import SyntheticCaseError


def test_synthetic_cases_expose_expected_defect_statistics(
    tmp_path: Path,
    tripdata_parquet_path: Path,
) -> None:
    """5가지 정상/이상 파티션이 DuckDB에서 기대 통계를 드러내는지 검증한다."""
    case_root = tmp_path / "cases"
    stale_observed_at = datetime(2024, 1, 1, tzinfo=UTC)

    with DuckDBConnectionManager() as connection:
        normal_path = write_normal_case(
            connection,
            [tripdata_parquet_path],
            case_root,
            sample_fraction=1,
            observed_at=datetime(2024, 1, 31, tzinfo=UTC),
        )
        row_drop_path = row_count_drop(
            connection,
            [tripdata_parquet_path],
            case_root,
            sample_fraction=0.25,
        )
        null_path = null_spike(
            connection,
            [tripdata_parquet_path],
            case_root,
            null_fraction=0.25,
            sample_fraction=1,
        )
        drift_path = schema_drift(
            connection,
            [tripdata_parquet_path],
            case_root,
            text_columns=("total_amount",),
            sample_fraction=1,
        )
        freshness_path = freshness_delay(
            connection,
            [tripdata_parquet_path],
            case_root,
            observed_at=stale_observed_at,
            sample_fraction=1,
        )

        normal_stats = _case_stats(connection, normal_path)
        row_drop_stats = _case_stats(connection, row_drop_path)
        null_ratio = _null_ratio(connection, null_path, "total_amount")
        drift_type = _column_type(connection, drift_path, "total_amount")
        freshness_gap = _freshness_gap(
            connection,
            freshness_path,
            stale_observed_at + timedelta(days=45),
        )

    assert normal_stats == (16, 4)
    assert row_drop_stats == (4, 4)
    assert null_ratio >= 0.05
    assert drift_type == "VARCHAR"
    assert freshness_gap > timedelta(days=30)


def test_sampling_is_stable_when_timestamps_tie(tmp_path: Path) -> None:
    """같은 타임스탬프 행의 물리 순서가 달라도 같은 샘플을 고른다."""
    ascending_path = tmp_path / "ascending.parquet"
    descending_path = tmp_path / "descending.parquet"

    with DuckDBConnectionManager() as connection:
        _write_tied_tripdata(connection, ascending_path, descending=False)
        _write_tied_tripdata(connection, descending_path, descending=True)

        ascending_case = row_count_drop(
            connection,
            [ascending_path],
            tmp_path / "ascending_cases",
            sample_fraction=0.5,
        )
        descending_case = row_count_drop(
            connection,
            [descending_path],
            tmp_path / "descending_cases",
            sample_fraction=0.5,
        )

        assert _sampled_vendor_ids(connection, ascending_case) == _sampled_vendor_ids(
            connection,
            descending_case,
        )


def test_synthetic_case_wraps_duckdb_errors(tmp_path: Path) -> None:
    """원천 Parquet 오류가 합성 데이터 도메인 예외로 변환되는지 검증한다."""
    missing_source_path = tmp_path / "missing.parquet"

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(SyntheticCaseError, match="스키마 조회"),
    ):
        null_spike(connection, [missing_source_path], tmp_path / "cases")


def _case_glob(case_path: Path) -> str:
    return str(case_path / "**/*.parquet")


def _case_stats(
    connection: duckdb.DuckDBPyConnection,
    case_path: Path,
) -> tuple[int, int]:
    row = connection.execute(
        """
        SELECT count(*), count(DISTINCT pickup_date)
        FROM read_parquet(?, hive_partitioning = true)
        """,
        [_case_glob(case_path)],
    ).fetchone()
    assert row is not None
    return int(row[0]), int(row[1])


def _null_ratio(
    connection: duckdb.DuckDBPyConnection,
    case_path: Path,
    column_name: str,
) -> float:
    row = connection.execute(
        f"""
        SELECT avg(CASE WHEN "{column_name}" IS NULL THEN 1.0 ELSE 0.0 END)
        FROM read_parquet(?, hive_partitioning = true)
        """,
        [_case_glob(case_path)],
    ).fetchone()
    assert row is not None
    return float(row[0])


def _column_type(
    connection: duckdb.DuckDBPyConnection,
    case_path: Path,
    column_name: str,
) -> str:
    rows = connection.execute(
        "DESCRIBE SELECT * FROM read_parquet(?, hive_partitioning = true) LIMIT 0",
        [_case_glob(case_path)],
    ).fetchall()
    return next(str(row[1]) for row in rows if row[0] == column_name)


def _freshness_gap(
    connection: duckdb.DuckDBPyConnection,
    case_path: Path,
    loaded_at: datetime,
) -> timedelta:
    row = connection.execute(
        """
        SELECT max(observed_at)
        FROM read_parquet(?, hive_partitioning = true)
        """,
        [_case_glob(case_path)],
    ).fetchone()
    assert row is not None
    observed_at = row[0]
    assert isinstance(observed_at, datetime)
    return loaded_at - observed_at


def _write_tied_tripdata(
    connection: duckdb.DuckDBPyConnection,
    path: Path,
    *,
    descending: bool,
) -> None:
    direction = "DESC" if descending else "ASC"
    connection.execute(
        f"""
        COPY (
            SELECT
                vendor_id AS VendorID,
                TIMESTAMP '2024-01-01 08:00:00' AS tpep_pickup_datetime,
                TIMESTAMP '2024-01-01 08:15:00' AS tpep_dropoff_datetime,
                1::BIGINT AS passenger_count,
                vendor_id::DOUBLE AS trip_distance,
                1 AS PULocationID,
                2 AS DOLocationID,
                1::BIGINT AS payment_type,
                10.0 AS fare_amount,
                (10.0 + vendor_id)::DOUBLE AS total_amount
            FROM range(1, 5) AS rows(vendor_id)
            ORDER BY vendor_id {direction}
        )
        TO ?
        (FORMAT PARQUET)
        """,
        [str(path)],
    )


def _sampled_vendor_ids(
    connection: duckdb.DuckDBPyConnection,
    case_path: Path,
) -> set[int]:
    rows = connection.execute(
        """
        SELECT VendorID
        FROM read_parquet(?, hive_partitioning = true)
        """,
        [_case_glob(case_path)],
    ).fetchall()
    return {int(row[0]) for row in rows}
