"""Approval 기반 backfill validation 테스트."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

import project_pivot.reliability.recovery.executor as recovery_executor
from project_pivot.data_platform.duckdb import DuckDBConnectionManager
from project_pivot.hmda_data import (
    HMDA_LOANS_TABLE,
    PartitionContentIdentity,
    load_hmda_loans_partition,
    partition_content_identity,
)
from project_pivot.hmda_data.errors import HMDAStalePartitionError
from project_pivot.reliability import (
    Approval,
    ApprovalGateError,
    ApprovalStatus,
    ApprovedBackfillRequest,
    ProfileSnapshotRequest,
    RecoveryProposal,
    execute_approved_backfill,
)


@pytest.mark.component
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


@pytest.mark.component
def test_approval_without_backfill_actions_is_rejected(tmp_path: Path) -> None:
    """다른 action 승인을 partition overwrite에 재사용하지 못하게 한다."""

    approval = _approval(ApprovalStatus.APPROVED).model_copy(
        update={"requested_actions": ["inspect_source"]}
    )

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(ApprovalGateError, match="action"),
    ):
        execute_approved_backfill(
            connection,
            _request(
                approval=approval,
                source_paths=(tmp_path / "missing.csv",),
            ),
        )


@pytest.mark.component
def test_mismatched_recovery_proposal_is_rejected_before_source_access(
    tmp_path: Path,
) -> None:
    """Approval과 request의 exact proposal이 다르면 source 접근 전에 차단한다."""

    approval = _approval(ApprovalStatus.APPROVED)
    mismatched = _proposal().model_copy(update={"dbt_projection_id": "dbt:other"})
    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(ApprovalGateError, match="proposal"),
    ):
        execute_approved_backfill(
            connection,
            _request(
                approval=approval,
                proposal=mismatched,
                source_paths=(tmp_path / "missing.csv",),
            ),
        )


@pytest.mark.integration
def test_approved_backfill_overwrites_partition_and_rebuilds_profile(
    tmp_path: Path,
) -> None:
    """승인된 backfill은 source_year overwrite 후 profile snapshot을 재생성한다."""

    source_path = _write_hmda_csv(tmp_path)

    proposal = _proposal_for_source(source_path)
    approval = _approval(ApprovalStatus.APPROVED, proposal=proposal)
    with DuckDBConnectionManager() as connection:
        result = execute_approved_backfill(
            connection,
            _request(
                approval=approval,
                proposal=proposal,
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
    assert result.actual_identity == proposal.expected_after_identity
    assert result.mutation_state == "partition_changed"
    assert result.reconciliation_action == "overwrite_partition"
    assert result.executed_actions == [
        "overwrite_partition",
        "rerun_profile_snapshot",
    ]


@pytest.mark.integration
def test_recovery_resumes_verification_without_repeating_overwrite(
    tmp_path: Path,
) -> None:
    """Expected-after target은 overwrite 없이 downstream verification만 재개한다."""

    source_path = _write_hmda_csv(tmp_path)
    proposal = _proposal_for_source(source_path)
    approval = _approval(ApprovalStatus.APPROVED, proposal=proposal)
    with DuckDBConnectionManager() as connection:
        load_hmda_loans_partition(connection, [source_path], 2025)
        result = execute_approved_backfill(
            connection,
            _request(approval=approval, proposal=proposal, source_paths=(source_path,)),
        )

    assert result.mutation_state == "already_recovered"
    assert result.reconciliation_action == "resume_verification"
    assert result.executed_actions == ["rerun_profile_snapshot"]


@pytest.mark.integration
def test_recovery_blocks_diverged_target_without_mutation(tmp_path: Path) -> None:
    """Approved before/after 어느 쪽도 아닌 target은 새 approval을 요구한다."""

    source_path = _write_hmda_csv(tmp_path)
    proposal = _proposal_for_source(source_path)
    approval = _approval(ApprovalStatus.APPROVED, proposal=proposal)
    with DuckDBConnectionManager() as connection:
        load_hmda_loans_partition(connection, [source_path], 2025)
        connection.execute("UPDATE raw.hmda_loans SET income = income + 1")
        diverged = partition_content_identity(connection, source_year=2025)

        with pytest.raises(ApprovalGateError, match="diverged"):
            execute_approved_backfill(
                connection,
                _request(
                    approval=approval,
                    proposal=proposal,
                    source_paths=(source_path,),
                ),
            )
        after = partition_content_identity(connection, source_year=2025)

    assert after == diverged


@pytest.mark.integration
def test_recovery_classifies_compare_and_replace_race_as_stale_approval(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Initial check 뒤 target이 바뀌면 stale approval로 분류한다."""

    source_path = _write_hmda_csv(tmp_path)
    proposal = _proposal_for_source(source_path)
    approval = _approval(ApprovalStatus.APPROVED, proposal=proposal)

    def raise_stale(*args: object, **kwargs: object) -> int:
        raise HMDAStalePartitionError("stale")

    monkeypatch.setattr(recovery_executor, "load_hmda_loans_partition", raise_stale)

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(ApprovalGateError, match="새 validation과 approval"),
    ):
        execute_approved_backfill(
            connection,
            _request(
                approval=approval,
                proposal=proposal,
                source_paths=(source_path,),
            ),
        )


@pytest.mark.integration
def test_equal_count_content_mismatch_is_post_mutation_failure(
    tmp_path: Path,
) -> None:
    """같은 row count의 다른 source는 content validation 실패로 관찰된다."""

    approved_source = _write_hmda_csv(tmp_path)
    mismatched_source = tmp_path / "year_2025_mismatched.csv"
    mismatched_source.write_text(
        approved_source.read_text(encoding="utf-8").replace("120,CA", "121,CA"),
        encoding="utf-8",
    )
    proposal = _proposal_for_source(approved_source)
    approval = _approval(ApprovalStatus.APPROVED, proposal=proposal)

    with DuckDBConnectionManager() as connection:
        result = execute_approved_backfill(
            connection,
            _request(
                approval=approval,
                proposal=proposal,
                source_paths=(mismatched_source,),
            ),
        )

    assert result.row_count == proposal.expected_after_identity.row_count
    assert result.actual_identity != proposal.expected_after_identity
    assert not result.validation_passed
    assert result.mutation_state == "partition_changed"


@pytest.mark.unit
def test_backfill_request_rejects_non_path_source_items() -> None:
    """source_paths 원소 타입 오류를 Pydantic validation error로 반환한다."""

    with pytest.raises(ValidationError, match="source_paths"):
        ApprovedBackfillRequest.model_validate(
            {
                "approval": _approval(ApprovalStatus.PENDING),
                "source_paths": [object()],
                "source_year": 2025,
                "profile_request": ProfileSnapshotRequest(
                    asset_name=HMDA_LOANS_TABLE,
                    table_name=HMDA_LOANS_TABLE,
                    partition_column="activity_year",
                    partition=2025,
                ),
            }
        )


def _request(
    *,
    approval: Approval,
    proposal: RecoveryProposal | None = None,
    source_paths: tuple[Path, ...],
    source_year: int = 2025,
) -> ApprovedBackfillRequest:
    return ApprovedBackfillRequest(
        approval=approval,
        proposal=proposal or approval.recovery_proposal or _proposal(),
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


def _approval(
    status: ApprovalStatus,
    *,
    proposal: RecoveryProposal | None = None,
) -> Approval:
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
            requested_actions=["overwrite_partition", "rerun_profile_snapshot"],
            recovery_proposal=proposal or _proposal(),
        )
    return Approval(
        approval_id=f"approval_{status}",
        incident_id="inc_volume_drop_2025",
        status=status,
        requested_by="data-platform",
        requested_at=requested_at,
        requested_actions=["prepare_partition_backfill"],
    )


def _proposal() -> RecoveryProposal:
    before = PartitionContentIdentity(
        table_name=HMDA_LOANS_TABLE,
        source_year=2025,
        row_count=0,
        digest="sha256-v1:before",
    )
    expected = PartitionContentIdentity(
        table_name=HMDA_LOANS_TABLE,
        source_year=2025,
        row_count=2,
        digest="sha256-v1:expected",
    )
    return RecoveryProposal(
        proposal_id="recovery_volume_drop_2025",
        incident_id="inc_volume_drop_2025",
        table_name=HMDA_LOANS_TABLE,
        source_year=2025,
        candidate_identity=expected,
        approved_before_identity=before,
        expected_after_identity=expected,
        validation_evidence_refs=("candidate-content", "candidate-dbt"),
        dbt_projection_id="dbt:candidate",
        target_actions=("overwrite_partition", "rerun_profile_snapshot"),
    )


def _proposal_for_source(source_path: Path) -> RecoveryProposal:
    with DuckDBConnectionManager() as connection:
        load_hmda_loans_partition(connection, [source_path], 2025)
        expected = partition_content_identity(connection, source_year=2025)
    before = PartitionContentIdentity(
        table_name=HMDA_LOANS_TABLE,
        source_year=2025,
        row_count=0,
        digest="sha256-v1:"
        + "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )
    return RecoveryProposal(
        proposal_id="recovery_volume_drop_2025",
        incident_id="inc_volume_drop_2025",
        table_name=HMDA_LOANS_TABLE,
        source_year=2025,
        candidate_identity=expected,
        approved_before_identity=before,
        expected_after_identity=expected,
        validation_evidence_refs=("candidate-content", "candidate-dbt"),
        dbt_projection_id="dbt:candidate",
        target_actions=("overwrite_partition", "rerun_profile_snapshot"),
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
