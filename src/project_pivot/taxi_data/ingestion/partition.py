"""Taxi 일자 파티션 적재."""

from __future__ import annotations

from collections.abc import Sequence
from contextlib import suppress
from datetime import date, datetime
from pathlib import Path

import duckdb

from project_pivot.taxi_data.errors import TaxiDataLoadError
from project_pivot.taxi_data.ingestion.common import (
    LOGGER,
    YELLOW_TRIPDATA_TABLE,
    YELLOW_TRIPDATA_TIMESTAMP_COLUMN,
    ensure_schema,
    table_row_count,
    yellow_tripdata_source_projection,
)
from project_pivot.taxi_data.sql import qualify_table_name, quote_identifier


def load_yellow_tripdata_partition(
    connection: duckdb.DuckDBPyConnection,
    parquet_paths: Sequence[str | Path],
    partition_date: str | date,
    *,
    table_name: str = YELLOW_TRIPDATA_TABLE,
) -> int:
    """픽업 일자 파티션 하나를 raw.yellow_tripdata에 멱등 적재한다."""

    source_paths = _source_paths_parameter(parquet_paths)
    target_date = _parse_partition_date(partition_date)
    try:
        _ensure_yellow_tripdata_table(connection, source_paths, table_name)
    except duckdb.Error as exc:
        msg = (
            "옐로우 택시 파티션 테이블 초기화에 실패했습니다: "
            f"table={table_name}, partition_date={target_date.isoformat()}"
        )
        raise TaxiDataLoadError(msg) from exc
    _overwrite_yellow_tripdata_partition(
        connection=connection,
        source_paths=source_paths,
        partition_date=target_date,
        table_name=table_name,
    )
    row_count = _partition_row_count(
        connection,
        table_name=table_name,
        partition_date=target_date,
    )
    LOGGER.debug(
        "옐로우 택시 파티션 적재 완료",
        extra={
            "table_name": table_name,
            "partition_date": target_date.isoformat(),
            "row_count": row_count,
        },
    )
    return row_count


def _source_paths_parameter(parquet_paths: Sequence[str | Path]) -> str | list[str]:
    if not parquet_paths:
        msg = "적재할 옐로우 택시 Parquet 파일이 없습니다."
        raise TaxiDataLoadError(msg)
    paths = [str(path) for path in parquet_paths]
    if len(paths) == 1:
        return paths[0]
    return paths


def _parse_partition_date(partition_date: str | date) -> date:
    if isinstance(partition_date, datetime):
        return partition_date.date()
    if isinstance(partition_date, date):
        return partition_date
    try:
        return date.fromisoformat(partition_date)
    except ValueError as exc:
        msg = f"partition_date는 YYYY-MM-DD 형식이어야 합니다: {partition_date}"
        raise TaxiDataLoadError(msg) from exc


def _ensure_yellow_tripdata_table(
    connection: duckdb.DuckDBPyConnection,
    source_paths: str | list[str],
    table_name: str,
) -> None:
    ensure_schema(connection)
    qualified_table = qualify_table_name(table_name)
    connection.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {qualified_table} AS
        SELECT
{yellow_tripdata_source_projection()}
        FROM read_parquet(?, filename = true)
        WHERE false
        """,
        [source_paths],
    )


def _overwrite_yellow_tripdata_partition(
    *,
    connection: duckdb.DuckDBPyConnection,
    source_paths: str | list[str],
    partition_date: date,
    table_name: str,
) -> None:
    qualified_table = qualify_table_name(table_name)
    pickup_date = f"CAST({quote_identifier(YELLOW_TRIPDATA_TIMESTAMP_COLUMN)} AS DATE)"
    staging_table = "__yellow_tripdata_partition_stage"
    transaction_started = False
    try:
        connection.execute(
            f"""
            CREATE OR REPLACE TEMP TABLE {quote_identifier(staging_table)} AS
            SELECT
{yellow_tripdata_source_projection()}
            FROM read_parquet(?, filename = true)
            WHERE {pickup_date} = ?
            """,
            [source_paths, partition_date],
        )
        source_row_count = table_row_count(connection, staging_table)
        if source_row_count == 0:
            msg = (
                "소스 파티션에 적재할 행이 없습니다: "
                f"table={table_name}, partition_date={partition_date.isoformat()}"
            )
            raise TaxiDataLoadError(msg)

        connection.execute("BEGIN TRANSACTION")
        transaction_started = True
        connection.execute(
            f"""
            DELETE FROM {qualified_table}
            WHERE {pickup_date} = ?
            """,
            [partition_date],
        )
        connection.execute(
            f"""
            INSERT INTO {qualified_table}
            SELECT *
            FROM {quote_identifier(staging_table)}
            """,
        )
        connection.execute("COMMIT")
    except duckdb.Error as exc:
        if transaction_started:
            connection.execute("ROLLBACK")
        msg = (
            "옐로우 택시 파티션 적재에 실패했습니다: "
            f"table={table_name}, partition_date={partition_date.isoformat()}"
        )
        raise TaxiDataLoadError(msg) from exc
    finally:
        with suppress(duckdb.Error):
            connection.execute(
                f"DROP TABLE IF EXISTS {quote_identifier(staging_table)}"
            )


def _partition_row_count(
    connection: duckdb.DuckDBPyConnection,
    *,
    table_name: str,
    partition_date: date,
) -> int:
    pickup_date = f"CAST({quote_identifier(YELLOW_TRIPDATA_TIMESTAMP_COLUMN)} AS DATE)"
    result = connection.execute(
        f"""
        SELECT count(*)
        FROM {qualify_table_name(table_name)}
        WHERE {pickup_date} = ?
        """,
        [partition_date],
    ).fetchone()
    if result is None:
        msg = (
            "파티션 행 수를 조회할 수 없습니다: "
            f"table={table_name}, partition_date={partition_date.isoformat()}"
        )
        raise TaxiDataLoadError(msg)
    return int(result[0])
