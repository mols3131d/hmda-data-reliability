"""Controlled schema-drift exact restoration evaluation tests."""

from __future__ import annotations

import fcntl
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO

import duckdb
import pytest

import hmda_reliability.reliability as reliability
import hmda_reliability.reliability.evaluation.schema_drift as schema_drift_evaluation
from hmda_reliability.data_operations import DataOperationRequest, DbtBuildResult
from hmda_reliability.data_operations.errors import DataOperationError
from hmda_reliability.data_platform.duckdb import DuckDBConnectionManager
from hmda_reliability.reliability import (
    ApprovalGateError,
    ApprovalStatus,
    SchemaRecoveryApproval,
    SchemaRecoveryProposal,
    build_evaluation_report,
    render_evaluation_report_markdown,
)
from hmda_reliability.reliability.errors import SchemaRecoveryValidationError


def _evaluation_api() -> tuple[Any, type[Any]]:
    evaluate = getattr(reliability, "evaluate_schema_drift_vertical_slice", None)
    result_type = getattr(reliability, "SchemaDriftVerticalSliceResult", None)
    assert evaluate is not None, (
        "evaluate_schema_drift_vertical_slice API가 필요합니다."
    )
    assert result_type is not None, "SchemaDriftVerticalSliceResult API가 필요합니다."
    return evaluate, result_type


@pytest.mark.integration
@pytest.mark.parametrize("existing_database", ["target", "clean", "candidate"])
def test_schema_drift_evaluation_rejects_existing_database_before_setup(
    tmp_path: Path,
    existing_database: str,
) -> None:
    """Existing evaluation DB is untouched and rejected before source/callbacks."""

    evaluate, _ = _evaluation_api()
    workspace = tmp_path / "run"
    request = _request(tmp_path, workspace=workspace)
    database_paths = {
        "target": request.database_path,
        "clean": workspace / "clean.duckdb",
        "candidate": workspace / "candidate.duckdb",
    }
    existing_path = database_paths[existing_database]
    existing_path.parent.mkdir(parents=True, exist_ok=True)
    with DuckDBConnectionManager(existing_path) as connection:
        connection.execute("CREATE TABLE sentinel(value INTEGER)")
        connection.execute("INSERT INTO sentinel VALUES (42)")
    original_bytes = existing_path.read_bytes()
    original_entries = (
        {path.name for path in workspace.iterdir()} if workspace.exists() else None
    )
    callback_calls: list[str] = []

    with pytest.raises(ValueError, match="새 path"):
        evaluate(
            request=request,
            source_paths=(tmp_path / "missing.csv",),
            workspace=workspace,
            approve=lambda proposal: callback_calls.append("approve"),
            validate_candidate=lambda candidate_request: _dbt_result(
                tmp_path,
                candidate_request,
            ),
            validate_target=lambda target_request: _dbt_result(
                tmp_path,
                target_request,
            ),
        )

    assert callback_calls == []
    assert existing_path.read_bytes() == original_bytes
    if original_entries is None:
        assert not workspace.exists()
    else:
        assert {path.name for path in workspace.iterdir()} == original_entries


@pytest.mark.integration
@pytest.mark.parametrize("alias_name", ["clean.duckdb", "candidate.duckdb"])
def test_schema_drift_evaluation_rejects_canonical_path_alias_before_setup(
    tmp_path: Path,
    alias_name: str,
) -> None:
    """Non-existing path aliases are rejected before workspace creation."""

    evaluate, _ = _evaluation_api()
    workspace = tmp_path / "run"
    aliased_target = workspace / "nested" / ".." / alias_name
    request = _request(tmp_path, workspace=workspace).model_copy(
        update={"database_path": aliased_target}
    )
    callback_calls: list[str] = []

    with pytest.raises(ValueError, match="서로 달라야"):
        evaluate(
            request=request,
            source_paths=(tmp_path / "missing.csv",),
            workspace=workspace,
            approve=lambda proposal: callback_calls.append("approve"),
            validate_candidate=lambda candidate_request: _dbt_result(
                tmp_path,
                candidate_request,
            ),
            validate_target=lambda target_request: _dbt_result(
                tmp_path,
                target_request,
            ),
        )

    assert callback_calls == []
    assert not workspace.exists()


@pytest.mark.integration
def test_schema_drift_evaluation_materializes_complete_varchar_target(
    tmp_path: Path,
) -> None:
    """Clean complete table becomes an actual VARCHAR target with one drift incident."""

    evaluate, result_type = _evaluation_api()
    workspace = tmp_path / "run"
    source_paths = _write_complete_sources(tmp_path)
    request = _request(tmp_path, workspace=workspace)

    def stop_before_recovery(proposal: object) -> object:
        del proposal
        raise ApprovalGateError("stop after controlled drift proof")

    result = evaluate(
        request=request,
        source_paths=source_paths,
        workspace=workspace,
        approve=stop_before_recovery,
        validate_candidate=lambda candidate_request: _dbt_result(
            tmp_path,
            candidate_request,
        ),
        validate_target=lambda target_request: _dbt_result(
            tmp_path,
            target_request,
        ),
    )

    assert isinstance(result, result_type)
    assert result.clean_case.detected_incident_types == []
    assert result.schema_drift_case.detected_incident_types == ["schema_drift"]
    assert result.baseline_state.schema_hash != result.drifted_state.schema_hash
    assert result.baseline_state.row_count == result.drifted_state.row_count == 3
    assert tuple(
        identity.source_year for identity in result.drifted_state.partition_identities
    ) == (2024, 2025)
    assert result.drifted_column == "loan_amount"
    assert result.drifted_column_type == "VARCHAR"
    with DuckDBConnectionManager(request.database_path, read_only=True) as connection:
        column_type = connection.execute(
            """
            SELECT data_type
            FROM information_schema.columns
            WHERE table_schema = 'raw'
              AND table_name = 'hmda_loans'
              AND column_name = 'loan_amount'
            """
        ).fetchone()
    assert column_type == ("VARCHAR",)


@pytest.mark.integration
def test_schema_drift_evaluation_restores_exact_state_and_replays(
    tmp_path: Path,
) -> None:
    """Approved complete candidate restores clean state, lifecycle, dbt, and replay."""

    evaluate, _ = _evaluation_api()
    workspace = tmp_path / "run"
    source_paths = _write_complete_sources(tmp_path)
    request = _request(tmp_path, workspace=workspace)
    proposals: list[SchemaRecoveryProposal] = []
    target_validation_states: list[reliability.TableStateIdentity] = []

    def approve(proposal: SchemaRecoveryProposal) -> SchemaRecoveryApproval:
        proposals.append(proposal)
        assert proposal.observation_partition == "2025"
        assert proposal.candidate_state == proposal.expected_after_state
        assert tuple(
            identity.source_year
            for identity in proposal.expected_after_state.partition_identities
        ) == (2024, 2025)
        approved_at = datetime(2026, 8, 16, 0, 0, tzinfo=UTC)
        return SchemaRecoveryApproval(
            approval_id="approval_schema_drift_2025",
            incident_id=proposal.incident_id,
            status=ApprovalStatus.APPROVED,
            requested_by="data-platform",
            requested_at=approved_at,
            approved_by="data-owner",
            approved_at=approved_at,
            requested_actions=proposal.target_actions,
            recovery_proposal=proposal,
        )

    def validate_candidate(candidate_request: DataOperationRequest) -> DbtBuildResult:
        with DuckDBConnectionManager(
            candidate_request.database_path,
            read_only=True,
        ) as connection:
            state = reliability.create_table_state_identity(
                connection,
                candidate_request.raw_table_name,
            )
        assert state.schema_hash.startswith("sha256:")
        return _dbt_result(tmp_path, candidate_request)

    def validate_target(target_request: DataOperationRequest) -> DbtBuildResult:
        with DuckDBConnectionManager(
            target_request.database_path,
            read_only=True,
        ) as connection:
            state = reliability.create_table_state_identity(
                connection,
                target_request.raw_table_name,
            )
        target_validation_states.append(state)
        assert proposals
        assert state == proposals[0].expected_after_state
        return _dbt_result(tmp_path, target_request)

    result = evaluate(
        request=request,
        source_paths=source_paths,
        workspace=workspace,
        approve=approve,
        validate_candidate=validate_candidate,
        validate_target=validate_target,
    )

    assert len(proposals) == 1
    assert result.recovery is not None
    assert result.replay is not None
    assert result.recovery.mutation_state == "table_replaced"
    assert result.recovery.actual_state == result.baseline_state
    assert result.replay.mutation_state == "already_restored"
    assert result.replay.reconciliation_action == "resume_verification"
    assert result.post_recovery_case.detected_incident_types == []
    assert result.post_recovery_case.target_mutated is True
    assert result.target_dbt_projection_id == "sha256:target"
    assert target_validation_states == [result.baseline_state]
    assert result.clean_case.required_actions == []
    assert result.clean_case.action_passed
    assert result.post_recovery_case.action_passed
    report = build_evaluation_report(
        [result.clean_case, result.schema_drift_case, result.post_recovery_case]
    )
    assert report.action_passed_cases == 3
    assert report.action_success_rate == 1.0
    with DuckDBConnectionManager(request.database_path, read_only=True) as connection:
        final_state = reliability.create_table_state_identity(
            connection,
            request.raw_table_name,
        )
    assert final_state == result.baseline_state


@pytest.mark.integration
def test_schema_drift_evaluation_rejects_incomplete_candidate_before_approval(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Incomplete candidate cannot reach approval or target mutation."""

    evaluate, _ = _evaluation_api()
    workspace = tmp_path / "run"
    source_paths = _write_complete_sources(tmp_path)
    request = _request(tmp_path, workspace=workspace)
    original_load = schema_drift_evaluation.load_hmda_loans
    load_count = 0
    approval_calls: list[SchemaRecoveryProposal] = []

    def load_incomplete_candidate(
        connection: duckdb.DuckDBPyConnection,
        paths: tuple[Path, ...],
        *,
        table_name: str,
    ) -> int:
        nonlocal load_count
        load_count += 1
        row_count = original_load(connection, paths, table_name=table_name)
        if load_count == 3:
            connection.execute("DELETE FROM raw.hmda_loans WHERE source_year = 2024")
        return row_count

    monkeypatch.setattr(
        schema_drift_evaluation,
        "load_hmda_loans",
        load_incomplete_candidate,
    )

    result = evaluate(
        request=request,
        source_paths=source_paths,
        workspace=workspace,
        approve=lambda proposal: approval_calls.append(proposal),
        validate_candidate=lambda candidate_request: _dbt_result(
            tmp_path,
            candidate_request,
        ),
        validate_target=lambda target_request: _dbt_result(
            tmp_path,
            target_request,
        ),
    )

    assert approval_calls == []
    assert result.post_recovery_case.case_name == "invalid_candidate"
    assert result.post_recovery_case.failure_stage == "before_target_mutation"
    assert result.post_recovery_case.target_mutated is False
    assert result.post_recovery_case.reconciliation_action == (
        "request_new_validation_and_approval"
    )
    assert not result.post_recovery_case.action_passed
    with DuckDBConnectionManager(request.database_path, read_only=True) as connection:
        current = reliability.create_table_state_identity(
            connection,
            request.raw_table_name,
        )
    assert current == result.drifted_state


@pytest.mark.integration
@pytest.mark.parametrize("stale_kind", ["schema", "content"])
def test_schema_drift_evaluation_maps_stale_target_before_mutation(
    tmp_path: Path,
    stale_kind: str,
) -> None:
    """Approval-time target drift requires new validation without recovery mutation."""

    evaluate, _ = _evaluation_api()
    workspace = tmp_path / "run"
    source_paths = _write_complete_sources(tmp_path)
    request = _request(tmp_path, workspace=workspace)

    def approve(proposal: SchemaRecoveryProposal) -> SchemaRecoveryApproval:
        with DuckDBConnectionManager(request.database_path) as connection:
            if stale_kind == "schema":
                connection.execute(
                    "ALTER TABLE raw.hmda_loans ADD COLUMN stale_marker INTEGER"
                )
            else:
                connection.execute(
                    "UPDATE raw.hmda_loans SET income = income + 1 "
                    "WHERE source_year = 2025"
                )
        return _approved(proposal)

    result = evaluate(
        request=request,
        source_paths=source_paths,
        workspace=workspace,
        approve=approve,
        validate_candidate=lambda candidate_request: _dbt_result(
            tmp_path,
            candidate_request,
        ),
        validate_target=lambda target_request: _dbt_result(
            tmp_path,
            target_request,
        ),
    )

    assert result.recovery is None
    assert result.post_recovery_case.case_name == "stale_target"
    assert result.post_recovery_case.failure_stage == "before_target_mutation"
    assert result.post_recovery_case.target_mutated is False
    assert result.post_recovery_case.reconciliation_action == (
        "request_new_validation_and_approval"
    )
    assert not result.post_recovery_case.action_passed
    assert any(
        "current_state" in evidence
        for evidence in result.post_recovery_case.evidence_refs
    )


@pytest.mark.integration
def test_schema_drift_evaluation_records_committed_state_after_unlock_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    evaluate, _ = _evaluation_api()
    workspace = tmp_path / "run"
    source_paths = _write_complete_sources(tmp_path)
    request = _request(tmp_path, workspace=workspace)
    original_flock = fcntl.flock

    def fail_target_unlock(file: TextIO, operation: int) -> None:
        if operation == fcntl.LOCK_UN and Path(file.name).name == (
            f".{request.database_path.name}.mutation.lock"
        ):
            raise OSError("injected target unlock failure")
        original_flock(file, operation)

    def approve(proposal: SchemaRecoveryProposal) -> SchemaRecoveryApproval:
        monkeypatch.setattr(fcntl, "flock", fail_target_unlock)
        return _approved(proposal)

    result = evaluate(
        request=request,
        source_paths=source_paths,
        workspace=workspace,
        approve=approve,
        validate_candidate=lambda candidate_request: _dbt_result(
            tmp_path, candidate_request
        ),
        validate_target=lambda _: pytest.fail("cleanup failure must stop validation"),
    )

    assert result.recovery is None
    assert result.post_recovery_case.failure_stage == "after_target_mutation"
    assert result.post_recovery_case.target_mutated is True
    assert result.post_recovery_case.reconciliation_action == "resume_verification"
    assert not result.post_recovery_case.action_passed
    with DuckDBConnectionManager(request.database_path, read_only=True) as connection:
        actual = reliability.create_table_state_identity(
            connection, request.raw_table_name
        )
    assert actual == result.expected_after_state


@pytest.mark.integration
def test_schema_drift_evaluation_maps_rolled_back_replacement(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Rolled-back replacement is no committed mutation and retryable approval."""

    evaluate, _ = _evaluation_api()
    workspace = tmp_path / "run"
    source_paths = _write_complete_sources(tmp_path)
    request = _request(tmp_path, workspace=workspace)

    def fail_replacement(
        recovery_request: reliability.ApprovedSchemaRecoveryRequest,
    ) -> reliability.SchemaRecoveryValidationResult:
        del recovery_request
        raise SchemaRecoveryValidationError(
            "replacement rolled back",
            failure_stage="in_target_transaction",
            mutation_state="rolled_back",
            reconciliation_action="retry_same_approval",
            context={"rollback": True},
        )

    monkeypatch.setattr(
        schema_drift_evaluation,
        "execute_approved_schema_recovery",
        fail_replacement,
    )

    result = evaluate(
        request=request,
        source_paths=source_paths,
        workspace=workspace,
        approve=_approved,
        validate_candidate=lambda candidate_request: _dbt_result(
            tmp_path,
            candidate_request,
        ),
        validate_target=lambda target_request: _dbt_result(
            tmp_path,
            target_request,
        ),
    )

    assert result.recovery is None
    assert result.post_recovery_case.case_name == "replacement_rollback"
    assert result.post_recovery_case.failure_stage == "in_target_transaction"
    assert result.post_recovery_case.target_mutated is False
    assert result.post_recovery_case.reconciliation_action == "retry_same_approval"
    assert not result.post_recovery_case.action_passed


@pytest.mark.integration
def test_schema_drift_evaluation_maps_diverged_replay(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Post-recovery target drift needs new approval."""

    evaluate, _ = _evaluation_api()
    workspace = tmp_path / "run"
    source_paths = _write_complete_sources(tmp_path)
    request = _request(tmp_path, workspace=workspace)
    original_execute = schema_drift_evaluation.execute_approved_schema_recovery
    execution_count = 0

    def diverge_before_replay(
        recovery_request: reliability.ApprovedSchemaRecoveryRequest,
    ) -> reliability.SchemaRecoveryValidationResult:
        nonlocal execution_count
        result = original_execute(recovery_request)
        execution_count += 1
        if execution_count == 1:
            with DuckDBConnectionManager(request.database_path) as connection:
                connection.execute(
                    "UPDATE raw.hmda_loans SET income = income + 1 "
                    "WHERE source_year = 2025"
                )
        return result

    monkeypatch.setattr(
        schema_drift_evaluation,
        "execute_approved_schema_recovery",
        diverge_before_replay,
    )

    result = evaluate(
        request=request,
        source_paths=source_paths,
        workspace=workspace,
        approve=_approved,
        validate_candidate=lambda candidate_request: _dbt_result(
            tmp_path,
            candidate_request,
        ),
        validate_target=lambda target_request: _dbt_result(
            tmp_path,
            target_request,
        ),
    )

    assert result.recovery is not None
    assert result.replay is None
    assert result.post_recovery_case.case_name == "diverged_replay"
    assert result.post_recovery_case.failure_stage == "replay_verification"
    assert result.post_recovery_case.target_mutated is True
    assert result.post_recovery_case.reconciliation_action == (
        "request_new_validation_and_approval"
    )
    assert not result.post_recovery_case.action_passed


@pytest.mark.integration
def test_schema_drift_evaluation_maps_post_restoration_dbt_failure(
    tmp_path: Path,
) -> None:
    """Target dbt failure preserves committed recovery and resumes verification."""

    evaluate, _ = _evaluation_api()
    workspace = tmp_path / "run"
    source_paths = _write_complete_sources(tmp_path)
    request = _request(tmp_path, workspace=workspace)

    def fail_target_dbt(_request: DataOperationRequest) -> DbtBuildResult:
        raise DataOperationError(
            "target dbt failed",
            context={"run_target_path": str(tmp_path / "failed-target-dbt")},
        )

    result = evaluate(
        request=request,
        source_paths=source_paths,
        workspace=workspace,
        approve=_approved,
        validate_candidate=lambda candidate_request: _dbt_result(
            tmp_path,
            candidate_request,
        ),
        validate_target=fail_target_dbt,
    )

    assert result.recovery is not None
    assert result.replay is not None
    assert result.post_recovery_case.case_name == "recovery_dbt_failure"
    assert result.post_recovery_case.failure_stage == "after_target_mutation"
    assert result.post_recovery_case.target_mutated is True
    assert result.post_recovery_case.reconciliation_action == "resume_verification"
    assert result.target_dbt_failure == "target dbt failed"
    assert result.target_dbt_failure_context == {
        "run_target_path": str(tmp_path / "failed-target-dbt")
    }
    assert result.post_recovery_case.evidence_refs == [
        "failure:DataOperationError",
        "target dbt failed",
        f"run_target_path:{tmp_path / 'failed-target-dbt'}",
    ]
    assert result.recovery.actual_state == result.baseline_state
    assert result.replay.actual_state == result.baseline_state

    report = build_evaluation_report(
        [result.clean_case, result.schema_drift_case, result.post_recovery_case]
    )
    rendered = render_evaluation_report_markdown(report)
    assert not result.post_recovery_case.action_passed, rendered
    assert report.total_cases == 3
    assert report.detection_passed_cases == 3
    assert report.action_passed_cases == 2
    assert report.action_success_rate == 2 / 3
    assert "| Action passed | 2 |" in rendered
    assert "| Action success rate | 66.67% |" in rendered
    assert (
        "| recovery_dbt_failure | - | - | PASS | FAIL | YES | "
        "after_target_mutation | resume_verification | "
        "failure:DataOperationError, target dbt failed, "
        f"run_target_path:{tmp_path / 'failed-target-dbt'} | - |"
    ) in rendered


def _request(tmp_path: Path, *, workspace: Path) -> DataOperationRequest:
    artifact_root = tmp_path / "dbt" / "target"
    artifact_root.mkdir(parents=True, exist_ok=True)
    artifact_root.joinpath("manifest.json").write_text(
        '{"sources":{"source.hmda_reliability.raw.hmda_loans":{"name":"hmda_loans","schema":"raw","resource_type":"source","depends_on":{"nodes":[]}}},"nodes":{}}',
        encoding="utf-8",
    )
    artifact_root.joinpath("run_results.json").write_text("{}", encoding="utf-8")
    return DataOperationRequest(
        database_path=workspace / "target.duckdb",
        source_root=tmp_path,
        source_year=2025,
        asset_name="source.hmda_reliability.raw.hmda_loans",
        raw_table_name="raw.hmda_loans",
        partition_column="activity_year",
        profile_columns=("loan_amount", "income"),
        observed_at=datetime(2026, 8, 16, 0, 0, tzinfo=UTC),
        dbt_manifest_path=artifact_root / "manifest.json",
        dbt_run_results_path=artifact_root / "run_results.json",
        dbt_run_target_path=workspace / "dbt-runs",
    )


def _write_complete_sources(tmp_path: Path) -> tuple[Path, Path]:
    source_2024 = tmp_path / "year_2024.csv"
    source_2025 = tmp_path / "year_2025.csv"
    header = (
        "activity_year,loan_purpose,action_taken,loan_amount,income,"
        "state_code,county_code"
    )
    source_2024.write_text(
        "\n".join([header, "2024,1,1,100000,80,TX,48113"]),
        encoding="utf-8",
    )
    source_2025.write_text(
        "\n".join(
            [
                header,
                "2025,1,1,200000,90,CA,06001",
                "2025,31,3,300000,100,NY,36061",
            ]
        ),
        encoding="utf-8",
    )
    return source_2024, source_2025


def _dbt_result(
    tmp_path: Path,
    request: DataOperationRequest,
) -> DbtBuildResult:
    run_target = tmp_path / f"{request.database_path.stem}-dbt"
    return DbtBuildResult(
        command=["dbt", "build"],
        return_code=0,
        manifest_path=run_target / "manifest.json",
        run_results_path=run_target / "run_results.json",
        projection_id=f"sha256:{request.database_path.stem}",
        succeeded=True,
    )


def _approved(proposal: SchemaRecoveryProposal) -> SchemaRecoveryApproval:
    approved_at = datetime(2026, 8, 16, 0, 0, tzinfo=UTC)
    return SchemaRecoveryApproval(
        approval_id="approval_schema_drift_2025",
        incident_id=proposal.incident_id,
        status=ApprovalStatus.APPROVED,
        requested_by="data-platform",
        requested_at=approved_at,
        approved_by="data-owner",
        approved_at=approved_at,
        requested_actions=proposal.target_actions,
        recovery_proposal=proposal,
    )
