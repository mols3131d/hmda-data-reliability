"""DuckDB schema와 table metadata 헬퍼."""

import duckdb

from project_pivot.shared.sql import qualify_table_name, quote_identifier


class DuckDBMetadataError(Exception):
    """DuckDB metadata 조회 실패를 나타낸다."""


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
        raise DuckDBMetadataError(msg)
    return int(result[0])


def table_columns(
    connection: duckdb.DuckDBPyConnection,
    table_name: str,
) -> set[str]:
    rows = connection.execute(f"DESCRIBE {qualify_table_name(table_name)}").fetchall()
    return {str(row[0]) for row in rows}
