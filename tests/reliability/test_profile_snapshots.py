"""Profile snapshot 계산 테스트."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime

import duckdb
import pytest

from hmda_reliability.data_platform.duckdb import DuckDBConnectionManager
from hmda_reliability.reliability import (
    FreshnessMeasurementStatus,
    ProfileSnapshotError,
    ProfileSnapshotRequest,
    calculate_schema_hash,
    create_profile_snapshot,
)

pytestmark = pytest.mark.component


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
                partition_column="partition_at",
                partition=date(2024, 1, 1),
                profile_columns=("loan_amount", "passenger_count"),
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
                partition_column="partition_at",
                partition=date(2024, 1, 1),
                profile_columns=("loan_amount", "passenger_count"),
                freshness_column="loaded_at",
                observed_at=observed_at,
            ),
        )

    payload = json.loads(snapshot.model_dump_json())

    assert snapshot.null_rates == {
        "passenger_count": 0.0,
        "loan_amount": 0.5,
    }
    assert snapshot.metric_values["loan_amount.null_count"] == 1.0
    assert snapshot.freshness_at == datetime(2024, 1, 2, 9, 30, tzinfo=UTC)
    assert snapshot.freshness_status is FreshnessMeasurementStatus.MEASURED
    assert payload["row_count"] == 2
    assert payload["null_rates"]["loan_amount"] == 0.5
    assert payload["freshness_at"] == "2024-01-02T09:30:00Z"
    assert payload["freshness_status"] == "measured"


@pytest.mark.parametrize(
    "schema_change",
    [
        "ADD COLUMN extra_note VARCHAR",
        "RENAME COLUMN loan_amount TO loan_value",
        "ALTER COLUMN loan_amount TYPE DECIMAL(12, 2)",
    ],
    ids=["added-column", "renamed-column", "changed-type"],
)
def test_schema_hash_is_deterministic_and_changes_with_schema(
    schema_change: str,
) -> None:
    """schema hash 재현성과 schema 변경 감지를 검증한다."""
    with DuckDBConnectionManager() as connection:
        _create_profile_table(connection)

        first_hash = calculate_schema_hash(connection, "raw.profile_test")
        second_hash = calculate_schema_hash(connection, "raw.profile_test")
        connection.execute(f"ALTER TABLE raw.profile_test {schema_change}")
        changed_hash = calculate_schema_hash(connection, "raw.profile_test")

    assert first_hash == second_hash
    assert changed_hash != first_hash


@pytest.mark.parametrize(
    "row_change",
    [
        "UPDATE raw.profile_test SET loan_amount = 42.0 WHERE loan_amount = 12.5",
        "INSERT INTO raw.profile_test VALUES "
        "(TIMESTAMP '2024-01-01 10:00:00', TIMESTAMP '2024-01-02 10:00:00', 25.0, 3)",
    ],
    ids=["updated-value", "inserted-row"],
)
def test_schema_hash_is_unchanged_by_row_changes(row_change: str) -> None:
    with DuckDBConnectionManager() as connection:
        _create_profile_table(connection)
        rows_before = connection.execute(
            "SELECT * FROM raw.profile_test ORDER BY partition_at"
        ).fetchall()
        hash_before = calculate_schema_hash(connection, "raw.profile_test")

        connection.execute(row_change)

        rows_after = connection.execute(
            "SELECT * FROM raw.profile_test ORDER BY partition_at"
        ).fetchall()
        hash_after = calculate_schema_hash(connection, "raw.profile_test")

    assert rows_after != rows_before
    assert hash_after == hash_before


@pytest.mark.parametrize(
    ("partition_day", "freshness_column", "expected_rows"),
    [(3, "loaded_at", 0), (1, "loaded_at", 2), (1, None, 2)],
    ids=["empty-partition", "all-null-timestamps", "unconfigured-column"],
)
def test_unmeasurable_profile_reports_unavailable_freshness(
    partition_day: int, freshness_column: str | None, expected_rows: int
) -> None:
    """측정할 수 없는 시각을 observed_at으로 대체하지 않는다."""
    observed_at = datetime(2026, 6, 10, 0, 0, tzinfo=UTC)
    with DuckDBConnectionManager() as connection:
        _create_profile_table(connection)
        if freshness_column is not None:
            connection.execute(
                "UPDATE raw.profile_test SET loaded_at = NULL "
                "WHERE CAST(partition_at AS DATE) = ?",
                [date(2024, 1, partition_day)],
            )

        snapshot = create_profile_snapshot(
            connection,
            ProfileSnapshotRequest(
                asset_name="raw.profile_test",
                table_name="raw.profile_test",
                partition_column="partition_at",
                partition=date(2024, 1, partition_day),
                profile_columns=("loan_amount",),
                freshness_column=freshness_column,
                observed_at=observed_at,
            ),
        )

    assert snapshot.row_count == expected_rows
    assert snapshot.null_rates["loan_amount"] == (0.0 if expected_rows == 0 else 0.5)
    assert snapshot.freshness_at is None
    assert snapshot.freshness_status is FreshnessMeasurementStatus.UNAVAILABLE
    assert "freshness_used_fallback" not in snapshot.metric_values


def test_profile_snapshot_rejects_future_freshness_measurement() -> None:
    observed_at = datetime(2024, 1, 2, 9, 0, tzinfo=UTC)
    with DuckDBConnectionManager() as connection:
        _create_profile_table(connection)

        with pytest.raises(ProfileSnapshotError, match="future|미래"):
            create_profile_snapshot(
                connection,
                ProfileSnapshotRequest(
                    asset_name="raw.profile_test",
                    table_name="raw.profile_test",
                    partition_column="partition_at",
                    partition=date(2024, 1, 1),
                    profile_columns=("loan_amount",),
                    freshness_column="loaded_at",
                    observed_at=observed_at,
                ),
            )


def _create_profile_table(connection: duckdb.DuckDBPyConnection) -> None:
    connection.execute("CREATE SCHEMA raw")
    connection.execute(
        """
        CREATE TABLE raw.profile_test (
            partition_at TIMESTAMP,
            loaded_at TIMESTAMP,
            loan_amount DOUBLE,
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
