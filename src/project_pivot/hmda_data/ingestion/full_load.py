"""HMDA 원천 전체를 target Bronze table로 교체하는 full-load path."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import duckdb

from project_pivot.data_platform.duckdb import ensure_schema, table_row_count
from project_pivot.data_platform.sql import qualify_table_name
from project_pivot.hmda_data.errors import HMDADataLoadError
from project_pivot.hmda_data.ingestion._common import (
    _LOGGER,
    HMDA_LOANS_TABLE,
    validate_required_columns,
)
from project_pivot.hmda_data.ingestion._source_query import (
    source_union_sql,
    table_schema_name,
    validate_source_paths,
)


def load_hmda_loans(
    connection: duckdb.DuckDBPyConnection,
    source_paths: Sequence[str | Path],
    *,
    table_name: str = HMDA_LOANS_TABLE,
) -> int:
    """모든 source로 target table을 교체하고 최종 row count를 반환한다.

    Append가 아니라 ``CREATE OR REPLACE TABLE``을 사용하므로 같은 input의 재실행은
    중복 row를 만들지 않는다. DuckDB read/write 실패는 ``HMDADataLoadError``로
    변환하며 required-column validation은 별도 domain validation error로 노출한다.
    """

    paths = validate_source_paths(source_paths)
    try:
        _create_hmda_loans_table(connection, paths, table_name=table_name)
        validate_required_columns(connection, table_name)
        row_count = table_row_count(connection, table_name)
        _LOGGER.debug(
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
        _LOGGER.exception("HMDA 원천 적재 실패", extra=context)
        msg = f"HMDA 원천 데이터 적재에 실패했습니다: table={table_name}"
        raise HMDADataLoadError(msg, context=context) from exc


def _create_hmda_loans_table(
    connection: duckdb.DuckDBPyConnection,
    source_paths: Sequence[Path],
    *,
    table_name: str = HMDA_LOANS_TABLE,
) -> None:
    ensure_schema(connection, table_schema_name(table_name))
    qualified_table = qualify_table_name(table_name)
    query = source_union_sql(source_paths)
    connection.execute(
        f"""
        CREATE OR REPLACE TABLE {qualified_table} AS
        {query}
        """,
        [path.as_posix() for path in source_paths],
    )
