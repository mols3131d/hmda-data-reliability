"""Taxi 데이터 테스트용 pytest fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from project_pivot.taxi_data import DuckDBConnectionManager
from project_pivot.taxi_data.sql import quote_string_literal


@pytest.fixture
def zone_csv_path(tmp_path: Path) -> Path:
    """테스트용 taxi_zone_lookup.csv 파일을 생성한다."""
    path = tmp_path / "taxi_zone_lookup.csv"
    path.write_text(
        "\n".join(
            [
                "LocationID,Borough,Zone,service_zone",
                "1,EWR,Newark Airport,EWR",
                "2,Queens,Jamaica Bay,Boro Zone",
            ]
        ),
        encoding="utf-8",
    )
    return path


@pytest.fixture
def tripdata_parquet_path(tmp_path: Path) -> Path:
    """테스트용 yellow_tripdata_2024-01.parquet 파일을 생성한다."""
    path = tmp_path / "yellow_tripdata_2024-01.parquet"
    target_path = quote_string_literal(str(path))
    with DuckDBConnectionManager() as connection:
        connection.execute(
            f"""
            COPY (
                SELECT
                    1 AS VendorID,
                    TIMESTAMP '2024-01-01 08:00:00'
                        + day_offset * INTERVAL '1 day'
                        + row_number * INTERVAL '1 minute'
                        AS tpep_pickup_datetime,
                    TIMESTAMP '2024-01-01 08:15:00'
                        + day_offset * INTERVAL '1 day'
                        + row_number * INTERVAL '1 minute'
                        AS tpep_dropoff_datetime,
                    1::BIGINT AS passenger_count,
                    3.5 + row_number AS trip_distance,
                    1 AS PULocationID,
                    2 AS DOLocationID,
                    1::BIGINT AS payment_type,
                    10.0 AS fare_amount,
                    12.5 + row_number AS total_amount
                FROM range(4) AS days(day_offset)
                CROSS JOIN range(4) AS rows(row_number)
            )
            TO {target_path}
            (FORMAT PARQUET)
            """
        )
    return path
