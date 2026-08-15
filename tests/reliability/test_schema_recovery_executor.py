"""Approved exact table-schema recovery executor tests."""

from __future__ import annotations

import subprocess
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from subprocess import CompletedProcess
from threading import Event, Thread
from typing import Any

import duckdb
import pytest

import project_pivot.data_operations.runner as data_runner
import project_pivot.hmda_data.ingestion.partition as partition_module
import project_pivot.reliability as reliability
import project_pivot.reliability.recovery.schema_executor as schema_executor
from project_pivot.data_operations import DataOperationRequest
from project_pivot.data_platform.duckdb import (
    DuckDBConnectionManager,
    database_mutation_lock,
)
from project_pivot.hmda_data import (
    PartitionContentIdentity,
    load_hmda_loans,
    load_hmda_loans_partition,
    partition_content_identity,
)
from project_pivot.hmda_data.errors import HMDAStalePartitionError
from project_pivot.reliability import (
    ApprovalGateError,
    ApprovalStatus,
    ApprovedSchemaRecoveryRequest,
    ProfileSnapshotRequest,
    SchemaRecoveryApproval,
    SchemaRecoveryProposal,
    SchemaRecoveryValidationError,
    StagedSchemaRecoveryCandidate,
    TableStateIdentity,
)
from project_pivot.reliability.errors import (
    ProfileSnapshotError,
    TableStateIdentityError,
)


def _executor_api() -> tuple[Any, type[SchemaRecoveryValidationError]]:
    execute = getattr(reliability, "execute_approved_schema_recovery", None)
    error_type = getattr(reliability, "SchemaRecoveryValidationError", None)
    assert execute is not None, "execute_approved_schema_recovery API가 필요합니다."
    assert error_type is not None, "SchemaRecoveryValidationError API가 필요합니다."
    return execute, error_type


@pytest.mark.component
def test_schema_recovery_rejects_mismatched_approval_before_candidate_access(
    tmp_path: Path,
) -> None:
    """Exact proposal mismatch는 candidate database 확인보다 먼저 실패한다."""

    execute, _ = _executor_api()
    request = _request(tmp_path, target_state="before")
    missing_candidate = tmp_path / "missing-candidate.duckdb"
    mismatched = request.proposal.model_copy(update={"dbt_projection_id": "dbt:other"})
    invalid_request = request.model_copy(
        update={
            "proposal": mismatched,
            "candidate_database_path": missing_candidate,
        }
    )

    with pytest.raises(ApprovalGateError, match="proposal"):
        execute(invalid_request)

    assert not missing_candidate.exists()


@pytest.mark.component
def test_schema_recovery_replaces_approved_before_state(tmp_path: Path) -> None:
    """Approved before-state is replaced with the exact complete candidate."""

    execute, _ = _executor_api()
    request = _request(tmp_path, target_state="before")

    result = execute(request)

    with DuckDBConnectionManager(request.target_database_path) as connection:
        actual_state = reliability.create_table_state_identity(
            connection,
            request.proposal.table_name,
        )
    assert actual_state == request.proposal.expected_after_state
    assert result.actual_state == actual_state
    assert result.mutation_state == "table_replaced"
    assert result.reconciliation_action == "replace_table"
    sentinel = next(
        identity
        for identity in result.actual_state.partition_identities
        if identity.source_year == 2024
    )
    expected_sentinel = next(
        identity
        for identity in request.proposal.expected_after_state.partition_identities
        if identity.source_year == 2024
    )
    assert sentinel == expected_sentinel


@pytest.mark.component
def test_schema_recovery_replays_exact_after_without_replacement(
    tmp_path: Path,
) -> None:
    """Exact after-state replay resumes profile verification without replacement."""

    execute, _ = _executor_api()
    request = _request(tmp_path, target_state="after")

    result = execute(request)

    assert result.actual_state == request.proposal.expected_after_state
    assert result.mutation_state == "already_restored"
    assert result.reconciliation_action == "resume_verification"
    assert result.executed_actions == ("rerun_profile_snapshot",)


@pytest.mark.component
def test_schema_recovery_rejects_diverged_target_without_mutation(
    tmp_path: Path,
) -> None:
    """Third-state target cannot reuse an existing approval."""

    execute, error_type = _executor_api()
    request = _request(tmp_path, target_state="diverged")
    with DuckDBConnectionManager(request.target_database_path) as connection:
        before = reliability.create_table_state_identity(
            connection,
            request.proposal.table_name,
        )

    with pytest.raises(error_type, match="diverged") as error:
        execute(request)

    with DuckDBConnectionManager(request.target_database_path) as connection:
        after = reliability.create_table_state_identity(
            connection,
            request.proposal.table_name,
        )
    assert after == before
    assert error.value.failure_stage == "before_target_mutation"
    assert error.value.reconciliation_action == ("request_new_validation_and_approval")


@pytest.mark.component
@pytest.mark.parametrize(
    "failure",
    ["replacement", "final_state", "profile"],
)
def test_schema_recovery_rolls_back_in_transaction_failures(
    failure: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Replacement, exact-state, and profile failures preserve exact before-state."""

    execute, error_type = _executor_api()
    request = _request(tmp_path, target_state="before")
    with DuckDBConnectionManager(request.target_database_path) as connection:
        before = reliability.create_table_state_identity(
            connection,
            request.proposal.table_name,
        )

    if failure == "replacement":
        missing_artifact = tmp_path / "missing.parquet"
        monkeypatch.setattr(
            schema_executor,
            "stage_approved_schema_recovery_candidate",
            lambda **kwargs: StagedSchemaRecoveryCandidate(
                artifact_path=missing_artifact,
                candidate_state=request.proposal.candidate_state,
            ),
        )
    elif failure == "final_state":
        mismatched_artifact = _write_mismatched_candidate(tmp_path)
        monkeypatch.setattr(
            schema_executor,
            "stage_approved_schema_recovery_candidate",
            lambda **kwargs: StagedSchemaRecoveryCandidate(
                artifact_path=mismatched_artifact,
                candidate_state=request.proposal.candidate_state,
            ),
        )
    else:
        monkeypatch.setattr(
            schema_executor,
            "create_profile_snapshot",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                ProfileSnapshotError("profile failed")
            ),
        )

    with pytest.raises(error_type) as error:
        execute(request)

    with DuckDBConnectionManager(request.target_database_path) as connection:
        after = reliability.create_table_state_identity(
            connection,
            request.proposal.table_name,
        )
    assert after == before
    assert error.value.failure_stage == "in_target_transaction"
    assert error.value.mutation_state == "rolled_back"
    assert error.value.reconciliation_action == "retry_same_approval"


@pytest.mark.component
def test_schema_recovery_rolls_back_table_state_builder_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Final state calculation failure after replacement also rolls back."""

    execute, error_type = _executor_api()
    request = _request(tmp_path, target_state="before")
    original_create_state = schema_executor.create_table_state_identity
    target_state_calls = 0

    def fail_final_state(
        connection: duckdb.DuckDBPyConnection,
        table_name: str,
    ) -> TableStateIdentity:
        nonlocal target_state_calls
        target_state_calls += 1
        if target_state_calls == 2:
            raise TableStateIdentityError("final state failed")
        return original_create_state(connection, table_name)

    with DuckDBConnectionManager(request.target_database_path) as connection:
        before = reliability.create_table_state_identity(
            connection,
            request.proposal.table_name,
        )
    monkeypatch.setattr(
        schema_executor,
        "create_table_state_identity",
        fail_final_state,
    )

    with pytest.raises(error_type) as error:
        execute(request)

    with DuckDBConnectionManager(request.target_database_path) as connection:
        after = reliability.create_table_state_identity(
            connection,
            request.proposal.table_name,
        )
    assert after == before
    assert error.value.failure_stage == "in_target_transaction"
    assert error.value.mutation_state == "rolled_back"
    assert error.value.reconciliation_action == "retry_same_approval"


@pytest.mark.integration
def test_schema_recovery_serializes_with_hmda_partition_writer(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """HMDA writer waits for recovery commit, then rechecks and stale-fails."""

    execute, _ = _executor_api()
    hmda_csv_path = _write_hmda_csv(tmp_path)
    request, expected_partition = _hmda_request(tmp_path, hmda_csv_path)
    replacement_path = tmp_path / "year_2025_replacement.csv"
    replacement_path.write_text(
        hmda_csv_path.read_text(encoding="utf-8").replace("120,CA", "121,CA"),
        encoding="utf-8",
    )
    target_checked = Event()
    release_recovery = Event()
    writer_attempted = Event()
    original_create_state = schema_executor.create_table_state_identity
    first_target_check = True

    def pause_after_target_check(
        connection: duckdb.DuckDBPyConnection,
        table_name: str,
    ) -> TableStateIdentity:
        nonlocal first_target_check
        state = original_create_state(connection, table_name)
        if first_target_check:
            first_target_check = False
            target_checked.set()
            assert release_recovery.wait(timeout=2)
        return state

    @contextmanager
    def observe_partition_lock(database_path: str | Path | None):
        writer_attempted.set()
        with database_mutation_lock(database_path):
            yield

    monkeypatch.setattr(
        schema_executor,
        "create_table_state_identity",
        pause_after_target_check,
    )
    monkeypatch.setattr(
        partition_module,
        "database_mutation_lock",
        observe_partition_lock,
    )
    recovery_errors: list[BaseException] = []
    writer_errors: list[BaseException] = []

    def recover() -> None:
        try:
            execute(request)
        except BaseException as exc:
            recovery_errors.append(exc)

    def replace_partition() -> None:
        try:
            with DuckDBConnectionManager(request.target_database_path) as connection:
                load_hmda_loans_partition(
                    connection,
                    [replacement_path],
                    2025,
                    expected_identity=expected_partition,
                )
        except BaseException as exc:
            writer_errors.append(exc)

    recovery_thread = Thread(target=recover, daemon=True)
    writer_thread = Thread(target=replace_partition, daemon=True)
    recovery_thread.start()
    assert target_checked.wait(timeout=2)
    writer_thread.start()
    assert writer_attempted.wait(timeout=2)
    assert writer_thread.is_alive()

    release_recovery.set()
    recovery_thread.join(timeout=3)
    writer_thread.join(timeout=3)

    assert not recovery_thread.is_alive()
    assert not writer_thread.is_alive()
    assert recovery_errors == []
    assert len(writer_errors) == 1
    assert isinstance(writer_errors[0], HMDAStalePartitionError)
    with DuckDBConnectionManager(request.target_database_path) as connection:
        assert (
            reliability.create_table_state_identity(
                connection,
                request.proposal.table_name,
            )
            == request.proposal.expected_after_state
        )


@pytest.mark.integration
def test_dbt_lock_blocks_schema_recovery_target_state_check(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Recovery cannot inspect the target while dbt holds the shared mutation lock."""

    execute, _ = _executor_api()
    request = _request(tmp_path, target_state="before")
    dbt_holds_lock = Event()
    release_dbt = Event()
    recovery_attempted = Event()
    target_checked = Event()
    original_recovery_lock = schema_executor.database_mutation_lock
    original_create_state = schema_executor.create_table_state_identity

    def run_dbt(command: list[str], **kwargs: object) -> CompletedProcess[str]:
        dbt_holds_lock.set()
        assert release_dbt.wait(timeout=2)
        run_target = Path(command[-1])
        run_target.joinpath("manifest.json").write_text("{}", encoding="utf-8")
        run_target.joinpath("run_results.json").write_text("{}", encoding="utf-8")
        return CompletedProcess(command, 0, "", "")

    @contextmanager
    def observe_recovery_lock(database_path: str | Path | None):
        recovery_attempted.set()
        with original_recovery_lock(database_path):
            yield

    def observe_target_state(
        connection: duckdb.DuckDBPyConnection,
        table_name: str,
    ) -> TableStateIdentity:
        target_checked.set()
        return original_create_state(connection, table_name)

    monkeypatch.setattr(subprocess, "run", run_dbt)
    monkeypatch.setattr(
        schema_executor,
        "database_mutation_lock",
        observe_recovery_lock,
    )
    monkeypatch.setattr(
        schema_executor,
        "create_table_state_identity",
        observe_target_state,
    )
    dbt_errors: list[BaseException] = []
    recovery_errors: list[BaseException] = []

    def build_dbt() -> None:
        try:
            data_runner.run_dbt_build(
                DataOperationRequest(
                    database_path=request.target_database_path,
                    dbt_run_target_path=tmp_path / "dbt-runs",
                )
            )
        except BaseException as exc:
            dbt_errors.append(exc)

    def recover() -> None:
        try:
            execute(request)
        except BaseException as exc:
            recovery_errors.append(exc)

    dbt_thread = Thread(target=build_dbt, daemon=True)
    recovery_thread = Thread(target=recover, daemon=True)
    dbt_thread.start()
    assert dbt_holds_lock.wait(timeout=2)
    recovery_thread.start()
    assert recovery_attempted.wait(timeout=2)
    assert not target_checked.is_set()

    release_dbt.set()
    dbt_thread.join(timeout=3)
    recovery_thread.join(timeout=3)

    assert not dbt_thread.is_alive()
    assert not recovery_thread.is_alive()
    assert dbt_errors == []
    assert recovery_errors == []
    assert target_checked.is_set()


def _request(
    tmp_path: Path,
    *,
    target_state: str,
) -> ApprovedSchemaRecoveryRequest:
    candidate_path = tmp_path / "candidate.duckdb"
    target_path = tmp_path / "target.duckdb"
    with DuckDBConnectionManager(candidate_path) as connection:
        _create_table(connection, drifted=False)
        expected_after = reliability.create_table_state_identity(
            connection,
            "raw.hmda_loans",
        )
    with duckdb.connect(":memory:") as connection:
        _create_table(connection, drifted=True)
        approved_before = reliability.create_table_state_identity(
            connection,
            "raw.hmda_loans",
        )
    with DuckDBConnectionManager(target_path) as connection:
        _create_table(connection, drifted=target_state != "after")
        if target_state == "diverged":
            connection.execute(
                "UPDATE raw.hmda_loans SET income = income + 1 WHERE source_year = 2025"
            )
    proposal = SchemaRecoveryProposal(
        proposal_id="schema_recovery_2025",
        incident_id="inc_schema_drift_2025",
        observation_partition="2025",
        table_name="raw.hmda_loans",
        candidate_state=expected_after,
        approved_before_state=approved_before,
        expected_after_state=expected_after,
        validation_evidence_refs=("candidate-state", "dbt:candidate"),
        dbt_projection_id="dbt:candidate",
        target_actions=("replace_table", "rerun_profile_snapshot"),
    )
    approved_at = datetime(2026, 8, 16, 0, 0, tzinfo=UTC)
    approval = SchemaRecoveryApproval(
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
    return ApprovedSchemaRecoveryRequest(
        approval=approval,
        proposal=proposal,
        target_database_path=target_path,
        candidate_database_path=candidate_path,
        profile_request=ProfileSnapshotRequest(
            asset_name="raw.hmda_loans",
            table_name="raw.hmda_loans",
            partition_column="source_year",
            partition=2025,
            profile_columns=("loan_amount", "income"),
            observed_at=approved_at,
        ),
    )


def _hmda_request(
    tmp_path: Path,
    hmda_csv_path: Path,
) -> tuple[ApprovedSchemaRecoveryRequest, PartitionContentIdentity]:
    candidate_path = tmp_path / "candidate.duckdb"
    target_path = tmp_path / "target.duckdb"
    with DuckDBConnectionManager(candidate_path) as connection:
        load_hmda_loans(connection, [hmda_csv_path])
        expected_after = reliability.create_table_state_identity(
            connection,
            "raw.hmda_loans",
        )
    with DuckDBConnectionManager(target_path) as connection:
        load_hmda_loans(connection, [hmda_csv_path])
        connection.execute(
            "ALTER TABLE raw.hmda_loans ALTER COLUMN loan_amount TYPE VARCHAR"
        )
        connection.execute(
            "UPDATE raw.hmda_loans SET income = income + 1 WHERE source_year = 2025"
        )
        approved_before = reliability.create_table_state_identity(
            connection,
            "raw.hmda_loans",
        )
        expected_partition = partition_content_identity(
            connection,
            source_year=2025,
        )
    proposal = SchemaRecoveryProposal(
        proposal_id="schema_recovery_hmda_2025",
        incident_id="inc_schema_drift_hmda_2025",
        observation_partition="2025",
        table_name="raw.hmda_loans",
        candidate_state=expected_after,
        approved_before_state=approved_before,
        expected_after_state=expected_after,
        validation_evidence_refs=("candidate-state", "dbt:candidate"),
        dbt_projection_id="dbt:candidate",
        target_actions=("replace_table", "rerun_profile_snapshot"),
    )
    approved_at = datetime(2026, 8, 16, 0, 0, tzinfo=UTC)
    approval = SchemaRecoveryApproval(
        approval_id="approval_schema_drift_hmda_2025",
        incident_id=proposal.incident_id,
        status=ApprovalStatus.APPROVED,
        requested_by="data-platform",
        requested_at=approved_at,
        approved_by="data-owner",
        approved_at=approved_at,
        requested_actions=proposal.target_actions,
        recovery_proposal=proposal,
    )
    return (
        ApprovedSchemaRecoveryRequest(
            approval=approval,
            proposal=proposal,
            target_database_path=target_path,
            candidate_database_path=candidate_path,
            profile_request=ProfileSnapshotRequest(
                asset_name="raw.hmda_loans",
                table_name="raw.hmda_loans",
                partition_column="source_year",
                partition=2025,
                profile_columns=("loan_amount", "income"),
                observed_at=approved_at,
            ),
        ),
        expected_partition,
    )


def _create_table(
    connection: duckdb.DuckDBPyConnection,
    *,
    drifted: bool,
) -> None:
    loan_amount_type = "VARCHAR" if drifted else "INTEGER"
    connection.execute("CREATE SCHEMA raw")
    connection.execute(
        f"""
        CREATE TABLE raw.hmda_loans (
            source_year INTEGER,
            source_file_name VARCHAR,
            loan_amount {loan_amount_type},
            income INTEGER
        )
        """
    )
    connection.execute(
        """
        INSERT INTO raw.hmda_loans VALUES
            (2024, '2024.csv', 100, 10),
            (2025, '2025-a.csv', 200, 20),
            (2025, '2025-b.csv', 300, 30)
        """
    )


def _write_mismatched_candidate(tmp_path: Path) -> Path:
    artifact_path = tmp_path / "mismatched.parquet"
    with duckdb.connect(":memory:") as connection:
        _create_table(connection, drifted=False)
        connection.execute(
            "UPDATE raw.hmda_loans SET income = income + 1 WHERE source_year = 2025"
        )
        connection.execute(
            "COPY raw.hmda_loans TO ? (FORMAT PARQUET)",
            [str(artifact_path)],
        )
    return artifact_path


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
