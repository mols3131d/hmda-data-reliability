"""DuckDB로부터 완전한 HMDA 테이블 스키마 및 내용 상태를 생성한다."""

from __future__ import annotations

import duckdb
from pydantic import ValidationError

from hmda_reliability.data_platform.duckdb import DuckDBMetadataError, table_row_count
from hmda_reliability.data_platform.sql import qualify_table_name, quote_identifier
from hmda_reliability.hmda_data import partition_content_identity
from hmda_reliability.reliability.contracts import TableStateIdentity
from hmda_reliability.reliability.errors import TableStateIdentityError
from hmda_reliability.reliability.profiling.profile_snapshot_builder import (
    calculate_schema_hash,
)


def create_table_state_identity(
    connection: duckdb.DuckDBPyConnection,
    table_name: str,
) -> TableStateIdentity:
    """정확한 스키마와 완전한 연도별 내용 식별자를 반환한다.

    완전성 및 무결성 불변식:
    1. 단일 소스 연도 누락 방지: `source_year`가 NULL인 행이 존재하면 전체 상태에
       포함할 수 없으므로 `TableStateIdentityError`를 즉시 발생시킨다.
    2. 파티션 인구수 보존: 각 연도별 파티션 `PartitionContentIdentity`의 행 수 합계가
       테이블 전체 `table_row_count`와 정확히 일치해야 한다 (누락/중복 집계 검증).
    3. 정렬 결정론성: 연도별 파티션 식별자는 오름차순으로 정렬되어 반환된다.
    """

    try:
        row_count = table_row_count(connection, table_name)
        schema_hash = calculate_schema_hash(connection, table_name)
        year_rows = connection.execute(
            f"""
            SELECT {quote_identifier("source_year")}
            FROM {qualify_table_name(table_name)}
            GROUP BY {quote_identifier("source_year")}
            ORDER BY {quote_identifier("source_year")}
            """
        ).fetchall()
        if any(row[0] is None for row in year_rows):
            raise TableStateIdentityError(
                "source_year가 NULL인 row는 complete table state에 "
                f"포함할 수 없습니다: {table_name}"
            )
        partition_identities = tuple(
            partition_content_identity(
                connection,
                source_year=int(row[0]),
                table_name=table_name,
            )
            for row in year_rows
        )
        covered_row_count = sum(identity.row_count for identity in partition_identities)
        if covered_row_count != row_count:
            raise TableStateIdentityError(
                "source_year partition population이 table row_count를 "
                "완전히 덮지 않습니다: "
                f"table={table_name}, covered={covered_row_count}, total={row_count}"
            )
        return TableStateIdentity(
            table_name=table_name,
            schema_hash=schema_hash,
            row_count=row_count,
            partition_identities=partition_identities,
        )
    except TableStateIdentityError:
        raise
    except (duckdb.Error, DuckDBMetadataError, ValidationError, ValueError) as exc:
        msg = f"table state identity를 계산할 수 없습니다: table={table_name}"
        raise TableStateIdentityError(msg) from exc
