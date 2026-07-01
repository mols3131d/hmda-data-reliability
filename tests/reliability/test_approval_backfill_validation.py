"""Approval 기반 backfill validation 테스트."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from project_pivot.data_platform.duckdb import DuckDBConnectionManager
from project_pivot.hmda_data import HMDA_LOANS_TABLE
from project_pivot.reliability import (
    Approval,
    ApprovalGateError,
    ApprovalStatus,
    ApprovedBackfillRequest,
    ProfileSnapshotRequest,
    execute_approved_backfill,
)


def test_pending_approval_blocks_before_source_access(tmp_path: Path) -> None:
    """미승인 요청은 source 파일을 보기 전에 차단된다."""

    missing_source = tmp_path / "missing.csv"

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(ApprovalGateError, match="승인되지 않은 backfill"),
    ):
        execute_approved_backfill(
            connection,
            _request(
                approval=_approval(ApprovalStatus.PENDING),
                source_paths=(missing_source,),
            ),
        )


def test_approved_backfill_overwrites_partition_and_rebuilds_profile(
    tmp_path: Path,
) -> None:
    """승인된 backfill은 source_year overwrite 후 profile snapshot을 재생성한다."""

    source_path = _write_hmda_csv(tmp_path)

    with DuckDBConnectionManager() as connection:
        result = execute_approved_backfill(
            connection,
            _request(
                approval=_approval(ApprovalStatus.APPROVED),
                source_paths=(source_path,),
            ),
        )

        row = connection.execute(
            """
            SELECT count(*), count(DISTINCT action_taken)
            FROM raw.hmda_loans
            WHERE activity_year = 2025
            """
        ).fetchone()

    assert row == (2, 2)
    assert result.row_count == 2
    assert result.profile_snapshot.row_count == 2
    assert result.profile_snapshot.partition == "2025"
    assert result.validation_passed
    assert result.executed_actions == [
        "overwrite_partition",
        "rerun_profile_snapshot",
    ]


def _request(
    *,
    approval: Approval,
    source_paths: tuple[Path, ...],
    source_year: int = 2025,
) -> ApprovedBackfillRequest:
    return ApprovedBackfillRequest(
        approval=approval,
        source_paths=source_paths,
        source_year=source_year,
        profile_request=ProfileSnapshotRequest(
            asset_name=HMDA_LOANS_TABLE,
            table_name=HMDA_LOANS_TABLE,
            partition_column="activity_year",
            partition=source_year,
            profile_columns=("loan_amount", "income"),
            observed_at=datetime(2026, 6, 10, 0, 0, tzinfo=UTC),
        ),
    )


def _approval(status: ApprovalStatus) -> Approval:
    requested_at = datetime(2026, 6, 10, 0, 0, tzinfo=UTC)
    if status is ApprovalStatus.APPROVED:
        return Approval(
            approval_id=f"approval_{status}",
            incident_id="inc_volume_drop_2025",
            status=status,
            requested_by="data-platform",
            requested_at=requested_at,
            approved_by="data-owner",
            approved_at=requested_at,
            requested_actions=["prepare_partition_backfill"],
        )
    return Approval(
        approval_id=f"approval_{status}",
        incident_id="inc_volume_drop_2025",
        status=status,
        requested_by="data-platform",
        requested_at=requested_at,
        requested_actions=["prepare_partition_backfill"],
    )


def _write_hmda_csv(tmp_path: Path) -> Path:
    path = tmp_path / "year_2025.csv"
    path.write_text(
        "\n".join(
            [
                "activity_year,loan_purpose,action_taken,loan_amount,income,state_code,county_code",
                "2025,1,1,350000,120,CA,06001",
                "2025,31,3,420000,95,NY,36061",
            ]
        ),
        encoding="utf-8",
    )
    return path
