"""Freshness-delay vertical-slice integration tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import duckdb
import pytest

import hmda_reliability.data_operations as data_operations
import hmda_reliability.reliability.evaluation.freshness_delay as freshness_evaluation
from hmda_reliability.data_operations import DataOperationRequest, LifecycleResult
from hmda_reliability.data_operations.errors import DataOperationError
from hmda_reliability.data_platform.artifacts import ArtifactProjectionLockError
from hmda_reliability.data_platform.duckdb import DuckDBConnectionManager
from hmda_reliability.reliability import (
    Approval,
    ApprovalStatus,
    ApprovedBackfillRequest,
    BackfillValidationResult,
    DetectionThresholds,
    ProfileSnapshot,
    RecoveryProposal,
    evaluate_freshness_delay_vertical_slice,
)

pytestmark = pytest.mark.integration


def test_freshness_delay_vertical_slice_recovers_and_replays(tmp_path: Path) -> None:
    source_path, request = _fixture(tmp_path)
    proposals: list[RecoveryProposal] = []

    def approve(proposal: RecoveryProposal) -> Approval:
        proposals.append(proposal)
        return _approved(proposal)

    result = evaluate_freshness_delay_vertical_slice(
        request=request,
        source_paths=(source_path,),
        workspace=tmp_path / "run",
        approve=approve,
        validate_candidate=lambda _request: "sha256:candidate",
        validate_target=lambda _request: "sha256:target",
        max_age_minutes=60,
        delay_minutes=120,
    )

    assert len(proposals) == 1
    assert proposals[0].freshness_binding is not None
    assert result.fixture_identity == result.expected_recovery_identity
    assert result.clean_case.detected_incident_types == []
    assert result.freshness_delay_case.detected_incident_types == ["freshness_delay"]
    assert result.clean_freshness.freshness_at == datetime(
        2026, 8, 15, 9, 0, tzinfo=UTC
    )
    assert result.delayed_freshness.freshness_at == datetime(
        2026, 8, 15, 7, 0, tzinfo=UTC
    )
    assert result.recovery is not None
    assert result.recovery.mutation_state == "partition_changed"
    assert result.recovery.validation_passed
    assert result.recovery.freshness_validation_passed
    assert result.replay is not None
    assert result.replay.mutation_state == "already_recovered"
    assert result.replay.freshness_validation_passed
    assert result.recovery_freshness == result.replay_freshness
    assert result.post_recovery_case.detected_incident_types == []
    assert result.target_dbt_projection_id == "sha256:target"


def test_freshness_evaluation_rejects_existing_database_before_side_effects(
    tmp_path: Path,
) -> None:
    source_path, request = _fixture(tmp_path)
    request.database_path.touch()
    workspace = tmp_path / "run"

    with pytest.raises(ValueError, match="새 path"):
        evaluate_freshness_delay_vertical_slice(
            request=request,
            source_paths=(source_path,),
            workspace=workspace,
            approve=lambda proposal: pytest.fail(f"approval called: {proposal}"),
            validate_candidate=lambda candidate: pytest.fail(
                f"candidate callback called: {candidate}"
            ),
            validate_target=lambda target: pytest.fail(f"target called: {target}"),
        )

    assert not workspace.exists()


def test_freshness_evaluation_rejects_aliased_database_paths(tmp_path: Path) -> None:
    source_path, request = _fixture(tmp_path)
    workspace = tmp_path / "run"
    request = request.model_copy(update={"database_path": workspace / "clean.duckdb"})

    with pytest.raises(ValueError, match="서로 달라"):
        evaluate_freshness_delay_vertical_slice(
            request=request,
            source_paths=(source_path,),
            workspace=workspace,
            approve=_approved,
            validate_candidate=lambda _request: "candidate",
            validate_target=lambda _request: "target",
        )

    assert not workspace.exists()


def test_freshness_evaluation_rejects_insufficient_delay(tmp_path: Path) -> None:
    source_path, request = _fixture(tmp_path)
    workspace = tmp_path / "run"

    with pytest.raises(ValueError, match="delay_minutes"):
        evaluate_freshness_delay_vertical_slice(
            request=request,
            source_paths=(source_path,),
            workspace=workspace,
            approve=_approved,
            validate_candidate=lambda _request: "candidate",
            validate_target=lambda _request: "target",
            max_age_minutes=60,
            delay_minutes=59,
        )

    assert not workspace.exists()


def test_freshness_evaluation_rejects_inexact_controlled_timestamp(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source_path, request = _fixture(tmp_path)
    original_set_freshness = freshness_evaluation._set_partition_ingested_at
    call_count = 0

    def skew_delayed_timestamp(
        connection: duckdb.DuckDBPyConnection,
        candidate_request: DataOperationRequest,
        *,
        minutes_ago: float,
    ) -> None:
        nonlocal call_count
        call_count += 1
        original_set_freshness(
            connection,
            candidate_request,
            minutes_ago=minutes_ago + 30 if call_count == 2 else minutes_ago,
        )

    monkeypatch.setattr(
        freshness_evaluation,
        "_set_partition_ingested_at",
        skew_delayed_timestamp,
    )

    result = evaluate_freshness_delay_vertical_slice(
        request=request,
        source_paths=(source_path,),
        workspace=tmp_path / "run",
        approve=lambda proposal: pytest.fail(f"approval called: {proposal}"),
        validate_candidate=lambda candidate: pytest.fail(
            f"candidate callback called: {candidate}"
        ),
        validate_target=lambda target: pytest.fail(f"target called: {target}"),
        delay_minutes=120,
    )

    assert result.post_recovery_case.case_name == "unachieved_controlled_defect"
    assert any(
        "delayed-freshness-mismatch" in evidence
        for evidence in result.post_recovery_case.evidence_refs
    )


def test_freshness_evaluation_rejects_validation_mutation_before_approval(
    tmp_path: Path,
) -> None:
    source_path, request = _fixture(tmp_path)

    def mutate_candidate(candidate_request: DataOperationRequest) -> str:
        with DuckDBConnectionManager(candidate_request.database_path) as connection:
            connection.execute(
                """
                UPDATE raw.hmda_loans
                SET ingested_at = TIMESTAMPTZ '2026-08-15 08:30:00+00'
                WHERE source_year = 2025
                """
            )
        return "sha256:candidate"

    result = evaluate_freshness_delay_vertical_slice(
        request=request,
        source_paths=(source_path,),
        workspace=tmp_path / "run",
        approve=lambda proposal: pytest.fail(f"approval called: {proposal}"),
        validate_candidate=mutate_candidate,
        validate_target=lambda target: pytest.fail(f"target called: {target}"),
    )

    assert result.recovery is None
    assert result.post_recovery_case.case_name == "candidate_artifact_mismatch"
    assert result.post_recovery_case.failure_stage == "before_target_mutation"
    assert result.post_recovery_case.target_mutated is False
    assert any(
        "candidate-artifact-freshness-mismatch" in evidence
        for evidence in result.post_recovery_case.evidence_refs
    )


def test_freshness_evaluation_reports_temporal_target_drift(tmp_path: Path) -> None:
    source_path, request = _fixture(tmp_path)

    def approve_after_drift(proposal: RecoveryProposal) -> Approval:
        with DuckDBConnectionManager(request.database_path) as connection:
            connection.execute(
                """
                UPDATE raw.hmda_loans
                SET ingested_at = TIMESTAMPTZ '2026-08-15 07:30:00+00'
                WHERE source_year = 2025
                """
            )
        return _approved(proposal)

    result = evaluate_freshness_delay_vertical_slice(
        request=request,
        source_paths=(source_path,),
        workspace=tmp_path / "run",
        approve=approve_after_drift,
        validate_candidate=lambda _request: "sha256:candidate",
        validate_target=lambda _request: "sha256:target",
    )

    assert result.recovery is None
    assert result.post_recovery_case.failure_stage == "before_target_mutation"
    assert result.post_recovery_case.reconciliation_action == (
        "request_new_validation_and_approval"
    )
    assert result.post_recovery_case.target_mutated is False
    assert result.delayed_freshness.freshness_at == datetime(
        2026, 8, 15, 7, 0, tzinfo=UTC
    )


@pytest.mark.parametrize(
    "failure",
    [
        DataOperationError(
            "target dbt failed",
            context={"run_target_path": "dbt/target/runs/failed"},
        ),
        ValueError("target validation failed"),
    ],
    ids=("data-operation", "value-error"),
)
def test_freshness_evaluation_preserves_evidence_on_target_validation_failure(
    failure: Exception,
    tmp_path: Path,
) -> None:
    source_path, request = _fixture(tmp_path)

    def fail_target(_request: DataOperationRequest) -> str:
        raise failure

    result = evaluate_freshness_delay_vertical_slice(
        request=request,
        source_paths=(source_path,),
        workspace=tmp_path / "run",
        approve=_approved,
        validate_candidate=lambda _request: "sha256:candidate",
        validate_target=fail_target,
    )

    assert result.recovery is not None
    assert result.replay is not None
    assert result.recovery_freshness is not None
    assert result.replay_freshness == result.recovery_freshness
    assert result.post_recovery_case.failure_stage == "after_partition_mutation"
    assert result.post_recovery_case.reconciliation_action == "resume_verification"
    assert result.post_recovery_case.detection_passed
    assert result.target_dbt_failure == str(failure)


def test_freshness_evaluation_classifies_expired_replay_for_new_approval(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source_path, request = _fixture(tmp_path)
    original_execute = freshness_evaluation.execute_approved_backfill
    call_count = 0

    def expire_replay(
        connection: duckdb.DuckDBPyConnection,
        recovery_request: ApprovedBackfillRequest,
    ) -> BackfillValidationResult:
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            expired_profile_request = recovery_request.profile_request.model_copy(
                update={
                    "observed_at": recovery_request.profile_request.observed_at
                    + timedelta(minutes=60)
                }
            )
            recovery_request = recovery_request.model_copy(
                update={"profile_request": expired_profile_request}
            )
        return original_execute(connection, recovery_request)

    monkeypatch.setattr(
        freshness_evaluation,
        "execute_approved_backfill",
        expire_replay,
    )

    result = evaluate_freshness_delay_vertical_slice(
        request=request,
        source_paths=(source_path,),
        workspace=tmp_path / "run",
        approve=_approved,
        validate_candidate=lambda _request: "sha256:candidate",
        validate_target=lambda _request: "sha256:target",
    )

    assert result.recovery is not None
    assert result.replay is None
    assert result.post_recovery_case.case_name == "replay_failure"
    assert result.post_recovery_case.failure_stage == "after_partition_mutation"
    assert result.post_recovery_case.reconciliation_action == (
        "request_new_validation_and_approval"
    )


@pytest.mark.parametrize(
    ("invalid_call", "expected_case"),
    [
        (1, "recovery_validation_failure"),
        (2, "replay_validation_failure"),
    ],
    ids=("recovery", "replay"),
)
def test_freshness_evaluation_rejects_failed_recovery_validation(
    invalid_call: int,
    expected_case: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source_path, request = _fixture(tmp_path)
    original_execute = freshness_evaluation.execute_approved_backfill
    call_count = 0

    def invalidate_result(
        connection: duckdb.DuckDBPyConnection,
        recovery_request: ApprovedBackfillRequest,
    ) -> BackfillValidationResult:
        nonlocal call_count
        call_count += 1
        result = original_execute(connection, recovery_request)
        if call_count == invalid_call:
            return result.model_copy(update={"freshness_validation_passed": False})
        return result

    monkeypatch.setattr(
        freshness_evaluation,
        "execute_approved_backfill",
        invalidate_result,
    )

    result = evaluate_freshness_delay_vertical_slice(
        request=request,
        source_paths=(source_path,),
        workspace=tmp_path / "run",
        approve=_approved,
        validate_candidate=lambda _request: "sha256:candidate",
        validate_target=lambda target: pytest.fail(f"target called: {target}"),
    )

    assert result.post_recovery_case.case_name == expected_case
    assert result.post_recovery_case.failure_stage == "after_partition_mutation"
    assert result.post_recovery_case.reconciliation_action == "resume_verification"
    assert any(
        "freshness-validation:False" in evidence
        for evidence in result.post_recovery_case.evidence_refs
    )


def test_freshness_evaluation_blocks_target_validation_for_unresolved_incident(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source_path, request = _fixture(tmp_path)
    original_lifecycle = data_operations.run_incident_lifecycle
    delayed_lifecycle: LifecycleResult | None = None
    call_count = 0

    def keep_delayed_incident(
        lifecycle_request: DataOperationRequest,
        baseline: ProfileSnapshot,
        *,
        thresholds: DetectionThresholds | None = None,
    ) -> LifecycleResult:
        nonlocal call_count, delayed_lifecycle
        call_count += 1
        result = original_lifecycle(
            lifecycle_request,
            baseline,
            thresholds=thresholds,
        )
        if call_count == 2:
            delayed_lifecycle = result
        if call_count == 3:
            assert delayed_lifecycle is not None
            return delayed_lifecycle
        return result

    monkeypatch.setattr(
        data_operations,
        "run_incident_lifecycle",
        keep_delayed_incident,
    )

    result = evaluate_freshness_delay_vertical_slice(
        request=request,
        source_paths=(source_path,),
        workspace=tmp_path / "run",
        approve=_approved,
        validate_candidate=lambda _request: "sha256:candidate",
        validate_target=lambda target: pytest.fail(f"target called: {target}"),
    )

    assert result.recovery is not None
    assert result.replay is not None
    assert result.post_recovery_case.case_name == "unresolved_post_recovery_incident"
    assert result.post_recovery_case.detected_incident_types == ["freshness_delay"]
    assert result.post_recovery_case.failure_stage == "after_partition_mutation"


def test_freshness_evaluation_rejects_unavailable_candidate_before_approval(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source_path, request = _fixture(tmp_path)
    original_set_freshness = freshness_evaluation._set_partition_ingested_at
    call_count = 0

    def make_candidate_unavailable(
        connection: duckdb.DuckDBPyConnection,
        candidate_request: DataOperationRequest,
        *,
        minutes_ago: float,
    ) -> None:
        nonlocal call_count
        call_count += 1
        original_set_freshness(
            connection,
            candidate_request,
            minutes_ago=minutes_ago,
        )
        if call_count == 3:
            connection.execute("UPDATE raw.hmda_loans SET ingested_at = NULL")

    monkeypatch.setattr(
        freshness_evaluation,
        "_set_partition_ingested_at",
        make_candidate_unavailable,
    )

    result = evaluate_freshness_delay_vertical_slice(
        request=request,
        source_paths=(source_path,),
        workspace=tmp_path / "run",
        approve=lambda proposal: pytest.fail(f"approval called: {proposal}"),
        validate_candidate=lambda candidate: pytest.fail(
            f"candidate callback called: {candidate}"
        ),
        validate_target=lambda target: pytest.fail(f"target called: {target}"),
    )

    assert result.recovery is None
    assert result.post_recovery_case.case_name == "unachieved_controlled_defect"
    assert result.post_recovery_case.failure_stage == "before_target_mutation"
    assert any(
        "candidate-freshness-unavailable" in evidence
        for evidence in result.post_recovery_case.evidence_refs
    )


@pytest.mark.parametrize(
    "lifecycle_failure",
    [
        DataOperationError("post lifecycle failed"),
        ArtifactProjectionLockError("post lifecycle lock failed"),
    ],
    ids=("data-operation", "artifact-lock"),
)
def test_freshness_evaluation_preserves_evidence_on_post_lifecycle_failure(
    lifecycle_failure: Exception,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    source_path, request = _fixture(tmp_path)
    original_lifecycle = data_operations.run_incident_lifecycle
    call_count = 0

    def fail_post_lifecycle(
        lifecycle_request: DataOperationRequest,
        baseline: ProfileSnapshot,
        *,
        thresholds: DetectionThresholds | None = None,
    ) -> LifecycleResult:
        nonlocal call_count
        call_count += 1
        if call_count == 3:
            raise lifecycle_failure
        return original_lifecycle(
            lifecycle_request,
            baseline,
            thresholds=thresholds,
        )

    monkeypatch.setattr(
        data_operations,
        "run_incident_lifecycle",
        fail_post_lifecycle,
    )

    result = evaluate_freshness_delay_vertical_slice(
        request=request,
        source_paths=(source_path,),
        workspace=tmp_path / "run",
        approve=_approved,
        validate_candidate=lambda _request: "sha256:candidate",
        validate_target=lambda _request: "sha256:target",
    )

    assert result.recovery is not None
    assert result.replay is not None
    assert result.recovery_freshness is not None
    assert result.replay_freshness == result.recovery_freshness
    assert result.post_recovery_case.case_name == "post_recovery_lifecycle_failure"
    assert result.post_recovery_case.failure_stage == "after_partition_mutation"
    assert result.post_recovery_case.reconciliation_action == "resume_verification"


def _fixture(tmp_path: Path) -> tuple[Path, DataOperationRequest]:
    source_path = tmp_path / "year_2025.csv"
    source_path.write_text(
        "\n".join(
            [
                "activity_year,loan_purpose,action_taken,loan_amount,income,state_code,county_code",
                "2025,1,1,350000,120,CA,06001",
                "2025,31,3,420000,95,NY,36061",
            ]
        ),
        encoding="utf-8",
    )
    artifact_dir = tmp_path / "dbt" / "target"
    artifact_dir.mkdir(parents=True)
    (artifact_dir / "manifest.json").write_text(
        '{"sources":{"source.hmda_reliability.raw.hmda_loans":{"name":"hmda_loans","schema":"raw","resource_type":"source","depends_on":{"nodes":[]}}},"nodes":{}}',
        encoding="utf-8",
    )
    (artifact_dir / "run_results.json").write_text("{}", encoding="utf-8")
    request = DataOperationRequest(
        database_path=tmp_path / "target.duckdb",
        source_root=tmp_path,
        freshness_column="ingested_at",
        observed_at=datetime(2026, 8, 15, 9, 0, tzinfo=UTC),
        dbt_manifest_path=artifact_dir / "manifest.json",
        dbt_run_results_path=artifact_dir / "run_results.json",
    )
    return source_path, request


def _approved(proposal: RecoveryProposal) -> Approval:
    approved_at = datetime(2026, 8, 15, 9, 0, tzinfo=UTC)
    return Approval(
        approval_id="approval_freshness_delay",
        incident_id=proposal.incident_id,
        status=ApprovalStatus.APPROVED,
        requested_by="data-platform",
        requested_at=approved_at,
        approved_by="data-owner",
        approved_at=approved_at,
        requested_actions=proposal.target_actions,
        recovery_proposal=proposal,
    )
