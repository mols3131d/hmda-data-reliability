"""Optimistic partition replacement를 위한 logical content identity."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import cast

import duckdb
from pydantic import BaseModel, ConfigDict, Field

from project_pivot.data_platform.sql import qualify_table_name, quote_identifier
from project_pivot.hmda_data.ingestion._common import HMDA_LOANS_TABLE

_IDENTITY_VERSION = "sha256-v1"
# 동일 logical content를 재적재한 시각 차이로 stale 처리하지 않도록 제외한다.
_VOLATILE_COLUMNS = frozenset({"ingested_at"})
_EMPTY_DIGEST = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


class PartitionContentIdentity(BaseModel):
    """Row order와 ingestion time에 독립적인 HMDA partition content identity.

    Logical values와 duplicate multiplicity는 identity에 포함된다.
    """

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
    """지정 partition의 stable logical identity를 계산한다.

    Target table이 아직 없으면 empty identity를 반환한다. Row order와 ``ingested_at``은
    digest에 영향을 주지 않지만 logical value 변경과 duplicate row 증감은 구분한다.
    """

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


def partition_max_ingested_at(
    connection: duckdb.DuckDBPyConnection,
    *,
    source_year: int,
    source_file: str | None = None,
    table_name: str = HMDA_LOANS_TABLE,
) -> datetime | None:
    """Return the exact maximum Bronze ingestion timestamp for a partition."""

    source_file_filter = "" if source_file is None else "AND source_file_name = ?"
    params: list[object] = [source_year]
    if source_file is not None:
        params.append(source_file)
    try:
        row = connection.execute(
            f"""
            SELECT max(ingested_at)
            FROM {qualify_table_name(table_name)}
            WHERE source_year = ?
            {source_file_filter}
            """,
            params,
        ).fetchone()
    except duckdb.CatalogException:
        return None
    if row is None or row[0] is None:
        return None
    value = cast(datetime, row[0])
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
