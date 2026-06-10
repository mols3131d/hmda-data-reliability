"""Table metadata evidence 테스트."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from project_pivot.reliability import (
    TableMetadataEvidenceError,
    TableMetadataEvidenceRequest,
    create_table_metadata_evidence,
)
from project_pivot.taxi_data import DuckDBConnectionManager


def test_create_table_metadata_evidence_contains_schema_and_row_count() -> None:
    """schema hash, columns, row_count payload를 검증한다."""
    observed_at = datetime(2026, 6, 10, 0, 0, tzinfo=UTC)

    with DuckDBConnectionManager() as connection:
        connection.execute("CREATE SCHEMA raw")
        connection.execute(
            """
            CREATE TABLE raw.metadata_test (
                pickup_date DATE,
                trip_count BIGINT
            )
            """
        )
        connection.execute(
            "INSERT INTO raw.metadata_test VALUES (DATE '2024-01-01', 10)"
        )

        evidence = create_table_metadata_evidence(
            connection,
            TableMetadataEvidenceRequest(
                asset_name="raw.metadata_test",
                table_name="raw.metadata_test",
                observed_at=observed_at,
            ),
        )

    assert evidence.evidence_id == "ev_table_metadata_raw_metadata_test_table"
    assert evidence.source == "table_metadata"
    assert evidence.asset_name == "raw.metadata_test"
    assert evidence.partition == "table"
    assert evidence.observed_at == observed_at
    assert evidence.payload["row_count"] == 1
    assert str(evidence.payload["schema_hash"]).startswith("sha256:")
    assert evidence.payload["columns"] == [
        {"name": "pickup_date", "type": "DATE", "nullable": "YES"},
        {"name": "trip_count", "type": "BIGINT", "nullable": "YES"},
    ]


def test_table_metadata_evidence_wraps_duckdb_errors() -> None:
    """없는 table 조회 실패를 도메인 예외로 변환한다."""
    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(TableMetadataEvidenceError, match="table metadata evidence"),
    ):
        create_table_metadata_evidence(
            connection,
            TableMetadataEvidenceRequest(
                asset_name="raw.missing",
                table_name="raw.missing",
            ),
        )
