"""DuckDB table metadata evidence builder."""

from __future__ import annotations

import duckdb

from project_pivot.data_platform.duckdb import table_row_count
from project_pivot.data_platform.sql import qualify_table_name
from project_pivot.reliability.contracts import Evidence, EvidenceSource
from project_pivot.reliability.errors import TableMetadataEvidenceError
from project_pivot.reliability.metadata.request import TableMetadataEvidenceRequest
from project_pivot.reliability.profiling import calculate_schema_hash


class DuckDBTableMetadataEvidenceBuilder:
    """DuckDB table metadata를 Evidence contract로 변환한다."""

    def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
        self._connection = connection

    def build(self, request: TableMetadataEvidenceRequest) -> Evidence:
        """요청 table의 metadata evidence를 생성한다."""

        try:
            columns = _describe_table(self._connection, request.table_name)
            row_count = table_row_count(self._connection, request.table_name)
            schema_hash = calculate_schema_hash(self._connection, request.table_name)
        except duckdb.Error as exc:
            msg = (
                "table metadata evidence 생성에 실패했습니다: "
                f"table={request.table_name}, partition={request.partition}"
            )
            raise TableMetadataEvidenceError(msg) from exc

        return Evidence(
            evidence_id=_evidence_id(request),
            source=EvidenceSource.TABLE_METADATA,
            asset_name=request.asset_name,
            partition=request.partition,
            observed_at=request.observed_at,
            summary=f"{request.table_name} table metadata evidence",
            payload={
                "table_name": request.table_name,
                "schema_hash": schema_hash,
                "columns": columns,
                "row_count": row_count,
            },
        )


def create_table_metadata_evidence(
    connection: duckdb.DuckDBPyConnection,
    request: TableMetadataEvidenceRequest,
) -> Evidence:
    """DuckDB connection과 요청 모델로 table metadata Evidence를 생성한다."""

    return DuckDBTableMetadataEvidenceBuilder(connection).build(request)


def _describe_table(
    connection: duckdb.DuckDBPyConnection,
    table_name: str,
) -> list[dict[str, str]]:
    rows = connection.execute(f"DESCRIBE {qualify_table_name(table_name)}").fetchall()
    return [
        {
            "name": str(row[0]),
            "type": str(row[1]),
            "nullable": str(row[2]),
        }
        for row in rows
    ]


def _evidence_id(request: TableMetadataEvidenceRequest) -> str:
    normalized_asset = "".join(
        character if character.isalnum() else "_"
        for character in request.asset_name.lower()
    ).strip("_")
    normalized_partition = "".join(
        character if character.isalnum() else "_"
        for character in request.partition.lower()
    ).strip("_")
    return f"ev_table_metadata_{normalized_asset}_{normalized_partition}"
