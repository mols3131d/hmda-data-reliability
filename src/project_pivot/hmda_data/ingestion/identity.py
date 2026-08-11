"""HMDA partition content identity."""

from __future__ import annotations

from typing import cast

import duckdb
from pydantic import BaseModel, ConfigDict, Field

from project_pivot.data_platform.sql import qualify_table_name, quote_identifier
from project_pivot.hmda_data.ingestion._common import HMDA_LOANS_TABLE

_IDENTITY_VERSION = "sha256-v1"
_VOLATILE_COLUMNS = frozenset({"ingested_at"})
_EMPTY_DIGEST = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


class PartitionContentIdentity(BaseModel):
    """Stable identity for one HMDA table partition row multiset."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    version: str = _IDENTITY_VERSION
    table_name: str
    source_year: int
    source_file: str | None = None
    row_count: int = Field(ge=0)
    digest: str


def partition_content_identity(
    connection: duckdb.DuckDBPyConnection,
    *,
    source_year: int,
    source_file: str | None = None,
    table_name: str = HMDA_LOANS_TABLE,
) -> PartitionContentIdentity:
    """Calculate an order-independent identity that preserves duplicate rows."""

    try:
        described_columns = connection.execute(
            f"DESCRIBE {qualify_table_name(table_name)}"
        ).fetchall()
    except duckdb.CatalogException:
        return PartitionContentIdentity(
            table_name=table_name,
            source_year=source_year,
            source_file=source_file,
            row_count=0,
            digest=f"{_IDENTITY_VERSION}:{_EMPTY_DIGEST}",
        )
    columns = [
        str(row[0]) for row in described_columns if str(row[0]) not in _VOLATILE_COLUMNS
    ]
    packed_columns = ", ".join(
        f"{quote_identifier(column)} := {quote_identifier(column)}"
        for column in columns
    )
    source_file_filter = "" if source_file is None else "AND source_file_name = ?"
    params: list[object] = [source_year]
    if source_file is not None:
        params.append(source_file)
    row = connection.execute(
        f"""
        WITH scoped AS (
            SELECT sha256(to_json(struct_pack({packed_columns}))) AS row_digest
            FROM {qualify_table_name(table_name)}
            WHERE source_year = ?
            {source_file_filter}
        )
        SELECT
            count(*),
            sha256(coalesce(string_agg(row_digest, '' ORDER BY row_digest), ''))
        FROM scoped
        """,
        params,
    ).fetchone()
    if row is None:
        raise RuntimeError("HMDA partition content identity를 계산할 수 없습니다.")
    return PartitionContentIdentity(
        table_name=table_name,
        source_year=source_year,
        source_file=source_file,
        row_count=int(cast(int, row[0])),
        digest=f"{_IDENTITY_VERSION}:{cast(str, row[1])}",
    )
