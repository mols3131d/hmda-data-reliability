"""HMDA 연도/파일 파티션 적재."""

from __future__ import annotations

from collections.abc import Sequence
from contextlib import suppress
from pathlib import Path

import duckdb

from project_pivot.data_platform.duckdb import ensure_schema, table_row_count
from project_pivot.data_platform.sql import qualify_table_name, quote_identifier
from project_pivot.hmda_data.errors import HMDADataLoadError
from project_pivot.hmda_data.ingestion._common import (
    _LOGGER,
    HMDA_LOANS_TABLE,
    validate_required_columns,
)
from project_pivot.hmda_data.ingestion._source_query import (
    normalize_source_paths,
    source_union_sql,
)

_STAGING_TABLE = "__hmda_loans_partition_stage"


def load_hmda_loans_partition(
    connection: duckdb.DuckDBPyConnection,
    source_paths: Sequence[str | Path],
    source_year: int,
    *,
    source_file: str | None = None,
    table_name: str = HMDA_LOANS_TABLE,
) -> int:
    """HMDA source_year/source_file 파티션을 멱등 적재한다."""

    paths = normalize_source_paths(source_paths)
    try:
        _ensure_hmda_loans_table(connection, paths, table_name)
    except duckdb.Error as exc:
        context = {
            "table_name": table_name,
            "source_year": source_year,
            "source_file": source_file,
        }
        msg = "HMDA 파티션 테이블 초기화에 실패했습니다."
        raise HMDADataLoadError(msg, context=context) from exc

    _overwrite_hmda_loans_partition(
        connection=connection,
        source_paths=paths,
        source_year=source_year,
        source_file=source_file,
        table_name=table_name,
    )
    row_count = _partition_row_count(
        connection,
        table_name=table_name,
        source_year=source_year,
        source_file=source_file,
    )
    _LOGGER.debug(
        "HMDA 파티션 적재 완료",
        extra={
            "table_name": table_name,
            "source_year": source_year,
            "source_file": source_file,
            "row_count": row_count,
        },
    )
    return row_count


def _ensure_hmda_loans_table(
    connection: duckdb.DuckDBPyConnection,
    source_paths: Sequence[Path],
    table_name: str,
) -> None:
    """파티션 적재 대상 테이블을 빈 raw 스키마로 보장한다."""

    ensure_schema(connection)
    qualified_table = qualify_table_name(table_name)
    query = source_union_sql(source_paths)
    connection.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {qualified_table} AS
        SELECT *
        FROM ({query})
        WHERE false
        """,
        [path.as_posix() for path in source_paths],
    )


def _overwrite_hmda_loans_partition(
    *,
    connection: duckdb.DuckDBPyConnection,
    source_paths: Sequence[Path],
    source_year: int,
    source_file: str | None,
    table_name: str,
) -> None:
    """source_year/source_file 파티션을 staging 테이블 기준으로 덮어쓴다."""

    transaction_started = False
    try:
        _create_staging_table(
            connection=connection,
            source_paths=source_paths,
            source_year=source_year,
            source_file=source_file,
        )
        _validate_staging_rows(
            connection=connection,
            table_name=table_name,
            source_year=source_year,
            source_file=source_file,
        )
        connection.execute("BEGIN TRANSACTION")
        transaction_started = True
        _replace_partition_rows(
            connection=connection,
            table_name=table_name,
            source_year=source_year,
            source_file=source_file,
        )
        connection.execute("COMMIT")
        transaction_started = False
    except duckdb.Error as exc:
        if transaction_started:
            connection.execute("ROLLBACK")
        context = _partition_context(table_name, source_year, source_file)
        msg = "HMDA 파티션 적재에 실패했습니다."
        raise HMDADataLoadError(msg, context=context) from exc
    finally:
        with suppress(duckdb.Error):
            connection.execute(
                f"DROP TABLE IF EXISTS {quote_identifier(_STAGING_TABLE)}"
            )


def _partition_row_count(
    connection: duckdb.DuckDBPyConnection,
    *,
    table_name: str,
    source_year: int,
    source_file: str | None,
) -> int:
    """적재된 source_year/source_file 파티션 행 수를 반환한다."""

    result = connection.execute(
        f"""
        SELECT count(*)
        FROM {qualify_table_name(table_name)}
        WHERE source_year = ?
        {_source_file_filter_sql(source_file)}
        """,
        [source_year, *_source_file_params(source_file)],
    ).fetchone()
    if result is None:
        context = _partition_context(table_name, source_year, source_file)
        msg = "HMDA 파티션 행 수를 조회할 수 없습니다."
        raise HMDADataLoadError(msg, context=context)
    return int(result[0])


def _create_staging_table(
    *,
    connection: duckdb.DuckDBPyConnection,
    source_paths: Sequence[Path],
    source_year: int,
    source_file: str | None,
) -> None:
    connection.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE {quote_identifier(_STAGING_TABLE)} AS
        SELECT *
        FROM ({source_union_sql(source_paths)})
        WHERE source_year = ?
        {_source_file_filter_sql(source_file)}
        """,
        [
            *map(Path.as_posix, source_paths),
            source_year,
            *_source_file_params(source_file),
        ],
    )


def _validate_staging_rows(
    *,
    connection: duckdb.DuckDBPyConnection,
    table_name: str,
    source_year: int,
    source_file: str | None,
) -> None:
    validate_required_columns(connection, _STAGING_TABLE)
    source_row_count = table_row_count(connection, _STAGING_TABLE)
    if source_row_count == 0:
        context = _partition_context(table_name, source_year, source_file)
        msg = "HMDA 소스 파티션에 적재할 행이 없습니다."
        raise HMDADataLoadError(msg, context=context)


def _replace_partition_rows(
    *,
    connection: duckdb.DuckDBPyConnection,
    table_name: str,
    source_year: int,
    source_file: str | None,
) -> None:
    connection.execute(
        f"""
        DELETE FROM {qualify_table_name(table_name)}
        WHERE source_year = ?
        {_source_file_filter_sql(source_file)}
        """,
        [source_year, *_source_file_params(source_file)],
    )
    connection.execute(
        f"""
        INSERT INTO {qualify_table_name(table_name)}
        SELECT *
        FROM {quote_identifier(_STAGING_TABLE)}
        """,
    )


def _source_file_filter_sql(source_file: str | None) -> str:
    if source_file is None:
        return ""
    return "AND source_file_name = ?"


def _source_file_params(source_file: str | None) -> list[str]:
    return [] if source_file is None else [source_file]


def _partition_context(
    table_name: str,
    source_year: int,
    source_file: str | None,
) -> dict[str, object]:
    return {
        "table_name": table_name,
        "source_year": source_year,
        "source_file": source_file,
    }
