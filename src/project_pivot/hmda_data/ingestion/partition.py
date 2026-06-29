"""HMDA 연도/파일 파티션 적재."""

from __future__ import annotations

from collections.abc import Sequence
from contextlib import suppress
from pathlib import Path

import duckdb

from project_pivot.hmda_data.errors import HMDADataLoadError
from project_pivot.hmda_data.ingestion.common import (
    HMDA_LOANS_TABLE,
    LOGGER,
    ensure_schema,
    table_row_count,
    validate_required_columns,
)
from project_pivot.hmda_data.sql import qualify_table_name, quote_identifier


def load_hmda_loans_partition(
    connection: duckdb.DuckDBPyConnection,
    source_paths: Sequence[str | Path],
    source_year: int,
    *,
    source_file: str | None = None,
    table_name: str = HMDA_LOANS_TABLE,
) -> int:
    """HMDA source_year/source_file 파티션을 멱등 적재한다."""

    paths = _normalize_source_paths(source_paths)
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
    LOGGER.debug(
        "HMDA 파티션 적재 완료",
        extra={
            "table_name": table_name,
            "source_year": source_year,
            "source_file": source_file,
            "row_count": row_count,
        },
    )
    return row_count


def _normalize_source_paths(source_paths: Sequence[str | Path]) -> list[Path]:
    if not source_paths:
        msg = "적재할 HMDA CSV 또는 Parquet 파일이 없습니다."
        raise HMDADataLoadError(msg)

    paths = [Path(path) for path in source_paths]
    unsupported_paths = [
        path.as_posix()
        for path in paths
        if path.suffix.lower() not in {".csv", ".parquet"}
    ]
    if unsupported_paths:
        msg = "지원하지 않는 HMDA 원천 파일 형식입니다."
        raise HMDADataLoadError(msg, context={"unsupported_paths": unsupported_paths})
    return paths


def _ensure_hmda_loans_table(
    connection: duckdb.DuckDBPyConnection,
    source_paths: Sequence[Path],
    table_name: str,
) -> None:
    ensure_schema(connection)
    qualified_table = qualify_table_name(table_name)
    query = _source_union_sql(source_paths)
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
    qualified_table = qualify_table_name(table_name)
    staging_table = "__hmda_loans_partition_stage"
    source_filter = _source_filter_sql(source_file)
    delete_filter = _delete_filter_sql(source_file)
    transaction_started = False
    try:
        connection.execute(
            f"""
            CREATE OR REPLACE TEMP TABLE {quote_identifier(staging_table)} AS
            SELECT *
            FROM ({_source_union_sql(source_paths)})
            WHERE source_year = ?
            {source_filter}
            """,
            [
                *map(Path.as_posix, source_paths),
                source_year,
                *filter(None, [source_file]),
            ],
        )
        validate_required_columns(connection, staging_table)
        source_row_count = table_row_count(connection, staging_table)
        if source_row_count == 0:
            context = {
                "table_name": table_name,
                "source_year": source_year,
                "source_file": source_file,
            }
            msg = "HMDA 소스 파티션에 적재할 행이 없습니다."
            raise HMDADataLoadError(msg, context=context)

        connection.execute("BEGIN TRANSACTION")
        transaction_started = True
        connection.execute(
            f"""
            DELETE FROM {qualified_table}
            WHERE source_year = ?
            {delete_filter}
            """,
            [source_year, *filter(None, [source_file])],
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
        context = {
            "table_name": table_name,
            "source_year": source_year,
            "source_file": source_file,
        }
        msg = "HMDA 파티션 적재에 실패했습니다."
        raise HMDADataLoadError(msg, context=context) from exc
    finally:
        with suppress(duckdb.Error):
            connection.execute(
                f"DROP TABLE IF EXISTS {quote_identifier(staging_table)}"
            )


def _partition_row_count(
    connection: duckdb.DuckDBPyConnection,
    *,
    table_name: str,
    source_year: int,
    source_file: str | None,
) -> int:
    result = connection.execute(
        f"""
        SELECT count(*)
        FROM {qualify_table_name(table_name)}
        WHERE source_year = ?
        {_delete_filter_sql(source_file)}
        """,
        [source_year, *filter(None, [source_file])],
    ).fetchone()
    if result is None:
        context = {
            "table_name": table_name,
            "source_year": source_year,
            "source_file": source_file,
        }
        msg = "HMDA 파티션 행 수를 조회할 수 없습니다."
        raise HMDADataLoadError(msg, context=context)
    return int(result[0])


def _source_union_sql(source_paths: Sequence[Path]) -> str:
    return "\nUNION ALL BY NAME\n".join(
        _source_select_sql(path) for path in source_paths
    )


def _source_select_sql(path: Path) -> str:
    return f"""
        SELECT
            * EXCLUDE (filename),
            filename AS source_file,
            regexp_extract(filename, '[^/]+$', 0) AS source_file_name,
            TRY_CAST(
                regexp_extract(
                    regexp_extract(filename, '[^/]+$', 0),
                    '(\\d{{4}})',
                    1
                ) AS INTEGER
            )
                AS source_year,
            current_timestamp AS ingested_at
        FROM {_reader_sql(path)}
    """


def _reader_sql(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return """
            read_csv_auto(
                ?,
                header = true,
                nullstr = ['NA', ''],
                sample_size = 200000,
                ignore_errors = true,
                filename = true
            )
        """
    if suffix == ".parquet":
        return "read_parquet(?, filename = true)"
    msg = f"지원하지 않는 HMDA 원천 파일 형식입니다: {path}"
    raise HMDADataLoadError(msg, context={"source_path": path.as_posix()})


def _source_filter_sql(source_file: str | None) -> str:
    if source_file is None:
        return ""
    return "AND source_file_name = ?"


def _delete_filter_sql(source_file: str | None) -> str:
    if source_file is None:
        return ""
    return "AND source_file_name = ?"
