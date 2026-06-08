"""Taxi 일자 파티션 적재 테스트."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from project_pivot.taxi_data import (
    DuckDBConnectionManager,
    load_yellow_tripdata_partition,
)
from project_pivot.taxi_data.errors import TaxiDataLoadError
from project_pivot.taxi_data.sql import quote_string_literal


def test_partition_loader_overwrites_without_duplicates_and_keeps_outliers(
    tmp_path: Path,
) -> None:
    """일자 파티션 재적재가 중복을 만들지 않고 이상치 날짜를 보존한다."""
    source_path = tmp_path / "yellow_tripdata_2024-01.parquet"

    with DuckDBConnectionManager() as connection:
        _write_partition_tripdata(connection, source_path)

        first_count = load_yellow_tripdata_partition(
            connection,
            [source_path],
            "2024-01-15",
        )
        second_count = load_yellow_tripdata_partition(
            connection,
            [source_path],
            "2024-01-15",
        )
        outlier_count = load_yellow_tripdata_partition(
            connection,
            [source_path],
            "2008-12-31",
        )
        partition_stats = connection.execute(
            """
            SELECT count(*), count(DISTINCT VendorID)
            FROM raw.yellow_tripdata
            WHERE CAST(tpep_pickup_datetime AS DATE) = DATE '2024-01-15'
            """
        ).fetchone()
        outlier_stats = connection.execute(
            """
            SELECT count(*), min(source_partition), max(source_partition)
            FROM raw.yellow_tripdata
            WHERE CAST(tpep_pickup_datetime AS DATE) = DATE '2008-12-31'
            """
        ).fetchone()

    assert first_count == 2
    assert second_count == 2
    assert outlier_count == 1
    assert partition_stats == (2, 2)
    assert outlier_stats == (1, "2024-01", "2024-01")


def test_partition_loader_rejects_empty_source_before_deleting_target(
    tmp_path: Path,
) -> None:
    """소스에 대상 날짜가 없으면 기존 파티션을 보존하고 실패한다."""
    source_path = tmp_path / "yellow_tripdata_2024-01.parquet"
    empty_source_path = tmp_path / "yellow_tripdata_2024-01-refresh.parquet"

    with DuckDBConnectionManager() as connection:
        _write_partition_tripdata(connection, source_path)
        _write_single_day_tripdata(connection, empty_source_path, "2024-01-16")

        assert load_yellow_tripdata_partition(
            connection,
            [source_path],
            "2024-01-15",
        ) == 2
        with pytest.raises(TaxiDataLoadError, match="소스 파티션에 적재할 행"):
            load_yellow_tripdata_partition(
                connection,
                [empty_source_path],
                "2024-01-15",
            )

        partition_count = connection.execute(
            """
            SELECT count(*)
            FROM raw.yellow_tripdata
            WHERE CAST(tpep_pickup_datetime AS DATE) = DATE '2024-01-15'
            """
        ).fetchone()

    assert partition_count == (2,)


def _write_partition_tripdata(
    connection: duckdb.DuckDBPyConnection,
    path: Path,
) -> None:
    connection.execute(
        """
        COPY (
            SELECT
                vendor_id AS VendorID,
                pickup_at AS tpep_pickup_datetime,
                pickup_at + INTERVAL '15 minutes' AS tpep_dropoff_datetime,
                1::BIGINT AS passenger_count,
                vendor_id::DOUBLE AS trip_distance,
                1 AS PULocationID,
                2 AS DOLocationID,
                1::BIGINT AS payment_type,
                10.0 AS fare_amount,
                (10.0 + vendor_id)::DOUBLE AS total_amount
            FROM (
                VALUES
                    (1, TIMESTAMP '2024-01-15 08:00:00'),
                    (2, TIMESTAMP '2024-01-15 09:00:00'),
                    (3, TIMESTAMP '2024-01-16 08:00:00'),
                    (4, TIMESTAMP '2008-12-31 23:59:00')
            ) AS rows(vendor_id, pickup_at)
        )
        TO ?
        (FORMAT PARQUET)
        """,
        [str(path)],
    )


def _write_single_day_tripdata(
    connection: duckdb.DuckDBPyConnection,
    path: Path,
    pickup_date: str,
) -> None:
    target_path = quote_string_literal(str(path))
    connection.execute(
        f"""
        COPY (
            SELECT
                1 AS VendorID,
                CAST(? AS TIMESTAMP) AS tpep_pickup_datetime,
                CAST(? AS TIMESTAMP) + INTERVAL '15 minutes'
                    AS tpep_dropoff_datetime,
                1::BIGINT AS passenger_count,
                1.0 AS trip_distance,
                1 AS PULocationID,
                2 AS DOLocationID,
                1::BIGINT AS payment_type,
                10.0 AS fare_amount,
                11.0 AS total_amount
        )
        TO {target_path}
        (FORMAT PARQUET)
        """,
        [f"{pickup_date} 08:00:00", f"{pickup_date} 08:00:00"],
    )
