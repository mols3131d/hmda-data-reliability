"""Deterministic System Recovery End-to-End Integration Tests.

Validates the complete closed loop between Data Plane and Reliability Control Plane:
    S0: Clean Data Plane execution (ingestion, quality gate, real dbt build, promotion)
    S1: Controlled null_spike defect injection, partition preservation, gate block
    S2: Read-only incident lifecycle analysis and zero-mutation preservation
    S3: Clean candidate validation via real dbt build and exact proposal binding
    S4: Pre-approval safety cases verifying zero mutation on unapproved attempts
    S5: Approved recovery backfill execution and content identity restoration
    S6: Post-recovery re-validation (quality gate, lifecycle, analytics promotion)
    S7: Replay reconciliation avoiding redundant mutation
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from hmda_reliability.data_operations import (
    DataOperationRequest,
    evaluate_quality_gate,
    promote_dbt_artifacts,
    run_dbt_build,
    run_incident_lifecycle,
    run_quality_gated_dbt_build,
)
from hmda_reliability.data_platform.duckdb import DuckDBConnectionManager
from hmda_reliability.hmda_data import (
    PartitionContentIdentity,
    load_hmda_loans_partition,
    partition_content_identity,
)
from hmda_reliability.hmda_data.synthetic.cases import null_spike
from hmda_reliability.reliability import (
    Approval,
    ApprovalGateError,
    ApprovalStatus,
    ApprovedBackfillRequest,
    ProfileSnapshotRequest,
    QualityGateError,
    RecoveryProposal,
    create_profile_snapshot,
    evaluate_null_spike_vertical_slice,
    execute_approved_backfill,
)

pytestmark = pytest.mark.integration


def _clean_hmda_csv(root: Path, row_count: int = 10) -> Path:
    """Generate a clean 2025 HMDA CSV with non-null required columns."""
    csv_path = root / "year_2025.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        "activity_year,loan_purpose,action_taken,loan_amount,income,state_code,county_code",
    ]
    for index in range(1, row_count + 1):
        purpose = 1 if index <= 5 else 31
        action = 1 if index % 2 == 1 else 3
        amount = index * 50000
        income = 100 + index * 10
        state = "CA" if index <= 5 else "NY"
        county = "06001" if index <= 5 else "36061"
        rows.append(f"2025,{purpose},{action},{amount},{income},{state},{county}")
    csv_path.write_text("\n".join(rows), encoding="utf-8")
    return csv_path


def _make_data_operation_request(
    database_path: Path,
    source_root: Path,
    workspace_root: Path,
    *,
    source_file: str | None = None,
    observed_at: datetime | None = None,
) -> DataOperationRequest:
    """Create a fully isolated DataOperationRequest pointing to canonical dbt paths."""
    manifest_path = workspace_root / "current_projection" / "manifest.json"
    run_results_path = workspace_root / "current_projection" / "run_results.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    return DataOperationRequest(
        database_path=database_path,
        source_root=source_root,
        source_year=2025,
        source_file=source_file,
        profile_columns=("loan_amount", "income"),
        dbt_project_dir=Path("dbt"),
        dbt_profiles_dir=Path("dbt"),
        dbt_manifest_path=manifest_path,
        dbt_run_results_path=run_results_path,
        dbt_run_target_path=workspace_root / "dbt_runs",
        observed_at=observed_at or datetime(2026, 6, 10, 0, 0, tzinfo=UTC),
    )


def _profile_request(request: DataOperationRequest) -> ProfileSnapshotRequest:
    """Build a ProfileSnapshotRequest ensuring observed_at is non-null."""
    assert request.observed_at is not None
    return ProfileSnapshotRequest(
        asset_name=request.asset_name,
        table_name=request.raw_table_name,
        partition_column=request.partition_column,
        partition=request.source_year,
        profile_columns=request.profile_columns,
        observed_at=request.observed_at,
    )


def _assert_analytics_outputs(database_path: Path, expected_rows: int = 10) -> None:
    """Query staging and mart models directly to verify analytical correctness."""
    with DuckDBConnectionManager(database_path, read_only=True) as connection:
        staging_count = connection.execute(
            "SELECT count(*) FROM staging.stg_hmda_loans"
        ).fetchone()
        assert staging_count is not None
        assert int(staging_count[0]) == expected_rows

        mart_count = connection.execute(
            "SELECT count(*) FROM marts.mart_hmda_loan_outcomes"
        ).fetchone()
        assert mart_count is not None
        assert int(mart_count[0]) > 0


def _build_approval(proposal: RecoveryProposal) -> Approval:
    """Create a valid matching Approval fixture for the exact proposal."""
    approved_at = datetime(2026, 6, 10, 0, 0, tzinfo=UTC)
    return Approval(
        approval_id=f"approval_{proposal.incident_id}",
        incident_id=proposal.incident_id,
        status=ApprovalStatus.APPROVED,
        requested_by="data-platform",
        requested_at=approved_at,
        approved_by="data-owner",
        approved_at=approved_at,
        requested_actions=proposal.target_actions,
        recovery_proposal=proposal,
    )


def _setup_dirty_target(
    tmp_path: Path,
) -> tuple[
    Path, Path, DataOperationRequest, PartitionContentIdentity, PartitionContentIdentity
]:
    """Helper to set up clean source and dirty target partition for safety tests."""
    clean_csv = _clean_hmda_csv(tmp_path / "raw")
    with DuckDBConnectionManager() as connection:
        defect_path = null_spike(
            connection,
            [clean_csv],
            tmp_path / "synthetic",
            case_name="null_spike_2025",
            target_column="income",
            null_fraction=0.5,
        )

    clean_db = tmp_path / "clean_ref.duckdb"
    with DuckDBConnectionManager(clean_db) as connection:
        load_hmda_loans_partition(
            connection, [clean_csv], 2025, table_name="raw.hmda_loans"
        )
        clean_identity = partition_content_identity(
            connection, table_name="raw.hmda_loans", source_year=2025
        )

    target_db = tmp_path / "target_dirty.duckdb"
    with DuckDBConnectionManager(target_db) as connection:
        load_hmda_loans_partition(
            connection, [defect_path], 2025, table_name="raw.hmda_loans"
        )
        dirty_identity = partition_content_identity(
            connection, table_name="raw.hmda_loans", source_year=2025
        )

    target_request = _make_data_operation_request(
        database_path=target_db,
        source_root=tmp_path / "raw",
        workspace_root=tmp_path / "ws_safety",
    )
    return clean_csv, target_db, target_request, clean_identity, dirty_identity


def test_deterministic_system_recovery_e2e(tmp_path: Path) -> None:
    """Multi-stage system recovery loop across Data Plane and Control Plane."""
    workspace = tmp_path / "system_e2e"
    workspace.mkdir(parents=True, exist_ok=True)
    clean_csv = _clean_hmda_csv(tmp_path / "raw")

    # S0: Clean Initial Data Plane execution on target database
    target_db = workspace / "target.duckdb"
    target_request = _make_data_operation_request(
        database_path=target_db,
        source_root=tmp_path / "raw",
        workspace_root=workspace / "target_proj",
    )
    with DuckDBConnectionManager(target_db) as connection:
        load_hmda_loans_partition(
            connection, [clean_csv], 2025, table_name="raw.hmda_loans"
        )
        clean_identity = partition_content_identity(
            connection, table_name="raw.hmda_loans", source_year=2025
        )
        clean_baseline = create_profile_snapshot(
            connection,
            _profile_request(target_request),
        )

    assert clean_identity.row_count == 10
    assert clean_baseline.null_rates["income"] == 0.0
    assert clean_baseline.null_rates["loan_amount"] == 0.0

    evaluate_quality_gate(target_request)
    initial_dbt_result = run_quality_gated_dbt_build(target_request)
    assert initial_dbt_result.succeeded is True
    promote_dbt_artifacts(initial_dbt_result, target_request)
    assert target_request.dbt_manifest_path.exists()
    assert target_request.dbt_run_results_path.exists()
    _assert_analytics_outputs(target_db, expected_rows=10)

    # S1: Controlled Defect Injection & Blocking Gate
    with DuckDBConnectionManager() as connection:
        defect_path = null_spike(
            connection,
            [clean_csv],
            workspace / "synthetic",
            case_name="null_spike_2025",
            target_column="income",
            null_fraction=0.5,
        )

    with DuckDBConnectionManager(target_db) as connection:
        load_hmda_loans_partition(
            connection, [defect_path], 2025, table_name="raw.hmda_loans"
        )
        dirty_identity = partition_content_identity(
            connection, table_name="raw.hmda_loans", source_year=2025
        )
        dirty_profile = create_profile_snapshot(
            connection,
            _profile_request(target_request),
        )

    assert dirty_identity.row_count == 10
    assert dirty_identity != clean_identity
    assert dirty_profile.null_rates["income"] == 0.50

    with pytest.raises(QualityGateError, match=r"null_spike\(income\)") as gate_error:
        evaluate_quality_gate(target_request)
    assert gate_error.value.detected_incident_types == ["null_spike(income)"]

    with pytest.raises(QualityGateError, match=r"null_spike\(income\)"):
        run_quality_gated_dbt_build(target_request)

    # S2: Read-Only Incident Analysis
    lifecycle_result = run_incident_lifecycle(target_request, clean_baseline)
    assert lifecycle_result.detected_incident_types == ["null_spike"]
    assert len(lifecycle_result.detected_incident_ids) == 1
    assert len(lifecycle_result.affected_assets) > 0

    with DuckDBConnectionManager(target_db, read_only=True) as connection:
        observed_target_identity = partition_content_identity(
            connection, table_name="raw.hmda_loans", source_year=2025
        )
    assert observed_target_identity == dirty_identity

    # S3: Candidate Validation with Real dbt & Exact Proposal Binding
    candidate_db = workspace / "candidate.duckdb"
    with DuckDBConnectionManager(candidate_db) as connection:
        load_hmda_loans_partition(
            connection, [clean_csv], 2025, table_name="raw.hmda_loans"
        )
        candidate_identity = partition_content_identity(
            connection, table_name="raw.hmda_loans", source_year=2025
        )
    assert candidate_identity == clean_identity

    candidate_request = _make_data_operation_request(
        database_path=candidate_db,
        source_root=tmp_path / "raw",
        workspace_root=workspace / "candidate_proj",
    )
    candidate_dbt_result = run_dbt_build(candidate_request)
    assert candidate_dbt_result.succeeded is True
    candidate_projection_id = candidate_dbt_result.projection_id

    incident_id = lifecycle_result.detected_incident_ids[0]
    proposal = RecoveryProposal(
        proposal_id=f"recovery_{incident_id}",
        incident_id=incident_id,
        incident_type="null_spike",
        table_name="raw.hmda_loans",
        source_year=2025,
        source_file=None,
        candidate_identity=candidate_identity,
        approved_before_identity=dirty_identity,
        expected_after_identity=clean_identity,
        validation_evidence_refs=(candidate_identity.digest, candidate_projection_id),
        dbt_projection_id=candidate_projection_id,
        target_actions=("overwrite_partition", "rerun_profile_snapshot"),
    )

    # S5: Approved Recovery Execution
    approval = _build_approval(proposal)
    backfill_request = ApprovedBackfillRequest(
        approval=approval,
        proposal=proposal,
        source_paths=(clean_csv,),
        source_year=2025,
        source_file=None,
        table_name="raw.hmda_loans",
        profile_request=_profile_request(target_request),
    )

    with DuckDBConnectionManager(target_db) as connection:
        recovery_result = execute_approved_backfill(connection, backfill_request)

    assert recovery_result.mutation_state == "partition_changed"
    assert recovery_result.validation_passed is True
    assert recovery_result.actual_identity == clean_identity
    assert recovery_result.profile_snapshot.null_rates["income"] == 0.0

    # S6: Post-Recovery Re-validation & Analytics Promotion
    evaluate_quality_gate(target_request)
    post_recovery_lifecycle = run_incident_lifecycle(target_request, clean_baseline)
    assert post_recovery_lifecycle.detected_incident_types == []

    recovered_dbt_result = run_quality_gated_dbt_build(target_request)
    assert recovered_dbt_result.succeeded is True
    promote_dbt_artifacts(recovered_dbt_result, target_request)
    _assert_analytics_outputs(target_db, expected_rows=10)

    # S7: Replay Reconciliation
    with DuckDBConnectionManager(target_db) as connection:
        replay_result = execute_approved_backfill(connection, backfill_request)

    assert replay_result.mutation_state == "already_recovered"
    assert replay_result.validation_passed is True
    assert replay_result.actual_identity == clean_identity
    assert replay_result.row_count == 10


def test_null_spike_evaluator_real_dbt_e2e(tmp_path: Path) -> None:
    """Validate vertical-slice evaluator using real dbt build and promotion."""
    workspace = tmp_path / "evaluator_e2e"
    workspace.mkdir(parents=True, exist_ok=True)
    clean_csv = _clean_hmda_csv(workspace / "raw")

    # Seed current projection so initial lifecycle can lock and read dbt manifest
    seed_db = workspace / "seed.duckdb"
    seed_request = _make_data_operation_request(
        database_path=seed_db,
        source_root=workspace / "raw",
        workspace_root=workspace / "current_proj",
    )
    with DuckDBConnectionManager(seed_db) as connection:
        load_hmda_loans_partition(
            connection, [clean_csv], 2025, table_name="raw.hmda_loans"
        )
    seed_dbt = run_dbt_build(seed_request)
    promote_dbt_artifacts(seed_dbt, seed_request)

    request = _make_data_operation_request(
        database_path=workspace / "eval_target.duckdb",
        source_root=workspace / "raw",
        workspace_root=workspace / "current_proj",
    )

    def validate_candidate(cand_req: DataOperationRequest) -> str:
        build_result = run_dbt_build(cand_req)
        return build_result.projection_id

    def validate_target(tgt_req: DataOperationRequest) -> str:
        build_result = run_dbt_build(tgt_req)
        promote_dbt_artifacts(build_result, tgt_req)
        return build_result.projection_id

    result = evaluate_null_spike_vertical_slice(
        request=request,
        source_paths=(clean_csv,),
        workspace=workspace / "eval_workspace",
        target_column="income",
        null_fraction=0.5,
        approve=_build_approval,
        validate_candidate=validate_candidate,
        validate_target=validate_target,
    )

    assert result.clean_case.detected_incident_types == []
    assert result.null_spike_case.detected_incident_types == ["null_spike"]
    assert result.recovery is not None
    assert result.recovery.mutation_state == "partition_changed"
    assert result.recovery.validation_passed is True
    assert result.post_recovery_case.detected_incident_types == []
    assert result.target_dbt_projection_id is not None
    assert result.target_dbt_projection_id.startswith("sha256:")
    _assert_analytics_outputs(request.database_path, expected_rows=10)


def test_pre_approval_safety_rejected_approval_zero_mutation(tmp_path: Path) -> None:
    """Rejected approval raises ApprovalGateError and leaves target unchanged."""
    clean_csv, target_db, target_request, clean_identity, dirty_identity = (
        _setup_dirty_target(tmp_path)
    )

    proposal = RecoveryProposal(
        proposal_id="proposal_rejected",
        incident_id="incident_rejected",
        incident_type="null_spike",
        table_name="raw.hmda_loans",
        source_year=2025,
        source_file=None,
        candidate_identity=clean_identity,
        approved_before_identity=dirty_identity,
        expected_after_identity=clean_identity,
        validation_evidence_refs=(clean_identity.digest, "sha256:dummy"),
        dbt_projection_id="sha256:dummy",
        target_actions=("overwrite_partition", "rerun_profile_snapshot"),
    )
    rejected_approval = Approval(
        approval_id="approval_rejected",
        incident_id="incident_rejected",
        status=ApprovalStatus.REJECTED,
        requested_by="data-platform",
        requested_at=datetime(2026, 6, 10, 0, 0, tzinfo=UTC),
        rejected_by="data-owner",
        rejected_at=datetime(2026, 6, 10, 0, 0, tzinfo=UTC),
        requested_actions=proposal.target_actions,
        recovery_proposal=proposal,
    )
    backfill_request = ApprovedBackfillRequest(
        approval=rejected_approval,
        proposal=proposal,
        source_paths=(clean_csv,),
        source_year=2025,
        source_file=None,
        table_name="raw.hmda_loans",
        profile_request=_profile_request(target_request),
    )

    with (
        DuckDBConnectionManager(target_db) as connection,
        pytest.raises(ApprovalGateError, match=r"승인되지 않은 backfill 요청입니다"),
    ):
        execute_approved_backfill(connection, backfill_request)

    with DuckDBConnectionManager(target_db, read_only=True) as connection:
        post_attempt_identity = partition_content_identity(
            connection, table_name="raw.hmda_loans", source_year=2025
        )
        post_attempt_profile = create_profile_snapshot(
            connection,
            _profile_request(target_request),
        )

    assert post_attempt_identity == dirty_identity
    assert post_attempt_profile.null_rates["income"] == 0.50


def test_pre_approval_safety_mismatched_identity_zero_mutation(tmp_path: Path) -> None:
    """Approval with mismatched before identity blocks before mutation."""
    clean_csv, target_db, target_request, clean_identity, dirty_identity = (
        _setup_dirty_target(tmp_path)
    )

    mismatched_before_identity = PartitionContentIdentity(
        table_name="raw.hmda_loans",
        source_year=2025,
        source_file=None,
        row_count=10,
        digest="sha256:0000000000000000000000000000000000000000000000000000000000000000",
    )
    proposal = RecoveryProposal(
        proposal_id="proposal_mismatched",
        incident_id="incident_mismatched",
        incident_type="null_spike",
        table_name="raw.hmda_loans",
        source_year=2025,
        source_file=None,
        candidate_identity=clean_identity,
        approved_before_identity=mismatched_before_identity,
        expected_after_identity=clean_identity,
        validation_evidence_refs=(clean_identity.digest, "sha256:dummy"),
        dbt_projection_id="sha256:dummy",
        target_actions=("overwrite_partition", "rerun_profile_snapshot"),
    )
    approval = _build_approval(proposal)
    backfill_request = ApprovedBackfillRequest(
        approval=approval,
        proposal=proposal,
        source_paths=(clean_csv,),
        source_year=2025,
        source_file=None,
        table_name="raw.hmda_loans",
        profile_request=_profile_request(target_request),
    )

    with (
        DuckDBConnectionManager(target_db) as connection,
        pytest.raises(ApprovalGateError, match="diverged|일치"),
    ):
        execute_approved_backfill(connection, backfill_request)

    with DuckDBConnectionManager(target_db, read_only=True) as connection:
        post_attempt_identity = partition_content_identity(
            connection, table_name="raw.hmda_loans", source_year=2025
        )
    assert post_attempt_identity == dirty_identity


def test_pre_approval_safety_mismatched_actions_zero_mutation(tmp_path: Path) -> None:
    """Approval missing required recovery actions blocks before mutation."""
    clean_csv, target_db, target_request, clean_identity, dirty_identity = (
        _setup_dirty_target(tmp_path)
    )

    proposal = RecoveryProposal(
        proposal_id="proposal_actions",
        incident_id="incident_actions",
        incident_type="null_spike",
        table_name="raw.hmda_loans",
        source_year=2025,
        source_file=None,
        candidate_identity=clean_identity,
        approved_before_identity=dirty_identity,
        expected_after_identity=clean_identity,
        validation_evidence_refs=(clean_identity.digest, "sha256:dummy"),
        dbt_projection_id="sha256:dummy",
        target_actions=("overwrite_partition", "rerun_profile_snapshot"),
    )
    # Tamper requested actions to omit rerun_profile_snapshot
    tampered_approval = Approval(
        approval_id="approval_actions",
        incident_id=proposal.incident_id,
        status=ApprovalStatus.APPROVED,
        requested_by="data-platform",
        requested_at=datetime(2026, 6, 10, 0, 0, tzinfo=UTC),
        approved_by="data-owner",
        approved_at=datetime(2026, 6, 10, 0, 0, tzinfo=UTC),
        requested_actions=("overwrite_partition",),
        recovery_proposal=proposal,
    )
    backfill_request = ApprovedBackfillRequest(
        approval=tampered_approval,
        proposal=proposal,
        source_paths=(clean_csv,),
        source_year=2025,
        source_file=None,
        table_name="raw.hmda_loans",
        profile_request=_profile_request(target_request),
    )

    with (
        DuckDBConnectionManager(target_db) as connection,
        pytest.raises(ApprovalGateError, match="action"),
    ):
        execute_approved_backfill(connection, backfill_request)

    with DuckDBConnectionManager(target_db, read_only=True) as connection:
        post_attempt_identity = partition_content_identity(
            connection, table_name="raw.hmda_loans", source_year=2025
        )
    assert post_attempt_identity == dirty_identity
