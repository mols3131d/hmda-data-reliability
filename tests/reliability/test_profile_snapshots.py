"""Profile snapshot 계산 테스트."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime

import duckdb

from project_pivot.reliability import (
    ProfileSnapshotRequest,
    calculate_schema_hash,
    create_profile_snapshot,
)
from project_pivot.taxi_data import DuckDBConnectionManager


def test_create_profile_snapshot_for_partition() -> None:
    """partition row count와 snapshot contract 생성을 검증한다."""
    observed_at = datetime(2026, 6, 10, 0, 0, tzinfo=UTC)
    with DuckDBConnectionManager() as connection:
        _create_profile_table(connection)

        snapshot = create_profile_snapshot(
            connection,
            ProfileSnapshotRequest(
                asset_name="raw.profile_test",
                table_name="raw.profile_test",
                partition_column="pickup_at",
                partition=date(2024, 1, 1),
                profile_columns=("total_amount", "passenger_count"),
                freshness_column="loaded_at",
                observed_at=observed_at,
            ),
        )

    assert snapshot.snapshot_id == "profile_raw_profile_test_2024_01_01"
    assert snapshot.asset_name == "raw.profile_test"
    assert snapshot.partition == "2024-01-01"
    assert snapshot.row_count == 2
    assert snapshot.schema_hash.startswith("sha256:")
    assert snapshot.metric_values["row_count"] == 2.0


def test_profile_snapshot_calculates_null_rate_freshness_and_json() -> None:
    """null rate, freshness, JSON 직렬화를 검증한다."""
    observed_at = datetime(2026, 6, 10, 0, 0, tzinfo=UTC)
    with DuckDBConnectionManager() as connection:
        _create_profile_table(connection)

        snapshot = create_profile_snapshot(
            connection,
            ProfileSnapshotRequest(
                asset_name="raw.profile_test",
                table_name="raw.profile_test",
                partition_column="pickup_at",
                partition=date(2024, 1, 1),
                profile_columns=("total_amount", "passenger_count"),
                freshness_column="loaded_at",
                observed_at=observed_at,
            ),
        )

    payload = json.loads(snapshot.model_dump_json())

    assert snapshot.null_rates == {
        "passenger_count": 0.0,
        "total_amount": 0.5,
    }
    assert snapshot.metric_values["total_amount.null_count"] == 1.0
    assert snapshot.freshness_at == datetime(2024, 1, 2, 9, 30, tzinfo=UTC)
    assert payload["row_count"] == 2
    assert payload["null_rates"]["total_amount"] == 0.5
    assert payload["freshness_at"] == "2024-01-02T09:30:00Z"


def test_schema_hash_is_deterministic_and_changes_with_schema() -> None:
    """schema hash 재현성과 schema 변경 감지를 검증한다."""
    with DuckDBConnectionManager() as connection:
        _create_profile_table(connection)

        first_hash = calculate_schema_hash(connection, "raw.profile_test")
        second_hash = calculate_schema_hash(connection, "raw.profile_test")
        connection.execute("ALTER TABLE raw.profile_test ADD COLUMN extra_note VARCHAR")
        changed_hash = calculate_schema_hash(connection, "raw.profile_test")

    assert first_hash == second_hash
    assert changed_hash != first_hash


def test_empty_partition_uses_zero_null_rates_and_observed_freshness() -> None:
    """빈 partition fallback metric을 검증한다."""
    observed_at = datetime(2026, 6, 10, 0, 0, tzinfo=UTC)
    with DuckDBConnectionManager() as connection:
        _create_profile_table(connection)

        snapshot = create_profile_snapshot(
            connection,
            ProfileSnapshotRequest(
                asset_name="raw.profile_test",
                table_name="raw.profile_test",
                partition_column="pickup_at",
                partition=date(2024, 1, 3),
                profile_columns=("total_amount",),
                freshness_column="loaded_at",
                observed_at=observed_at,
            ),
        )

    assert snapshot.row_count == 0
    assert snapshot.null_rates["total_amount"] == 0.0
    assert snapshot.freshness_at == observed_at
    assert snapshot.metric_values["freshness_used_fallback"] == 1.0


def _create_profile_table(connection: duckdb.DuckDBPyConnection) -> None:
    connection.execute("CREATE SCHEMA raw")
    connection.execute(
        """
        CREATE TABLE raw.profile_test (
            pickup_at TIMESTAMP,
            loaded_at TIMESTAMP,
            total_amount DOUBLE,
            passenger_count BIGINT
        )
        """
    )
    connection.execute(
        """
        INSERT INTO raw.profile_test VALUES
            (
                TIMESTAMP '2024-01-01 08:00:00',
                TIMESTAMP '2024-01-02 09:00:00',
                12.5,
                1
            ),
            (
                TIMESTAMP '2024-01-01 09:00:00',
                TIMESTAMP '2024-01-02 09:30:00',
                NULL,
                2
            ),
            (
                TIMESTAMP '2024-01-02 08:00:00',
                TIMESTAMP '2024-01-03 09:00:00',
                20.0,
                1
            )
        """
    )
