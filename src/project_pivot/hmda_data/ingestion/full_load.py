"""HMDA 원천 테이블 전체 적재."""

from __future__ import annotations

from collections.abc import Sequence
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
from project_pivot.hmda_data.sql import qualify_table_name


def load_hmda_loans(
    connection: duckdb.DuckDBPyConnection,
    source_paths: Sequence[str | Path],
    *,
    table_name: str = HMDA_LOANS_TABLE,
) -> int:
    """HMDA CSV/Parquet 파일을 raw.hmda_loans에 멱등 적재한다."""

    paths = _normalize_source_paths(source_paths)
    try:
        _create_hmda_loans_table(connection, paths, table_name=table_name)
        validate_required_columns(connection, table_name)
        row_count = table_row_count(connection, table_name)
        LOGGER.debug(
            "HMDA 원천 적재 완료",
            extra={
                "table_name": table_name,
                "source_count": len(paths),
                "row_count": row_count,
            },
        )
        return row_count
    except HMDADataLoadError:
        raise
    except duckdb.Error as exc:
        context = {
            "table_name": table_name,
            "source_paths": [str(path) for path in paths],
        }
        LOGGER.exception("HMDA 원천 적재 실패", extra=context)
        msg = f"HMDA 원천 데이터 적재에 실패했습니다: table={table_name}"
        raise HMDADataLoadError(msg, context=context) from exc


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


def _create_hmda_loans_table(
    connection: duckdb.DuckDBPyConnection,
    source_paths: Sequence[Path],
    *,
    table_name: str = HMDA_LOANS_TABLE,
) -> None:
    ensure_schema(connection)
    qualified_table = qualify_table_name(table_name)
    selects = [_source_select_sql(path) for path in source_paths]
    query = "\nUNION ALL BY NAME\n".join(selects)
    connection.execute(
        f"""
        CREATE OR REPLACE TABLE {qualified_table} AS
        {query}
        """,
        [path.as_posix() for path in source_paths],
    )


def _source_select_sql(path: Path) -> str:
    reader = _reader_sql(path)
    return f"""
        SELECT
            * EXCLUDE (filename),
            filename AS source_file,
            TRY_CAST(
                regexp_extract(
                    regexp_extract(filename, '[^/]+$', 0),
                    '(\\d{{4}})',
                    1
                ) AS INTEGER
            )
                AS source_year,
            current_timestamp AS ingested_at
        FROM {reader}
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
