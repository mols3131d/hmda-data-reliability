"""Build complete HMDA table schema/content state from DuckDB."""

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
    """Return exact schema and complete ``source_year`` content identity."""

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
