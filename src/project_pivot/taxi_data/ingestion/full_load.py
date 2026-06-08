"""Taxi 원천 테이블 전체 적재."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import duckdb

from project_pivot.taxi_data.errors import TaxiDataLoadError
from project_pivot.taxi_data.ingestion.common import (
    LOGGER,
    YELLOW_TRIPDATA_TABLE,
    ensure_schema,
    table_row_count,
    yellow_tripdata_source_projection,
)
from project_pivot.taxi_data.sql import qualify_table_name


def load_taxi_zones(
    connection: duckdb.DuckDBPyConnection,
    csv_path: str | Path,
    *,
    table_name: str = "raw.taxi_zones",
) -> int:
    """taxi_zone_lookup.csv를 raw.taxi_zones에 멱등 적재한다."""

    try:
        _create_taxi_zones_table(connection, csv_path, table_name=table_name)
        row_count = table_row_count(connection, table_name)
        LOGGER.debug(
            "택시 존 적재 완료",
            extra={
                "table_name": table_name,
                "csv_path": str(csv_path),
                "row_count": row_count,
            },
        )
        return row_count
    except duckdb.Error as exc:
        msg = f"택시 존 CSV 적재에 실패했습니다: table={table_name}, path={csv_path}"
        raise TaxiDataLoadError(msg) from exc


def load_yellow_tripdata(
    connection: duckdb.DuckDBPyConnection,
    parquet_paths: Sequence[str | Path],
    *,
    table_name: str = YELLOW_TRIPDATA_TABLE,
) -> int:
    """옐로우 택시 Parquet 파일을 raw.yellow_tripdata에 멱등 적재한다."""

    if not parquet_paths:
        msg = "적재할 옐로우 택시 Parquet 파일이 없습니다."
        raise TaxiDataLoadError(msg)
    try:
        _create_yellow_tripdata_table(connection, parquet_paths, table_name=table_name)
        row_count = table_row_count(connection, table_name)
        LOGGER.debug(
            "옐로우 택시 원천 적재 완료",
            extra={
                "table_name": table_name,
                "source_count": len(parquet_paths),
                "row_count": row_count,
            },
        )
        return row_count
    except duckdb.Error as exc:
        msg = f"옐로우 택시 Parquet 적재에 실패했습니다: table={table_name}"
        raise TaxiDataLoadError(msg) from exc


def _create_taxi_zones_table(
    connection: duckdb.DuckDBPyConnection,
    csv_path: str | Path,
    *,
    table_name: str = "raw.taxi_zones",
) -> None:
    ensure_schema(connection)
    qualified_table = qualify_table_name(table_name)
    connection.execute(
        f"""
        CREATE OR REPLACE TABLE {qualified_table} AS
        SELECT *
        FROM read_csv_auto(?)
        """,
        [str(csv_path)],
    )


def _create_yellow_tripdata_table(
    connection: duckdb.DuckDBPyConnection,
    parquet_paths: Sequence[str | Path],
    *,
    table_name: str = YELLOW_TRIPDATA_TABLE,
) -> None:
    ensure_schema(connection)
    qualified_table = qualify_table_name(table_name)
    source_paths = [str(path) for path in parquet_paths]
    connection.execute(
        f"""
        CREATE OR REPLACE TABLE {qualified_table} AS
        SELECT
{yellow_tripdata_source_projection()}
        FROM read_parquet(?, filename = true)
        """,
        [source_paths],
    )
