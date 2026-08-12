"""HMDA Bronze partition row의 atomic compare-and-replace 적재."""

from __future__ import annotations

from collections.abc import Sequence
from contextlib import suppress
from pathlib import Path

import duckdb

from project_pivot.data_platform.duckdb import ensure_schema, table_row_count
from project_pivot.data_platform.sql import qualify_table_name, quote_identifier
from project_pivot.hmda_data.errors import HMDADataLoadError, HMDAStalePartitionError
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
from project_pivot.hmda_data.ingestion.identity import (
    PartitionContentIdentity,
    partition_content_identity,
)

_STAGING_TABLE = "__hmda_loans_partition_stage"


def load_hmda_loans_partition(
    connection: duckdb.DuckDBPyConnection,
    source_paths: Sequence[str | Path],
    source_year: int,
    *,
    source_file: str | None = None,
    table_name: str = HMDA_LOANS_TABLE,
    expected_identity: PartitionContentIdentity | None = None,
    preserve_source_metadata: bool = False,
) -> int:
    """한 ``source_year``/optional file scope를 교체하고 최종 row count를 반환한다.

    Target schema와 빈 table은 필요하면 staging validation 전에 생성된다. 기존 partition
    row는 staging의 required columns와 non-empty 조건을 통과한 뒤에만 교체된다.
    ``expected_identity``가 있으면 현재 identity 비교와 delete/insert를 같은 transaction에서
    수행하며 mismatch 시 기존 partition row는 변경하지 않는다.
    ``preserve_source_metadata=True``이면 input의 source tracking fields를 재계산하지 않는다.
    """

    paths = validate_source_paths(source_paths)
    try:
        _ensure_hmda_loans_table(
            connection,
            paths,
            table_name,
            preserve_source_metadata=preserve_source_metadata,
        )
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
        expected_identity=expected_identity,
        preserve_source_metadata=preserve_source_metadata,
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
    *,
    preserve_source_metadata: bool,
) -> None:
    """Source shape를 사용해 비어 있는 target table과 schema를 보장한다."""

    ensure_schema(connection, table_schema_name(table_name))
    qualified_table = qualify_table_name(table_name)
    query = source_union_sql(
        source_paths,
        preserve_source_metadata=preserve_source_metadata,
    )
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
    expected_identity: PartitionContentIdentity | None,
    preserve_source_metadata: bool,
) -> None:
    """Source scope를 staging에서 검증한 뒤 target partition row를 교체한다."""

    try:
        _create_staging_table(
            connection=connection,
            source_paths=source_paths,
            source_year=source_year,
            source_file=source_file,
            preserve_source_metadata=preserve_source_metadata,
        )
        _validate_staging_rows(
            connection=connection,
            table_name=table_name,
            source_year=source_year,
            source_file=source_file,
        )
        _replace_partition_in_transaction(
            connection=connection,
            table_name=table_name,
            source_year=source_year,
            source_file=source_file,
            expected_identity=expected_identity,
        )
    except HMDAStalePartitionError:
        raise
    except duckdb.Error as exc:
        context = _partition_context(table_name, source_year, source_file)
        msg = "HMDA 파티션 적재에 실패했습니다."
        raise HMDADataLoadError(msg, context=context) from exc
    finally:
        # 임시 테이블 정리 실패가 원래 적재 결과나 예외를 덮지 않게 한다.
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

    source_file_filter, source_file_params = _source_file_filter(source_file)
    result = connection.execute(
        f"""
        SELECT count(*)
        FROM {qualify_table_name(table_name)}
        WHERE source_year = ?
        {source_file_filter}
        """,
        [source_year, *source_file_params],
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
    preserve_source_metadata: bool,
) -> None:
    source_file_filter, source_file_params = _source_file_filter(source_file)
    source_query = source_union_sql(
        source_paths,
        preserve_source_metadata=preserve_source_metadata,
    )
    connection.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE {quote_identifier(_STAGING_TABLE)} AS
        SELECT *
        FROM ({source_query})
        WHERE source_year = ?
        {source_file_filter}
        """,
        [
            *map(Path.as_posix, source_paths),
            source_year,
            *source_file_params,
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


def _replace_partition_in_transaction(
    *,
    connection: duckdb.DuckDBPyConnection,
    table_name: str,
    source_year: int,
    source_file: str | None,
    expected_identity: PartitionContentIdentity | None,
) -> None:
    """Expected identity 확인과 partition row delete/insert를 하나의 transaction으로 묶는다."""

    connection.execute("BEGIN TRANSACTION")
    try:
        if expected_identity is not None:
            actual_identity = partition_content_identity(
                connection,
                table_name=table_name,
                source_year=source_year,
                source_file=source_file,
            )
            if actual_identity != expected_identity:
                context = {
                    **_partition_context(table_name, source_year, source_file),
                    "expected_identity": expected_identity.model_dump(),
                    "actual_identity": actual_identity.model_dump(),
                }
                raise HMDAStalePartitionError(
                    "HMDA target partition이 stale state입니다.", context=context
                )
        _replace_partition_rows(
            connection=connection,
            table_name=table_name,
            source_year=source_year,
            source_file=source_file,
        )
        connection.execute("COMMIT")
    except (HMDAStalePartitionError, duckdb.Error):
        connection.execute("ROLLBACK")
        raise


def _replace_partition_rows(
    *,
    connection: duckdb.DuckDBPyConnection,
    table_name: str,
    source_year: int,
    source_file: str | None,
) -> None:
    source_file_filter, source_file_params = _source_file_filter(source_file)
    connection.execute(
        f"""
        DELETE FROM {qualify_table_name(table_name)}
        WHERE source_year = ?
        {source_file_filter}
        """,
        [source_year, *source_file_params],
    )
    connection.execute(
        f"""
        INSERT INTO {qualify_table_name(table_name)}
        SELECT *
        FROM {quote_identifier(_STAGING_TABLE)}
        """,
    )


def _source_file_filter(source_file: str | None) -> tuple[str, list[str]]:
    """선택적 source_file 조건과 대응하는 바인딩 값을 함께 반환한다."""

    if source_file is None:
        return "", []
    return "AND source_file_name = ?", [source_file]


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
