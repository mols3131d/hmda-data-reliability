"""Taxi 적재 내부 공통 헬퍼."""

from __future__ import annotations

import duckdb

from project_pivot.logger import get_logger
from project_pivot.taxi_data.errors import TaxiDataLoadError
from project_pivot.taxi_data.sql import qualify_table_name, quote_identifier

YELLOW_TRIPDATA_TABLE = "raw.yellow_tripdata"
YELLOW_TRIPDATA_TIMESTAMP_COLUMN = "tpep_pickup_datetime"
LOGGER = get_logger("project_pivot.taxi_data.ingestion")


def ensure_schema(
    connection: duckdb.DuckDBPyConnection,
    schema_name: str = "raw",
) -> None:
    connection.execute(f"CREATE SCHEMA IF NOT EXISTS {quote_identifier(schema_name)}")


def table_row_count(
    connection: duckdb.DuckDBPyConnection,
    table_name: str,
) -> int:
    result = connection.execute(
        f"SELECT count(*) FROM {qualify_table_name(table_name)}"
    ).fetchone()
    if result is None:
        msg = f"테이블 행 수를 조회할 수 없습니다: {table_name}"
        raise TaxiDataLoadError(msg)
    return int(result[0])


def yellow_tripdata_source_projection() -> str:
    return """
            * EXCLUDE (filename),
            filename AS source_file,
            regexp_extract(
                filename,
                'yellow_tripdata_(\\d{4}-\\d{2})\\.parquet$',
                1
            ) AS source_partition
    """
