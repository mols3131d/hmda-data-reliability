"""Approval 기반 backfill validation 테스트."""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path

import duckdb
import pytest

from project_pivot.reliability import (
    Approval,
    ApprovalGateError,
    ApprovalStatus,
    ApprovedBackfillRequest,
    ProfileSnapshotRequest,
    execute_approved_backfill,
)
from project_pivot.taxi_data import YELLOW_TRIPDATA_TABLE, DuckDBConnectionManager


def test_pending_approval_blocks_before_source_access(tmp_path: Path) -> None:
    """미승인 요청은 source 파일을 보기 전에 차단된다."""
    missing_source = tmp_path / "missing.parquet"

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(ApprovalGateError, match="승인되지 않은 backfill"),
    ):
        execute_approved_backfill(
            connection,
            _request(
                approval=_approval(ApprovalStatus.PENDING),
                parquet_paths=(missing_source,),
            ),
        )


def test_approved_backfill_overwrites_partition_and_rebuilds_profile(
    tmp_path: Path,
) -> None:
    """승인된 backfill은 partition overwrite 후 profile snapshot을 재생성한다."""
    source_path = tmp_path / "yellow_tripdata_2024-01.parquet"
    partition_date = date(2024, 1, 15)

    with DuckDBConnectionManager() as connection:
        _write_tripdata(connection, source_path)

        result = execute_approved_backfill(
            connection,
            _request(
                approval=_approval(ApprovalStatus.APPROVED),
                parquet_paths=(source_path,),
                partition_date=partition_date,
            ),
        )

        row = connection.execute(
            """
            SELECT count(*), count(DISTINCT VendorID)
            FROM raw.yellow_tripdata
            WHERE CAST(tpep_pickup_datetime AS DATE) = DATE '2024-01-15'
            """
        ).fetchone()

    assert row == (2, 2)
    assert result.row_count == 2
    assert result.profile_snapshot.row_count == 2
    assert result.profile_snapshot.partition == "2024-01-15"
    assert result.validation_passed
    assert result.executed_actions == [
        "overwrite_partition",
        "rerun_profile_snapshot",
    ]


def _request(
    *,
    approval: Approval,
    parquet_paths: tuple[Path, ...],
    partition_date: date = date(2024, 1, 15),
) -> ApprovedBackfillRequest:
    return ApprovedBackfillRequest(
        approval=approval,
        parquet_paths=parquet_paths,
        partition_date=partition_date,
        profile_request=ProfileSnapshotRequest(
            asset_name=YELLOW_TRIPDATA_TABLE,
            table_name=YELLOW_TRIPDATA_TABLE,
            partition_column="tpep_pickup_datetime",
            partition=partition_date,
            profile_columns=("total_amount", "passenger_count"),
            freshness_column="tpep_dropoff_datetime",
            observed_at=datetime(2026, 6, 10, 0, 0, tzinfo=UTC),
        ),
    )


def _approval(status: ApprovalStatus) -> Approval:
    requested_at = datetime(2026, 6, 10, 0, 0, tzinfo=UTC)
    if status is ApprovalStatus.APPROVED:
        return Approval(
            approval_id=f"approval_{status}",
            incident_id="inc_volume_drop_2024_01_15",
            status=status,
            requested_by="data-platform",
            requested_at=requested_at,
            approved_by="data-owner",
            approved_at=requested_at,
            requested_actions=["prepare_partition_backfill"],
        )
    return Approval(
        approval_id=f"approval_{status}",
        incident_id="inc_volume_drop_2024_01_15",
        status=status,
        requested_by="data-platform",
        requested_at=requested_at,
        requested_actions=["prepare_partition_backfill"],
    )


def _write_tripdata(connection: duckdb.DuckDBPyConnection, path: Path) -> None:
    connection.execute(
        """
        COPY (
            SELECT
                vendor_id AS VendorID,
                pickup_at AS tpep_pickup_datetime,
                pickup_at + INTERVAL '15 minutes' AS tpep_dropoff_datetime,
                1::BIGINT AS passenger_count,
                vendor_id::DOUBLE AS trip_distance,
                1 AS PULocationID,
                2 AS DOLocationID,
                1::BIGINT AS payment_type,
                10.0 AS fare_amount,
                (10.0 + vendor_id)::DOUBLE AS total_amount
            FROM (
                VALUES
                    (1, TIMESTAMP '2024-01-15 08:00:00'),
                    (2, TIMESTAMP '2024-01-15 09:00:00'),
                    (3, TIMESTAMP '2024-01-16 08:00:00')
            ) AS rows(vendor_id, pickup_at)
        )
        TO ?
        (FORMAT PARQUET)
        """,
        [str(path)],
    )
