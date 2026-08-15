"""Schema recovery complete candidate preflight tests."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

import duckdb
import pytest
from pydantic import ValidationError

import project_pivot.reliability as reliability
import project_pivot.reliability.recovery.schema_candidate as schema_candidate
from project_pivot.data_operations import DbtBuildResult
from project_pivot.data_platform.duckdb import DuckDBConnectionManager
from project_pivot.reliability import SchemaRecoveryCandidateError


def _preflight_api() -> tuple[Any, type[SchemaRecoveryCandidateError], type[Any]]:
    preflight = getattr(reliability, "preflight_schema_recovery_candidate", None)
    error_type = getattr(reliability, "SchemaRecoveryCandidateError", None)
    evidence_type = getattr(reliability, "SchemaRecoveryCandidateEvidence", None)
    assert preflight is not None, (
        "preflight_schema_recovery_candidate API가 필요합니다."
    )
    assert error_type is not None, "SchemaRecoveryCandidateError API가 필요합니다."
    assert evidence_type is not None, (
        "SchemaRecoveryCandidateEvidence API가 필요합니다."
    )
    return preflight, error_type, evidence_type


def _staging_api() -> tuple[Any, type[Any]]:
    stage_candidate = getattr(
        reliability,
        "stage_approved_schema_recovery_candidate",
        None,
    )
    staged_type = getattr(reliability, "StagedSchemaRecoveryCandidate", None)
    assert stage_candidate is not None, (
        "stage_approved_schema_recovery_candidate API가 필요합니다."
    )
    assert staged_type is not None, "StagedSchemaRecoveryCandidate API가 필요합니다."
    return stage_candidate, staged_type


@pytest.mark.component
@pytest.mark.parametrize(
    "invalid_candidate",
    ["schema", "content", "missing_population"],
)
def test_candidate_state_failure_blocks_approval_and_target_access(
    invalid_candidate: str,
    tmp_path: Path,
) -> None:
    """Incomplete or mismatched candidate fails before approval and target access."""

    preflight, error_type, _ = _preflight_api()
    target_path = tmp_path / "target.duckdb"
    approval_calls: list[object] = []
    with duckdb.connect(":memory:") as clean_connection:
        _create_candidate_table(clean_connection)
        expected_state = reliability.create_table_state_identity(
            clean_connection,
            "raw.hmda_loans",
        )
    with duckdb.connect(":memory:") as candidate_connection:
        _create_candidate_table(candidate_connection)
        if invalid_candidate == "schema":
            candidate_connection.execute(
                "ALTER TABLE raw.hmda_loans ALTER COLUMN loan_amount TYPE VARCHAR"
            )
        elif invalid_candidate == "content":
            candidate_connection.execute(
                "UPDATE raw.hmda_loans SET loan_amount = loan_amount + 1 "
                "WHERE source_year = 2025"
            )
        else:
            candidate_connection.execute(
                "DELETE FROM raw.hmda_loans WHERE source_year = 2024"
            )

        with pytest.raises(error_type) as error:
            preflight(
                candidate_connection,
                expected_after_state=expected_state,
                dbt_result=_dbt_result(tmp_path),
            )
            approval_calls.append(object())

    assert approval_calls == []
    assert not target_path.exists()
    if invalid_candidate == "missing_population":
        assert error.value.context["missing_source_years"] == [2024]


@pytest.mark.component
def test_candidate_dbt_failure_blocks_approval_and_target_access(
    tmp_path: Path,
) -> None:
    """Unsuccessful candidate dbt evidence is rejected before approval."""

    preflight, error_type, _ = _preflight_api()
    target_path = tmp_path / "target.duckdb"
    approval_calls: list[object] = []
    with duckdb.connect(":memory:") as candidate_connection:
        _create_candidate_table(candidate_connection)
        expected_state = reliability.create_table_state_identity(
            candidate_connection,
            "raw.hmda_loans",
        )

        with pytest.raises(error_type, match="dbt") as error:
            preflight(
                candidate_connection,
                expected_after_state=expected_state,
                dbt_result=_dbt_result(tmp_path, succeeded=False, return_code=1),
            )
            approval_calls.append(object())

    assert approval_calls == []
    assert not target_path.exists()
    assert error.value.context["return_code"] == 1


@pytest.mark.component
def test_complete_candidate_returns_immutable_approval_evidence(
    tmp_path: Path,
) -> None:
    """Exact complete state and successful dbt projection become proposal input."""

    preflight, _, evidence_type = _preflight_api()
    with duckdb.connect(":memory:") as candidate_connection:
        _create_candidate_table(candidate_connection)
        expected_state = reliability.create_table_state_identity(
            candidate_connection,
            "raw.hmda_loans",
        )

        evidence = preflight(
            candidate_connection,
            expected_after_state=expected_state,
            dbt_result=_dbt_result(tmp_path),
        )

    assert isinstance(evidence, evidence_type)
    assert evidence.candidate_state == expected_state
    assert evidence.dbt_projection_id == "sha256:candidate-dbt"
    assert evidence.validation_evidence_refs[-1] == evidence.dbt_projection_id
    with pytest.raises(ValidationError):
        evidence.dbt_projection_id = "changed"


@pytest.mark.component
def test_staging_rejects_candidate_changed_after_approval(tmp_path: Path) -> None:
    """Approval 뒤 candidate state가 바뀌면 artifact를 만들지 않는다."""

    stage_candidate, _ = _staging_api()
    candidate_path = tmp_path / "candidate.duckdb"
    staging_directory = tmp_path / "staging"
    with DuckDBConnectionManager(candidate_path) as connection:
        _create_candidate_table(connection)
        approved_state = reliability.create_table_state_identity(
            connection,
            "raw.hmda_loans",
        )
        connection.execute(
            "UPDATE raw.hmda_loans SET loan_amount = loan_amount + 1 "
            "WHERE source_year = 2025"
        )

    with pytest.raises(
        reliability.SchemaRecoveryCandidateError,
        match="approved candidate",
    ):
        stage_candidate(
            candidate_database_path=candidate_path,
            approved_candidate_state=approved_state,
            staging_directory=staging_directory,
        )

    assert not staging_directory.exists()


@pytest.mark.component
def test_staging_rejects_candidate_changed_during_export(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """State check와 export 사이 direct change는 staged mismatch로 차단된다."""

    stage_candidate, _ = _staging_api()
    candidate_path = tmp_path / "candidate.duckdb"
    staging_directory = tmp_path / "staging"
    with DuckDBConnectionManager(candidate_path) as connection:
        _create_candidate_table(connection)
        approved_state = reliability.create_table_state_identity(
            connection,
            "raw.hmda_loans",
        )

    original_create_state = schema_candidate.create_table_state_identity
    candidate_checked = threading.Event()
    writer_finished = threading.Event()
    writer_errors: list[BaseException] = []
    first_check = True

    def pause_after_candidate_check(
        connection: duckdb.DuckDBPyConnection,
        table_name: str,
    ) -> reliability.TableStateIdentity:
        nonlocal first_check
        state = original_create_state(connection, table_name)
        if first_check:
            first_check = False
            candidate_checked.set()
            assert writer_finished.wait(timeout=2)
        return state

    def change_candidate() -> None:
        try:
            assert candidate_checked.wait(timeout=2)
            with DuckDBConnectionManager(candidate_path) as connection:
                connection.execute(
                    "UPDATE raw.hmda_loans SET loan_amount = loan_amount + 1 "
                    "WHERE source_year = 2025"
                )
        except BaseException as exc:
            writer_errors.append(exc)
        finally:
            writer_finished.set()

    monkeypatch.setattr(
        schema_candidate,
        "create_table_state_identity",
        pause_after_candidate_check,
    )
    writer = threading.Thread(target=change_candidate)
    writer.start()
    try:
        with pytest.raises(
            reliability.SchemaRecoveryCandidateError,
            match="staged candidate",
        ):
            stage_candidate(
                candidate_database_path=candidate_path,
                approved_candidate_state=approved_state,
                staging_directory=staging_directory,
            )
    finally:
        writer.join()

    assert writer_errors == []
    assert not staging_directory.joinpath("approved-candidate.parquet").exists()


@pytest.mark.component
def test_staging_returns_exact_immutable_parquet(tmp_path: Path) -> None:
    """Approved candidate는 exact state가 확인된 immutable Parquet가 된다."""

    stage_candidate, staged_type = _staging_api()
    candidate_path = tmp_path / "candidate.duckdb"
    staging_directory = tmp_path / "staging"
    with DuckDBConnectionManager(candidate_path) as connection:
        _create_candidate_table(connection)
        approved_state = reliability.create_table_state_identity(
            connection,
            "raw.hmda_loans",
        )

    staged = stage_candidate(
        candidate_database_path=candidate_path,
        approved_candidate_state=approved_state,
        staging_directory=staging_directory,
    )

    assert isinstance(staged, staged_type)
    assert staged.candidate_state == approved_state
    assert staged.artifact_path.is_file()
    with pytest.raises(ValidationError):
        staged.artifact_path = tmp_path / "changed.parquet"


def _dbt_result(
    tmp_path: Path,
    *,
    succeeded: bool = True,
    return_code: int = 0,
) -> DbtBuildResult:
    return DbtBuildResult(
        command=["dbt", "build"],
        return_code=return_code,
        manifest_path=tmp_path / "manifest.json",
        run_results_path=tmp_path / "run_results.json",
        projection_id="sha256:candidate-dbt",
        succeeded=succeeded,
    )


def _create_candidate_table(connection: duckdb.DuckDBPyConnection) -> None:
    connection.execute("CREATE SCHEMA raw")
    connection.execute(
        """
        CREATE TABLE raw.hmda_loans (
            source_year INTEGER,
            source_file_name VARCHAR,
            loan_amount INTEGER
        )
        """
    )
    connection.execute(
        """
        INSERT INTO raw.hmda_loans VALUES
            (2024, '2024.csv', 100),
            (2025, '2025-a.csv', 200),
            (2025, '2025-b.csv', 300)
        """
    )
