"""Approval 기반 backfill validation 테스트."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import duckdb
import pytest
from pydantic import ValidationError

import hmda_reliability.reliability.recovery.executor as recovery_executor
from hmda_reliability.data_platform.duckdb import DuckDBConnectionManager
from hmda_reliability.hmda_data import (
    HMDA_LOANS_TABLE,
    PartitionContentIdentity,
    load_hmda_loans_partition,
    partition_content_identity,
    partition_max_ingested_at,
)
from hmda_reliability.hmda_data.errors import HMDAStalePartitionError
from hmda_reliability.reliability import (
    Approval,
    ApprovalGateError,
    ApprovalStatus,
    ApprovedBackfillRequest,
    BackfillValidationError,
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


@pytest.mark.unit
def test_approved_action_set_is_immutable() -> None:
    """승인 이후 action scope를 nested mutation으로 바꿀 수 없다."""

    approval = _approval(ApprovalStatus.APPROVED)

    with pytest.raises(AttributeError):
        cast(list[str], approval.requested_actions).append("delete_partition")

    assert approval.requested_actions == (
        "overwrite_partition",
        "rerun_profile_snapshot",
    )


@pytest.mark.component
def test_approval_gate_revalidates_model_copy_updates(tmp_path: Path) -> None:
    """Pydantic copy로 validator를 우회한 approval은 실행 경계에서 거부한다."""

    proposal = _proposal()
    approval = _approval(ApprovalStatus.PENDING).model_copy(
        update={
            "status": ApprovalStatus.APPROVED,
            "requested_actions": [
                "overwrite_partition",
                "rerun_profile_snapshot",
            ],
            "recovery_proposal": proposal,
        }
    )
    request = _request(
        approval=_approval(ApprovalStatus.APPROVED, proposal=proposal),
        proposal=proposal,
        source_paths=(tmp_path / "missing.csv",),
    ).model_copy(update={"approval": approval})

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(ApprovalGateError, match="contract"),
    ):
        execute_approved_backfill(connection, request)


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
    assert result.approved_before_freshness is None
    assert result.expected_after_freshness_at is None
    assert result.actual_freshness is None
    assert result.freshness_validation_passed is None
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
def test_freshness_recovery_changes_equal_content_stale_state(tmp_path: Path) -> None:
    source_path = _write_hmda_csv(tmp_path)
    candidate_path, proposal = _freshness_proposal_for_source(source_path, tmp_path)
    approval = _freshness_approval(proposal)

    with DuckDBConnectionManager() as connection:
        _load_stale_freshness_target(connection, source_path)
        before_identity = partition_content_identity(connection, source_year=2025)

        result = execute_approved_backfill(
            connection,
            _freshness_request(approval, proposal, candidate_path),
        )
        after_identity = partition_content_identity(connection, source_year=2025)

    assert before_identity == after_identity == proposal.expected_after_identity
    assert result.mutation_state == "partition_changed"
    assert result.validation_passed
    assert result.freshness_validation_passed
    assert proposal.freshness_binding is not None
    assert (
        result.approved_before_freshness == proposal.freshness_binding.approved_before
    )
    assert result.expected_after_freshness_at == datetime(2026, 8, 15, 9, 0, tzinfo=UTC)
    assert result.actual_freshness is not None
    assert result.actual_freshness.freshness_at == result.expected_after_freshness_at


@pytest.mark.integration
def test_freshness_recovery_rejects_candidate_timestamp_mismatch(
    tmp_path: Path,
) -> None:
    source_path = _write_hmda_csv(tmp_path)
    candidate_path, proposal = _freshness_proposal_for_source(source_path, tmp_path)
    approval = _freshness_approval(proposal)
    with DuckDBConnectionManager() as candidate:
        candidate.execute(
            """
            CREATE TABLE candidate AS
            SELECT * REPLACE (
                TIMESTAMPTZ '2026-08-15 08:59:00+00' AS ingested_at
            )
            FROM read_parquet(?)
            """,
            [candidate_path.as_posix()],
        )
        candidate_path.unlink()
        candidate.execute(
            "COPY candidate TO ? (FORMAT PARQUET)",
            [candidate_path.as_posix()],
        )

    with DuckDBConnectionManager() as connection:
        _load_stale_freshness_target(connection, source_path)
        before_freshness = partition_max_ingested_at(connection, source_year=2025)

        with pytest.raises(ApprovalGateError, match="candidate.*freshness"):
            execute_approved_backfill(
                connection,
                _freshness_request(approval, proposal, candidate_path),
            )
        after_freshness = partition_max_ingested_at(connection, source_year=2025)

    assert after_freshness == before_freshness


@pytest.mark.integration
def test_freshness_recovery_rejects_unavailable_candidate(tmp_path: Path) -> None:
    source_path = _write_hmda_csv(tmp_path)
    candidate_path, proposal = _freshness_proposal_for_source(source_path, tmp_path)
    approval = _freshness_approval(proposal)
    with DuckDBConnectionManager() as candidate:
        candidate.execute(
            """
            CREATE TABLE candidate AS
            SELECT * REPLACE (NULL::TIMESTAMPTZ AS ingested_at)
            FROM read_parquet(?)
            """,
            [candidate_path.as_posix()],
        )
        candidate_path.unlink()
        candidate.execute(
            "COPY candidate TO ? (FORMAT PARQUET)",
            [candidate_path.as_posix()],
        )

    with DuckDBConnectionManager() as connection:
        _load_stale_freshness_target(connection, source_path)
        before_freshness = partition_max_ingested_at(connection, source_year=2025)

        with pytest.raises(ApprovalGateError, match="candidate freshness"):
            execute_approved_backfill(
                connection,
                _freshness_request(approval, proposal, candidate_path),
            )
        after_freshness = partition_max_ingested_at(connection, source_year=2025)

    assert after_freshness == before_freshness


@pytest.mark.integration
def test_freshness_replay_blocks_expired_expected_state(tmp_path: Path) -> None:
    source_path = _write_hmda_csv(tmp_path)
    candidate_path, proposal = _freshness_proposal_for_source(source_path, tmp_path)
    approval = _freshness_approval(proposal)

    with DuckDBConnectionManager() as connection:
        _load_stale_freshness_target(connection, source_path)
        request = _freshness_request(approval, proposal, candidate_path)
        execute_approved_backfill(connection, request)
        expired_request = request.model_copy(
            update={
                "profile_request": request.profile_request.model_copy(
                    update={"observed_at": datetime(2026, 8, 15, 10, 0, tzinfo=UTC)}
                )
            }
        )

        with pytest.raises(ApprovalGateError, match="freshness|새 validation"):
            execute_approved_backfill(connection, expired_request)
        after_freshness = partition_max_ingested_at(connection, source_year=2025)

    assert after_freshness == datetime(2026, 8, 15, 9, 0, tzinfo=UTC)


@pytest.mark.integration
def test_freshness_recovery_transaction_gate_blocks_temporal_race(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source_path = _write_hmda_csv(tmp_path)
    candidate_path, proposal = _freshness_proposal_for_source(source_path, tmp_path)
    approval = _freshness_approval(proposal)
    original_load = cast(
        Callable[..., int],
        recovery_executor.load_hmda_loans_partition,
    )

    def drift_before_target_transaction(*args: object, **kwargs: object) -> int:
        if kwargs.get("expected_max_ingested_at") is not None:
            connection = cast(duckdb.DuckDBPyConnection, args[0])
            connection.execute(
                """
                UPDATE raw.hmda_loans
                SET ingested_at = TIMESTAMPTZ '2026-08-15 07:30:00+00'
                WHERE source_year = 2025
                """
            )
        return original_load(*args, **kwargs)

    monkeypatch.setattr(
        recovery_executor,
        "load_hmda_loans_partition",
        drift_before_target_transaction,
    )

    with DuckDBConnectionManager() as connection:
        _load_stale_freshness_target(connection, source_path)
        with pytest.raises(ApprovalGateError, match="새 validation과 approval"):
            execute_approved_backfill(
                connection,
                _freshness_request(approval, proposal, candidate_path),
            )
        after_freshness = partition_max_ingested_at(connection, source_year=2025)

    assert after_freshness == datetime(2026, 8, 15, 7, 30, tzinfo=UTC)


@pytest.mark.integration
def test_freshness_profile_failure_preserves_temporal_evidence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source_path = _write_hmda_csv(tmp_path)
    candidate_path, proposal = _freshness_proposal_for_source(source_path, tmp_path)
    approval = _freshness_approval(proposal)

    def fail_profile(*args: object, **kwargs: object) -> None:
        raise recovery_executor.ProfileSnapshotError("freshness profile failed")

    monkeypatch.setattr(recovery_executor, "create_profile_snapshot", fail_profile)

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(BackfillValidationError) as error,
    ):
        _load_stale_freshness_target(connection, source_path)
        execute_approved_backfill(
            connection,
            _freshness_request(approval, proposal, candidate_path),
        )

    assert error.value.mutation_state == "partition_changed"
    assert error.value.reconciliation_action == "resume_verification"
    assert error.value.context["actual_freshness_at"] == "2026-08-15T09:00:00+00:00"
    assert error.value.context["expected_after_freshness_at"] == (
        "2026-08-15T09:00:00+00:00"
    )


@pytest.mark.integration
def test_recovery_classifies_compare_and_replace_race_as_stale_approval(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Initial check 뒤 target이 바뀌면 stale approval로 분류한다."""

    source_path = _write_hmda_csv(tmp_path)
    proposal = _proposal_for_source(source_path)
    approval = _approval(ApprovalStatus.APPROVED, proposal=proposal)

    original_load = cast(
        Callable[..., int],
        recovery_executor.load_hmda_loans_partition,
    )
    load_count = 0

    def raise_stale_on_target_load(*args: object, **kwargs: object) -> int:
        nonlocal load_count
        load_count += 1
        if load_count == 2:
            raise HMDAStalePartitionError("stale")
        return original_load(*args, **kwargs)

    monkeypatch.setattr(
        recovery_executor,
        "load_hmda_loans_partition",
        raise_stale_on_target_load,
    )

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
def test_recovery_uses_approved_staged_source_when_original_changes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Source 검증 뒤 원본이 바뀌어도 target에는 승인된 staged content만 쓴다."""

    source_path = _write_hmda_csv(tmp_path)
    proposal = _proposal_for_source(source_path)
    approval = _approval(ApprovalStatus.APPROVED, proposal=proposal)
    original_identity = cast(
        Callable[..., PartitionContentIdentity],
        recovery_executor.partition_content_identity,
    )
    identity_count = 0

    def replace_original_after_source_identity(*args: object, **kwargs: object):
        nonlocal identity_count
        identity = original_identity(*args, **kwargs)
        identity_count += 1
        if identity_count == 1:
            source_path.write_text(
                source_path.read_text(encoding="utf-8").replace("120,CA", "121,CA"),
                encoding="utf-8",
            )
        return identity

    monkeypatch.setattr(
        recovery_executor,
        "partition_content_identity",
        replace_original_after_source_identity,
    )

    with DuckDBConnectionManager() as connection:
        result = execute_approved_backfill(
            connection,
            _request(
                approval=approval,
                proposal=proposal,
                source_paths=(source_path,),
            ),
        )

    assert result.validation_passed
    assert result.actual_identity == proposal.expected_after_identity


@pytest.mark.component
def test_recovery_wraps_staging_source_failure(tmp_path: Path) -> None:
    """Approved source staging 실패도 recovery domain error로 반환한다."""

    source_path = _write_hmda_csv(tmp_path)
    proposal = _proposal_for_source(source_path)
    approval = _approval(ApprovalStatus.APPROVED, proposal=proposal)
    source_path.unlink()

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(BackfillValidationError, match="backfill validation"),
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
def test_profile_failure_preserves_post_mutation_recovery_state(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Partition commit 후 profile 실패도 resume 가능한 상태로 반환한다."""

    source_path = _write_hmda_csv(tmp_path)
    proposal = _proposal_for_source(source_path)
    approval = _approval(ApprovalStatus.APPROVED, proposal=proposal)
    original_profile_builder = recovery_executor.create_profile_snapshot

    def fail_profile(*args: object, **kwargs: object) -> None:
        raise recovery_executor.ProfileSnapshotError("profile failed")

    monkeypatch.setattr(recovery_executor, "create_profile_snapshot", fail_profile)

    with DuckDBConnectionManager() as connection:
        with pytest.raises(BackfillValidationError) as error:
            execute_approved_backfill(
                connection,
                _request(
                    approval=approval,
                    proposal=proposal,
                    source_paths=(source_path,),
                ),
            )
        monkeypatch.setattr(
            recovery_executor,
            "create_profile_snapshot",
            original_profile_builder,
        )
        retry = execute_approved_backfill(
            connection,
            _request(approval=approval, proposal=proposal, source_paths=(source_path,)),
        )

    assert error.value.mutation_state == "partition_changed"
    assert error.value.reconciliation_action == "resume_verification"
    assert error.value.context["profile_error"] == "profile failed"
    assert error.value.context["actual_identity"]["row_count"] == 2
    assert retry.mutation_state == "already_recovered"
    assert retry.reconciliation_action == "resume_verification"


@pytest.mark.integration
def test_profile_failure_reports_diverged_post_mutation_state(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Profile 실패 시 실제 target이 diverged면 새 approval을 요구한다."""

    source_path = _write_hmda_csv(tmp_path)
    proposal = _proposal_for_source(source_path)
    approval = _approval(ApprovalStatus.APPROVED, proposal=proposal)

    def diverge_then_fail_profile(*args: object, **kwargs: object) -> None:
        connection = cast(duckdb.DuckDBPyConnection, args[0])
        connection.execute("UPDATE raw.hmda_loans SET income = income + 1")
        raise recovery_executor.ProfileSnapshotError("profile failed")

    monkeypatch.setattr(
        recovery_executor,
        "create_profile_snapshot",
        diverge_then_fail_profile,
    )

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(BackfillValidationError) as error,
    ):
        execute_approved_backfill(
            connection,
            _request(approval=approval, proposal=proposal, source_paths=(source_path,)),
        )

    assert error.value.mutation_state == "diverged_after_profile_failure"
    assert error.value.reconciliation_action == "request_new_validation_and_approval"
    assert error.value.context["execution_mutation_state"] == "partition_changed"


@pytest.mark.component
def test_recovery_wraps_staging_directory_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Approved recovery의 staging directory 생성 실패도 domain error로 반환한다."""

    source_path = _write_hmda_csv(tmp_path)
    proposal = _proposal_for_source(source_path)
    approval = _approval(ApprovalStatus.APPROVED, proposal=proposal)

    def fail_temporary_directory(*args: object, **kwargs: object) -> None:
        raise OSError("cannot create staging directory")

    monkeypatch.setattr(
        recovery_executor,
        "TemporaryDirectory",
        fail_temporary_directory,
    )

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(BackfillValidationError, match="backfill validation"),
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
def test_equal_count_content_mismatch_is_rejected_before_target_mutation(
    tmp_path: Path,
) -> None:
    """승인한 candidate와 다른 source는 target 변경 전에 차단한다."""

    approved_source = _write_hmda_csv(tmp_path)
    mismatched_source = tmp_path / "year_2025_mismatched.csv"
    mismatched_source.write_text(
        approved_source.read_text(encoding="utf-8").replace("120,CA", "121,CA"),
        encoding="utf-8",
    )
    proposal = _proposal_for_source(approved_source)
    approval = _approval(ApprovalStatus.APPROVED, proposal=proposal)

    with DuckDBConnectionManager() as connection:
        before = partition_content_identity(connection, source_year=2025)
        with pytest.raises(ApprovalGateError, match="candidate"):
            execute_approved_backfill(
                connection,
                _request(
                    approval=approval,
                    proposal=proposal,
                    source_paths=(mismatched_source,),
                ),
            )
        after = partition_content_identity(connection, source_year=2025)

    assert before == proposal.approved_before_identity
    assert after == before


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
        incident_type="volume_drop",
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
        incident_type="volume_drop",
        table_name=HMDA_LOANS_TABLE,
        source_year=2025,
        candidate_identity=expected,
        approved_before_identity=before,
        expected_after_identity=expected,
        validation_evidence_refs=("candidate-content", "candidate-dbt"),
        dbt_projection_id="dbt:candidate",
        target_actions=("overwrite_partition", "rerun_profile_snapshot"),
    )


def _freshness_proposal_for_source(
    source_path: Path,
    tmp_path: Path,
) -> tuple[Path, RecoveryProposal]:
    candidate_database_path = tmp_path / "freshness-candidate.duckdb"
    candidate_path = tmp_path / "freshness-candidate.parquet"
    candidate_at = datetime(2026, 8, 15, 9, 0, tzinfo=UTC)
    with DuckDBConnectionManager(candidate_database_path) as connection:
        load_hmda_loans_partition(connection, [source_path], 2025)
        connection.execute(
            "UPDATE raw.hmda_loans SET ingested_at = ? WHERE source_year = 2025",
            [candidate_at],
        )
        identity = partition_content_identity(connection, source_year=2025)
        connection.execute(
            "COPY raw.hmda_loans TO ? (FORMAT PARQUET)",
            [candidate_path.as_posix()],
        )
    proposal = RecoveryProposal(
        proposal_id="recovery_freshness_delay_2025",
        incident_id="inc_freshness_delay_2025",
        incident_type="freshness_delay",
        table_name=HMDA_LOANS_TABLE,
        source_year=2025,
        candidate_identity=identity,
        approved_before_identity=identity,
        expected_after_identity=identity,
        validation_evidence_refs=("candidate-content", "candidate-freshness"),
        dbt_projection_id="dbt:candidate",
        target_actions=("overwrite_partition", "rerun_profile_snapshot"),
        freshness_binding={
            "approved_before": {
                "freshness_status": "measured",
                "freshness_at": datetime(2026, 8, 15, 7, 0, tzinfo=UTC),
                "observed_at": datetime(2026, 8, 15, 9, 0, tzinfo=UTC),
            },
            "expected_after_freshness_at": candidate_at,
            "max_age_minutes": 60,
        },
    )
    return candidate_path, proposal


def _freshness_approval(proposal: RecoveryProposal) -> Approval:
    approved_at = datetime(2026, 8, 15, 9, 0, tzinfo=UTC)
    return Approval(
        approval_id="approval_freshness_delay_2025",
        incident_id=proposal.incident_id,
        status=ApprovalStatus.APPROVED,
        requested_by="data-platform",
        requested_at=approved_at,
        approved_by="data-owner",
        approved_at=approved_at,
        requested_actions=("overwrite_partition", "rerun_profile_snapshot"),
        recovery_proposal=proposal,
    )


def _freshness_request(
    approval: Approval,
    proposal: RecoveryProposal,
    candidate_path: Path,
) -> ApprovedBackfillRequest:
    return ApprovedBackfillRequest(
        approval=approval,
        proposal=proposal,
        source_paths=(candidate_path,),
        source_year=2025,
        profile_request=ProfileSnapshotRequest(
            asset_name=HMDA_LOANS_TABLE,
            table_name=HMDA_LOANS_TABLE,
            partition_column="activity_year",
            partition=2025,
            profile_columns=("loan_amount", "income"),
            freshness_column="ingested_at",
            observed_at=datetime(2026, 8, 15, 9, 30, tzinfo=UTC),
        ),
    )


def _load_stale_freshness_target(
    connection: duckdb.DuckDBPyConnection,
    source_path: Path,
) -> None:
    load_hmda_loans_partition(connection, [source_path], 2025)
    connection.execute(
        "UPDATE raw.hmda_loans SET ingested_at = TIMESTAMPTZ '2026-08-15 07:00:00+00'"
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