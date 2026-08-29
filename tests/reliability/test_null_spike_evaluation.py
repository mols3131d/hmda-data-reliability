"""Null-spike vertical-slice evaluator integration tests.

Contract:
    - A controlled target-column null spike preserves rows and is the only incident.
    - Exact approval restores clean content, null rate, and downstream evidence.
    - Ambiguous incidents fail with cardinality evidence before approval or mutation.
    - Candidate, replay, gate, and dbt failures return mutation-aware evidence.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Never

import duckdb
import pytest

import hmda_reliability.data_operations as data_operations
import hmda_reliability.reliability.evaluation.null_spike as null_spike_evaluation
import hmda_reliability.reliability.recovery.executor as recovery_executor
from hmda_reliability.data_operations import (
    DataOperationRequest,
    DbtBuildResult,
    LifecycleResult,
    promote_dbt_artifacts,
)
from hmda_reliability.data_operations.errors import DataOperationError
from hmda_reliability.data_platform.artifacts import (
    ArtifactProjectionLockError,
    artifact_projection_id,
)
from hmda_reliability.data_platform.duckdb import DuckDBConnectionManager
from hmda_reliability.hmda_data import (
    PartitionContentIdentity,
    partition_content_identity,
)
from hmda_reliability.hmda_data.errors import HMDAStalePartitionError
from hmda_reliability.reliability import (
    Approval,
    ApprovalStatus,
    BackfillValidationResult,
    ProfileSnapshot,
    RecoveryProposal,
)
from hmda_reliability.reliability.errors import (
    ApprovalGateError,
    BackfillValidationError,
    ProfileSnapshotError,
)
from hmda_reliability.reliability.profiling import ProfileSnapshotRequest


@pytest.mark.integration
def test_null_spike_vertical_slice_preserves_rows_and_selects_target_incident(
    tmp_path: Path,
) -> None:
    """A single profiled target column produces only its null-spike incident."""

    source_path, request = _null_spike_fixture(tmp_path)
    proposals: list[RecoveryProposal] = []

    def approve(proposal: RecoveryProposal) -> Approval:
        proposals.append(proposal)
        assert proposal.approved_before_identity.row_count == 10
        assert proposal.expected_after_identity.row_count == 10
        return _approved(proposal)

    result = _evaluate_null_spike(
        request=request,
        source_paths=(source_path,),
        workspace=tmp_path / "run",
        target_column="income",
        null_fraction=0.2,
        approve=approve,
        validate_candidate=lambda _request: "sha256:candidate",
        validate_target=lambda _request: "sha256:target",
    )

    assert request.profile_columns == ("income",)
    assert result.clean_case.detected_incident_types == []
    assert result.null_spike_case.detected_incident_types == ["null_spike"]
    assert "volume_drop" not in result.null_spike_case.detected_incident_types
    assert len(proposals) == 1


@pytest.mark.integration
def test_null_spike_vertical_slice_recovers_approved_clean_partition(
    tmp_path: Path,
) -> None:
    """Approved clean content restores identity, null rate, and dbt evidence."""

    source_path, request = _null_spike_fixture(tmp_path)
    proposals: list[RecoveryProposal] = []
    approvals: list[Approval] = []

    def approve(proposal: RecoveryProposal) -> Approval:
        approval = _approved(proposal)
        proposals.append(proposal)
        approvals.append(approval)
        return approval

    result = _evaluate_null_spike(
        request=request,
        source_paths=(source_path,),
        workspace=tmp_path / "run",
        target_column="income",
        null_fraction=0.2,
        approve=approve,
        validate_candidate=lambda _request: "sha256:candidate",
        validate_target=lambda _request: "sha256:target",
    )

    assert len(proposals) == 1
    assert len(approvals) == 1
    assert proposals[0].candidate_identity == result.fixture_identity
    assert proposals[0].candidate_identity == result.expected_recovery_identity
    assert proposals[0].expected_after_identity == result.fixture_identity
    assert approvals[0].recovery_proposal == proposals[0]
    assert result.recovery is not None
    assert result.recovery.approval_id == approvals[0].approval_id
    assert result.recovery.mutation_state == "partition_changed"
    assert result.recovery.validation_passed is True
    assert result.recovery.actual_identity == result.recovery.expected_after_identity
    assert result.recovery.profile_snapshot.null_rates["income"] == 0.0
    assert result.post_recovery_case.detected_incident_types == []
    assert result.target_dbt_projection_id == "sha256:target"


@pytest.mark.integration
@pytest.mark.parametrize("existing_database", ["target", "clean", "candidate"])
def test_null_spike_vertical_slice_rejects_existing_evaluation_database(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    existing_database: str,
) -> None:
    """Existing evaluation databases are rejected before load or callbacks."""

    source_path, request = _null_spike_fixture(tmp_path)
    workspace = tmp_path / "run"
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
    original_content = existing_path.read_bytes()
    original_workspace_entries = (
        {path.name for path in workspace.iterdir()} if workspace.exists() else None
    )

    load_calls: list[Path] = []
    callback_calls: list[str] = []
    original_load = null_spike_evaluation.load_hmda_loans_partition

    def track_load(
        connection: duckdb.DuckDBPyConnection,
        source_paths: Sequence[str | Path],
        source_year: int,
        *,
        source_file: str | None = None,
        table_name: str = "raw.hmda_loans",
        expected_identity: PartitionContentIdentity | None = None,
        preserve_source_metadata: bool = False,
    ) -> int:
        database_row = connection.execute("PRAGMA database_list").fetchone()
        assert database_row is not None
        load_calls.append(Path(database_row[2]))
        return original_load(
            connection,
            source_paths,
            source_year,
            source_file=source_file,
            table_name=table_name,
            expected_identity=expected_identity,
            preserve_source_metadata=preserve_source_metadata,
        )

    def approve(proposal: RecoveryProposal) -> Approval:
        callback_calls.append("approve")
        return _approved(proposal)

    def validate_candidate(_request: DataOperationRequest) -> str:
        callback_calls.append("validate_candidate")
        return "sha256:candidate"

    def validate_target(_request: DataOperationRequest) -> str:
        callback_calls.append("validate_target")
        return "sha256:target"

    monkeypatch.setattr(
        null_spike_evaluation,
        "load_hmda_loans_partition",
        track_load,
    )

    try:
        result = _evaluate_null_spike(
            request=request,
            source_paths=(source_path,),
            workspace=workspace,
            target_column="income",
            null_fraction=0.2,
            approve=approve,
            validate_candidate=validate_candidate,
            validate_target=validate_target,
        )
    except ValueError:
        pass
    else:
        assert result.post_recovery_case.failure_stage == "before_target_mutation"
        assert result.post_recovery_case.target_mutated is False

    assert load_calls == []
    assert callback_calls == []
    assert existing_path.read_bytes() == original_content
    if original_workspace_entries is None:
        assert not workspace.exists()
    else:
        assert {path.name for path in workspace.iterdir()} == original_workspace_entries


@pytest.mark.integration
@pytest.mark.parametrize(
    ("left_name", "right_name"),
    [
        pytest.param("target", "clean", id="target-clean"),
        pytest.param("target", "candidate", id="target-candidate"),
        pytest.param("clean", "candidate", id="clean-candidate"),
    ],
)
def test_null_spike_vertical_slice_rejects_aliased_evaluation_database_paths(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    left_name: str,
    right_name: str,
) -> None:
    """Pairwise physical aliases are rejected before any evaluation side effect."""

    source_path, request = _null_spike_fixture(tmp_path)
    workspace = tmp_path / "run"
    sentinel_path = tmp_path / "sentinel.txt"
    sentinel_path.write_text("preserve", encoding="utf-8")
    database_paths = {
        "target": workspace / "target.duckdb",
        "clean": workspace / "clean.duckdb",
        "candidate": workspace / "candidate.duckdb",
    }
    if left_name == "target":
        database_paths["target"] = database_paths[right_name]
    else:
        workspace.mkdir()
        database_paths["candidate"].symlink_to(database_paths["clean"].name)
    request = request.model_copy(update={"database_path": database_paths["target"]})

    assert database_paths[left_name].resolve(strict=False) == (
        database_paths[right_name].resolve(strict=False)
    )
    assert all(not path.exists() for path in database_paths.values())

    source_content = source_path.read_bytes()
    manifest_content = request.dbt_manifest_path.read_bytes()
    run_results_content = request.dbt_run_results_path.read_bytes()
    original_workspace_entries = (
        {path.name for path in workspace.iterdir()} if workspace.exists() else None
    )
    original_symlink_targets = (
        {
            path.name: path.readlink()
            for path in workspace.iterdir()
            if path.is_symlink()
        }
        if workspace.exists()
        else {}
    )
    database_calls: list[str] = []
    load_calls: list[None] = []
    synthetic_calls: list[str] = []
    callback_calls: list[str] = []

    class EvaluationSideEffect(RuntimeError):
        pass

    def track_database(*args: object, **kwargs: object) -> None:
        database_calls.append("database")
        raise EvaluationSideEffect

    def track_load(*args: object, **kwargs: object) -> int:
        load_calls.append(None)
        raise EvaluationSideEffect

    def track_null_spike(*args: object, **kwargs: object) -> Path:
        synthetic_calls.append("null_spike")
        raise EvaluationSideEffect

    def track_materialize(*args: object, **kwargs: object) -> Path:
        synthetic_calls.append("materialize")
        raise EvaluationSideEffect

    def approve(proposal: RecoveryProposal) -> Approval:
        callback_calls.append("approve")
        raise EvaluationSideEffect

    def validate_candidate(_request: DataOperationRequest) -> str:
        callback_calls.append("validate_candidate")
        raise EvaluationSideEffect

    def validate_target(_request: DataOperationRequest) -> str:
        callback_calls.append("validate_target")
        raise EvaluationSideEffect

    monkeypatch.setattr(
        null_spike_evaluation,
        "DuckDBConnectionManager",
        track_database,
    )
    monkeypatch.setattr(
        null_spike_evaluation,
        "load_hmda_loans_partition",
        track_load,
    )
    monkeypatch.setattr(null_spike_evaluation, "null_spike", track_null_spike)
    monkeypatch.setattr(
        null_spike_evaluation,
        "_materialize_defect_source",
        track_materialize,
    )

    rejected = False
    try:
        _evaluate_null_spike(
            request=request,
            source_paths=(source_path,),
            workspace=workspace,
            target_column="income",
            null_fraction=0.2,
            approve=approve,
            validate_candidate=validate_candidate,
            validate_target=validate_target,
        )
    except ValueError:
        rejected = True
    except EvaluationSideEffect:
        pass

    violations = []
    if not rejected:
        violations.append("aliased database paths were not rejected")
    if database_calls:
        violations.append("database workspace was opened")
    if load_calls:
        violations.append("source load was invoked")
    if synthetic_calls:
        violations.append("synthetic materialization was invoked")
    if callback_calls:
        violations.append(f"callbacks were invoked: {callback_calls}")
    if original_workspace_entries is None:
        if workspace.exists():
            violations.append("workspace directory was created")
    elif {path.name for path in workspace.iterdir()} != original_workspace_entries:
        violations.append("workspace entries changed")
    if (
        workspace.exists()
        and {
            path.name: path.readlink()
            for path in workspace.iterdir()
            if path.is_symlink()
        }
        != original_symlink_targets
    ):
        violations.append("workspace aliases changed")
    if sentinel_path.read_text(encoding="utf-8") != "preserve":
        violations.append("unrelated sentinel changed")
    if source_path.read_bytes() != source_content:
        violations.append("source content changed")
    if request.dbt_manifest_path.read_bytes() != manifest_content:
        violations.append("manifest artifact changed")
    if request.dbt_run_results_path.read_bytes() != run_results_content:
        violations.append("run-results artifact changed")
    if any(path.exists() for path in database_paths.values()):
        violations.append("evaluation database was created")

    assert violations == []


@pytest.mark.integration
@pytest.mark.parametrize("dangling_database", ["target", "clean", "candidate"])
def test_null_spike_vertical_slice_rejects_dangling_database_symlink(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    dangling_database: str,
) -> None:
    """A dangling database symlink is an existing path with no side effects."""

    source_path, request = _null_spike_fixture(tmp_path)
    workspace = tmp_path / "run"
    database_paths = {
        "target": request.database_path,
        "clean": workspace / "clean.duckdb",
        "candidate": workspace / "candidate.duckdb",
    }
    dangling_path = database_paths[dangling_database]
    dangling_path.parent.mkdir(parents=True, exist_ok=True)
    unrelated_target = tmp_path / "unrelated" / f"{dangling_database}.duckdb"
    dangling_path.symlink_to(unrelated_target)

    assert dangling_path.is_symlink()
    assert not dangling_path.exists()
    assert unrelated_target not in {
        path.resolve(strict=False)
        for name, path in database_paths.items()
        if name != dangling_database
    }

    source_content = source_path.read_bytes()
    manifest_content = request.dbt_manifest_path.read_bytes()
    run_results_content = request.dbt_run_results_path.read_bytes()
    original_workspace_entries = (
        {path.name for path in workspace.iterdir()} if workspace.exists() else None
    )
    original_link_text = dangling_path.readlink()
    side_effects: list[str] = []

    class EvaluationSideEffect(RuntimeError):
        pass

    def fail_side_effect(*args: object, **kwargs: object) -> Never:
        side_effects.append("evaluation")
        raise EvaluationSideEffect

    monkeypatch.setattr(
        null_spike_evaluation,
        "DuckDBConnectionManager",
        fail_side_effect,
    )
    monkeypatch.setattr(
        null_spike_evaluation,
        "load_hmda_loans_partition",
        fail_side_effect,
    )
    monkeypatch.setattr(null_spike_evaluation, "null_spike", fail_side_effect)
    monkeypatch.setattr(
        null_spike_evaluation,
        "_materialize_defect_source",
        fail_side_effect,
    )

    rejected = False
    try:
        _evaluate_null_spike(
            request=request,
            source_paths=(source_path,),
            workspace=workspace,
            target_column="income",
            null_fraction=0.2,
            approve=fail_side_effect,
            validate_candidate=fail_side_effect,
            validate_target=fail_side_effect,
        )
    except ValueError:
        rejected = True
    except EvaluationSideEffect:
        pass

    assert rejected, "dangling database symlink must be rejected as existing"
    assert side_effects == []
    assert dangling_path.is_symlink()
    assert dangling_path.readlink() == original_link_text
    assert not unrelated_target.exists()
    assert source_path.read_bytes() == source_content
    assert request.dbt_manifest_path.read_bytes() == manifest_content
    assert request.dbt_run_results_path.read_bytes() == run_results_content
    if original_workspace_entries is None:
        assert not workspace.exists()
    else:
        assert {path.name for path in workspace.iterdir()} == original_workspace_entries
    assert all(
        path == dangling_path or not path.exists() for path in database_paths.values()
    )


@pytest.mark.integration
def test_null_spike_success_records_exact_null_rate_evidence(tmp_path: Path) -> None:
    """Success evidence independently records baseline, recovery, and replay rates."""

    source_path, request = _null_spike_fixture(tmp_path)

    result = _evaluate_null_spike(
        request=request,
        source_paths=(source_path,),
        workspace=tmp_path / "run",
        target_column="income",
        null_fraction=0.2,
        approve=_approved,
        validate_candidate=lambda _request: "sha256:candidate",
        validate_target=lambda _request: "sha256:target",
    )

    assert {
        "baseline-null-rate:income:0.0",
        "recovery-null-rate:income:0.0",
        "replay-null-rate:income:0.0",
    } <= set(result.post_recovery_case.evidence_refs)


@pytest.mark.integration
@pytest.mark.parametrize(
    ("failure_kind", "expected_validation", "expected_action"),
    [
        pytest.param(
            "content_validation",
            False,
            "request_new_validation_and_approval",
            id="content-validation",
        ),
        pytest.param("null_rate", True, "resume_verification", id="null-rate"),
    ],
)
def test_null_spike_failed_recovery_quality_stops_before_target_validation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    failure_kind: str,
    expected_validation: bool,
    expected_action: str,
) -> None:
    """Failed content or null-rate acceptance returns post-mutation evidence."""

    source_path, request = _null_spike_fixture(tmp_path)
    original_recovery = null_spike_evaluation.execute_approved_backfill
    recovery_calls = 0
    first_recovery: BackfillValidationResult | None = None

    def fail_first_recovery(connection, recovery_request):
        nonlocal recovery_calls, first_recovery
        recovery_calls += 1
        recovery = original_recovery(connection, recovery_request)
        if recovery_calls == 1:
            if failure_kind == "content_validation":
                recovery = recovery.model_copy(update={"validation_passed": False})
            else:
                profile = recovery.profile_snapshot.model_copy(
                    update={"null_rates": {"income": 0.1}}
                )
                recovery = recovery.model_copy(update={"profile_snapshot": profile})
            first_recovery = recovery
        return recovery

    target_validation_calls: list[DataOperationRequest] = []

    def validate_target(target_request: DataOperationRequest) -> str:
        target_validation_calls.append(target_request)
        return "sha256:target"

    monkeypatch.setattr(
        null_spike_evaluation,
        "execute_approved_backfill",
        fail_first_recovery,
    )

    result = _evaluate_null_spike(
        request=request,
        source_paths=(source_path,),
        workspace=tmp_path / "run",
        target_column="income",
        null_fraction=0.2,
        approve=_approved,
        validate_candidate=lambda _request: "sha256:candidate",
        validate_target=validate_target,
    )

    assert first_recovery is not None
    assert recovery_calls == 1
    assert result.recovery == first_recovery
    assert result.recovery.validation_passed is expected_validation
    assert result.replay is None
    assert result.post_recovery_case.failure_stage == "after_partition_mutation"
    assert result.post_recovery_case.target_mutated is True
    assert result.post_recovery_case.reconciliation_action == expected_action
    assert target_validation_calls == []


@pytest.mark.integration
def test_null_spike_candidate_value_error_returns_structured_failure(
    tmp_path: Path,
) -> None:
    """Candidate ValueError preserves projection evidence without escaping."""

    source_path, request = _null_spike_fixture(tmp_path)
    initial_projection_id = artifact_projection_id(
        request.dbt_manifest_path,
        request.dbt_run_results_path,
    )
    callback_calls: list[str] = []

    def fail_candidate(_request: DataOperationRequest) -> str:
        callback_calls.append("validate_candidate")
        raise ValueError("candidate validation rejected")

    def approve(proposal: RecoveryProposal) -> Approval:
        callback_calls.append("approve")
        return _approved(proposal)

    def validate_target(_request: DataOperationRequest) -> str:
        callback_calls.append("validate_target")
        return "sha256:target"

    try:
        result = _evaluate_null_spike(
            request=request,
            source_paths=(source_path,),
            workspace=tmp_path / "run",
            target_column="income",
            null_fraction=0.2,
            approve=approve,
            validate_candidate=fail_candidate,
            validate_target=validate_target,
        )
    except ValueError:
        pytest.fail(
            "candidate ValueError must return structured pre-mutation evidence",
            pytrace=False,
        )

    assert callback_calls == ["validate_candidate"]
    assert result.recovery is None
    assert result.replay is None
    assert result.candidate_dbt_projection_id is None
    assert result.post_recovery_case.case_name == "candidate_validation_failure"
    assert result.post_recovery_case.failure_stage == "before_target_mutation"
    assert result.post_recovery_case.target_mutated is False
    assert result.post_recovery_case.artifact_projection_ids == [initial_projection_id]
    assert any(
        "ValueError" in evidence for evidence in result.post_recovery_case.evidence_refs
    )


@pytest.mark.integration
@pytest.mark.parametrize(
    ("detected_incident_ids", "detected_incident_types"),
    [
        pytest.param([], [], id="zero"),
        pytest.param(
            ["inc_null_spike", "inc_volume_drop"],
            ["null_spike", "volume_drop"],
            id="multiple",
        ),
        pytest.param(
            ["inc_schema_drift"],
            ["schema_drift"],
            id="unrelated",
        ),
    ],
)
def test_null_spike_vertical_slice_rejects_ambiguous_incidents_before_mutation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    detected_incident_ids: list[str],
    detected_incident_types: list[str],
) -> None:
    """Zero, multiple, or unrelated incidents never reach approval or recovery."""

    source_path, request = _null_spike_fixture(tmp_path)
    target_identity = None

    def lifecycle_stub(
        lifecycle_request: DataOperationRequest,
        _baseline: object,
    ) -> LifecycleResult:
        nonlocal target_identity
        if lifecycle_request.database_path.name == "clean.duckdb":
            return LifecycleResult(
                metadata_row_count=10,
                baseline_row_count=10,
                current_row_count=10,
            )
        with DuckDBConnectionManager(
            lifecycle_request.database_path,
            read_only=True,
        ) as connection:
            target_identity = partition_content_identity(
                connection,
                table_name=lifecycle_request.raw_table_name,
                source_year=lifecycle_request.source_year,
                source_file=lifecycle_request.source_file,
            )
        return LifecycleResult(
            metadata_row_count=10,
            baseline_row_count=10,
            current_row_count=10,
            detected_incident_ids=detected_incident_ids,
            detected_incident_types=detected_incident_types,
            evidence_refs=[
                f"incident:{incident_id}" for incident_id in detected_incident_ids
            ],
            target_content_identity=target_identity,
        )

    monkeypatch.setattr(data_operations, "run_incident_lifecycle", lifecycle_stub)
    approval_calls: list[RecoveryProposal] = []
    candidate_validation_calls: list[DataOperationRequest] = []

    def approve(proposal: RecoveryProposal) -> Approval:
        approval_calls.append(proposal)
        return _approved(proposal)

    def validate_candidate(candidate_request: DataOperationRequest) -> str:
        candidate_validation_calls.append(candidate_request)
        return "sha256:candidate"

    result = _evaluate_null_spike(
        request=request,
        source_paths=(source_path,),
        workspace=tmp_path / "run",
        target_column="income",
        null_fraction=0.2,
        approve=approve,
        validate_candidate=validate_candidate,
        validate_target=lambda _request: "sha256:target",
    )

    assert result.recovery is None
    assert result.post_recovery_case.failure_stage == "before_target_mutation"
    assert result.post_recovery_case.target_mutated is False
    assert result.post_recovery_case.detected_incident_types == detected_incident_types
    assert (
        f"incident-cardinality:{len(detected_incident_ids)}"
        in result.post_recovery_case.evidence_refs
    )
    assert candidate_validation_calls == []
    assert approval_calls == []
    assert target_identity is not None
    with DuckDBConnectionManager(request.database_path, read_only=True) as connection:
        assert (
            partition_content_identity(
                connection,
                table_name=request.raw_table_name,
                source_year=request.source_year,
                source_file=request.source_file,
            )
            == target_identity
        )


@pytest.mark.integration
@pytest.mark.parametrize(
    "invalid_target_state",
    [
        pytest.param("row_count", id="row-count"),
        pytest.param("null_rate_delta", id="null-rate-delta"),
    ],
)
def test_null_spike_vertical_slice_rejects_unachieved_controlled_defect(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    invalid_target_state: str,
) -> None:
    """Lifecycle incident labels cannot override the actual target profile state."""

    source_path, request = _null_spike_fixture(tmp_path, row_count=20)
    original_lifecycle = data_operations.run_incident_lifecycle
    lifecycle_count = 0

    def lifecycle_stub(
        lifecycle_request: DataOperationRequest,
        baseline: ProfileSnapshot,
    ) -> LifecycleResult:
        nonlocal lifecycle_count
        lifecycle_count += 1
        if lifecycle_count == 1:
            return original_lifecycle(lifecycle_request, baseline)
        with DuckDBConnectionManager(lifecycle_request.database_path) as connection:
            if invalid_target_state == "row_count":
                connection.execute("DELETE FROM raw.hmda_loans WHERE loan_amount = 0")
            else:
                connection.execute("UPDATE raw.hmda_loans SET income = 100")
                connection.execute(
                    "UPDATE raw.hmda_loans SET income = NULL WHERE loan_amount = 0"
                )
            target_identity = partition_content_identity(
                connection,
                table_name=lifecycle_request.raw_table_name,
                source_year=lifecycle_request.source_year,
                source_file=lifecycle_request.source_file,
            )
        return LifecycleResult(
            metadata_row_count=20,
            baseline_row_count=20,
            current_row_count=20,
            detected_incident_ids=["inc_null_spike"],
            detected_incident_types=["null_spike"],
            evidence_refs=["incident:inc_null_spike"],
            target_content_identity=target_identity,
        )

    monkeypatch.setattr(data_operations, "run_incident_lifecycle", lifecycle_stub)
    callback_calls: list[str] = []

    def fail_callback(*args: object, **kwargs: object) -> Never:
        callback_calls.append("callback")
        pytest.fail("unachieved controlled defect must stop before callbacks")

    result = _evaluate_null_spike(
        request=request,
        source_paths=(source_path,),
        workspace=tmp_path / "run",
        target_column="income",
        null_fraction=0.2,
        approve=fail_callback,
        validate_candidate=fail_callback,
        validate_target=fail_callback,
    )

    with DuckDBConnectionManager(request.database_path, read_only=True) as connection:
        observed = connection.execute(
            "SELECT count(*), avg(CASE WHEN income IS NULL THEN 1.0 ELSE 0.0 END) "
            "FROM raw.hmda_loans"
        ).fetchone()
    assert observed is not None
    actual_row_count, actual_null_rate = observed

    if invalid_target_state == "row_count":
        assert actual_row_count == 19
    else:
        assert actual_row_count == 20
        assert actual_null_rate == 0.05
    assert result.recovery is None
    assert result.post_recovery_case.failure_stage == "before_target_mutation"
    assert result.post_recovery_case.target_mutated is False
    assert callback_calls == []


@pytest.mark.integration
def test_null_spike_vertical_slice_rejects_residual_null_candidate_with_evidence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A below-threshold residual null still differs from the clean fixture."""

    source_path, request = _null_spike_fixture(tmp_path, row_count=20)
    residual_source = tmp_path / "residual_2025.csv"
    residual_source.write_text(
        "\n".join(
            [
                "activity_year,loan_purpose,action_taken,loan_amount,income,state_code,county_code",
                "2025,1,1,0,,CA,06001",
                *[f"2025,1,1,{index},100,CA,06001" for index in range(1, 20)],
            ]
        ),
        encoding="utf-8",
    )
    original_load = null_spike_evaluation.load_hmda_loans_partition
    load_count = 0
    candidate_identity: PartitionContentIdentity | None = None
    candidate_null_rate: float | None = None
    target_identity_before_recovery: PartitionContentIdentity | None = None

    def load_residual_candidate(
        connection: duckdb.DuckDBPyConnection,
        source_paths: Sequence[str | Path],
        source_year: int,
        *,
        source_file: str | None = None,
        table_name: str = "raw.hmda_loans",
        expected_identity: PartitionContentIdentity | None = None,
        preserve_source_metadata: bool = False,
    ) -> int:
        nonlocal load_count, candidate_identity, candidate_null_rate
        nonlocal target_identity_before_recovery
        load_count += 1
        selected_source_paths = (residual_source,) if load_count == 3 else source_paths
        row_count = original_load(
            connection,
            selected_source_paths,
            source_year,
            source_file=source_file,
            table_name=table_name,
            expected_identity=expected_identity,
            preserve_source_metadata=preserve_source_metadata,
        )
        if load_count in {2, 3}:
            observed_identity = partition_content_identity(
                connection,
                table_name=request.raw_table_name,
                source_year=request.source_year,
                source_file=request.source_file,
            )
            if load_count == 2:
                target_identity_before_recovery = observed_identity
            else:
                candidate_identity = observed_identity
        if load_count == 3:
            null_rate_row = connection.execute(
                "SELECT avg(CASE WHEN income IS NULL THEN 1.0 ELSE 0.0 END) "
                "FROM raw.hmda_loans"
            ).fetchone()
            assert null_rate_row is not None
            candidate_null_rate = null_rate_row[0]
        return row_count

    monkeypatch.setattr(
        null_spike_evaluation,
        "load_hmda_loans_partition",
        load_residual_candidate,
    )
    recovery_count = 0

    def accept_residual_candidate(
        _connection: duckdb.DuckDBPyConnection,
        recovery_request,
    ) -> BackfillValidationResult:
        nonlocal recovery_count
        recovery_count += 1
        assert candidate_identity is not None
        assert request.observed_at is not None
        return BackfillValidationResult(
            approval_id=recovery_request.approval.approval_id,
            incident_id=recovery_request.approval.incident_id,
            partition=str(recovery_request.source_year),
            row_count=candidate_identity.row_count,
            profile_snapshot=ProfileSnapshot(
                snapshot_id=f"residual-{recovery_count}",
                asset_name=request.asset_name,
                partition=str(request.source_year),
                observed_at=request.observed_at,
                row_count=candidate_identity.row_count,
                null_rates={"income": 0.05},
                schema_hash="residual",
                freshness_at=request.observed_at,
                freshness_status="measured",
            ),
            approved_before_identity=recovery_request.proposal.approved_before_identity,
            expected_after_identity=recovery_request.proposal.expected_after_identity,
            actual_identity=candidate_identity,
            mutation_state=(
                "partition_changed" if recovery_count == 1 else "already_recovered"
            ),
            reconciliation_action=(
                "overwrite_partition" if recovery_count == 1 else "resume_verification"
            ),
            validation_passed=False,
            executed_actions=["rerun_profile_snapshot"],
        )

    monkeypatch.setattr(
        null_spike_evaluation,
        "execute_approved_backfill",
        accept_residual_candidate,
    )
    approval_calls: list[RecoveryProposal] = []

    def approve(proposal: RecoveryProposal) -> Approval:
        approval_calls.append(proposal)
        return _approved(proposal)

    result = _evaluate_null_spike(
        request=request,
        source_paths=(source_path,),
        workspace=tmp_path / "run",
        target_column="income",
        null_fraction=0.2,
        approve=approve,
        validate_candidate=lambda _request: "sha256:candidate",
        validate_target=lambda _request: "sha256:target",
    )

    assert candidate_identity is not None
    assert candidate_null_rate == 0.05
    evidence = result.post_recovery_case.evidence_refs
    assert any(
        "candidate" in ref and candidate_identity.digest in ref for ref in evidence
    )
    assert any(
        "expected" in ref and result.expected_recovery_identity.digest in ref
        for ref in evidence
    )
    assert any(
        "candidate" in ref and "null-rate" in ref and "income" in ref and "0.05" in ref
        for ref in evidence
    )
    assert any(
        "baseline" in ref and "null-rate" in ref and "income" in ref and "0.0" in ref
        for ref in evidence
    )
    assert result.recovery is None
    assert result.replay is None
    assert result.post_recovery_case.case_name == "invalid_candidate"
    assert result.post_recovery_case.failure_stage == "before_target_mutation"
    assert result.post_recovery_case.target_mutated is False
    assert approval_calls == []
    assert target_identity_before_recovery is not None
    with DuckDBConnectionManager(request.database_path, read_only=True) as connection:
        assert (
            partition_content_identity(
                connection,
                table_name=request.raw_table_name,
                source_year=request.source_year,
                source_file=request.source_file,
            )
            == target_identity_before_recovery
        )


@pytest.mark.integration
def test_null_spike_vertical_slice_replay_is_stable(tmp_path: Path) -> None:
    """The same approved recovery resumes verification without another overwrite."""

    source_path, request = _null_spike_fixture(tmp_path)

    result = _evaluate_null_spike(
        request=request,
        source_paths=(source_path,),
        workspace=tmp_path / "run",
        target_column="income",
        null_fraction=0.2,
        approve=_approved,
        validate_candidate=lambda _request: "sha256:candidate",
        validate_target=lambda _request: "sha256:target",
    )

    assert result.recovery is not None
    assert result.recovery.mutation_state == "partition_changed"
    assert result.replay is not None
    assert result.replay.mutation_state == "already_recovered"
    assert result.replay.reconciliation_action == "resume_verification"
    assert result.replay.expected_after_identity == result.expected_recovery_identity
    assert result.replay.actual_identity == result.recovery.actual_identity
    assert result.replay.row_count == result.recovery.row_count
    assert (
        result.replay.profile_snapshot.null_rates["income"]
        == (result.recovery.profile_snapshot.null_rates["income"])
    )


@pytest.mark.integration
def test_null_spike_replay_profile_failure_preserves_first_recovery(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Replay profile failure retains the completed partition mutation evidence."""

    source_path, request = _null_spike_fixture(tmp_path)
    original_snapshot = recovery_executor.create_profile_snapshot
    snapshot_count = 0

    def fail_replay_snapshot(
        connection: duckdb.DuckDBPyConnection,
        profile_request: ProfileSnapshotRequest,
    ) -> ProfileSnapshot:
        nonlocal snapshot_count
        snapshot_count += 1
        if snapshot_count == 2:
            raise ProfileSnapshotError("replay profile failed")
        return original_snapshot(connection, profile_request)

    monkeypatch.setattr(
        recovery_executor,
        "create_profile_snapshot",
        fail_replay_snapshot,
    )

    try:
        result = _evaluate_null_spike(
            request=request,
            source_paths=(source_path,),
            workspace=tmp_path / "run",
            target_column="income",
            null_fraction=0.2,
            approve=_approved,
            validate_candidate=lambda _request: "sha256:candidate",
            validate_target=lambda _request: "sha256:target",
        )
    except BackfillValidationError:
        pytest.fail(
            "replay profile failure must return structured recovery evidence",
            pytrace=False,
        )

    assert result.recovery is not None
    assert result.recovery.mutation_state == "partition_changed"
    assert result.replay is None
    assert result.post_recovery_case.case_name == "replay_failure"
    assert result.post_recovery_case.failure_stage == "after_partition_mutation"
    assert result.post_recovery_case.target_mutated is True
    assert result.post_recovery_case.reconciliation_action == "resume_verification"


@pytest.mark.integration
def test_null_spike_post_recovery_lifecycle_failure_preserves_mutation_evidence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Post-recovery lifecycle failure returns structured canonical evidence."""

    source_path, request = _null_spike_fixture(tmp_path)
    initial_projection_id = artifact_projection_id(
        request.dbt_manifest_path,
        request.dbt_run_results_path,
    )
    original_lifecycle = data_operations.run_incident_lifecycle
    lifecycle_count = 0

    def fail_post_recovery_lifecycle(
        lifecycle_request: DataOperationRequest,
        baseline: ProfileSnapshot,
    ) -> LifecycleResult:
        nonlocal lifecycle_count
        lifecycle_count += 1
        if lifecycle_count == 3:
            raise DataOperationError("post-recovery lifecycle failed")
        return original_lifecycle(lifecycle_request, baseline)

    monkeypatch.setattr(
        data_operations,
        "run_incident_lifecycle",
        fail_post_recovery_lifecycle,
    )

    try:
        result = _evaluate_null_spike(
            request=request,
            source_paths=(source_path,),
            workspace=tmp_path / "run",
            target_column="income",
            null_fraction=0.2,
            approve=_approved,
            validate_candidate=lambda _request: "sha256:candidate",
            validate_target=lambda _request: "sha256:target",
        )
    except DataOperationError:
        pytest.fail(
            "post-recovery lifecycle domain failure must return structured evidence",
            pytrace=False,
        )

    assert lifecycle_count == 3
    assert result.recovery is not None
    assert result.recovery.mutation_state == "partition_changed"
    assert result.replay is not None
    assert result.replay.mutation_state == "already_recovered"
    assert result.post_recovery_case.failure_stage == "after_partition_mutation"
    assert result.post_recovery_case.target_mutated is True
    assert result.post_recovery_case.reconciliation_action == "resume_verification"
    assert result.post_recovery_case.artifact_projection_ids == [initial_projection_id]
    assert any(
        "DataOperationError" in evidence
        for evidence in result.post_recovery_case.evidence_refs
    )
    _assert_exact_null_rate_evidence(result.post_recovery_case.evidence_refs)


@pytest.mark.integration
def test_null_spike_post_recovery_artifact_lock_failure_preserves_evidence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Post-recovery artifact lock failure keeps completed recovery evidence."""

    source_path, request = _null_spike_fixture(tmp_path)
    initial_projection_id = artifact_projection_id(
        request.dbt_manifest_path,
        request.dbt_run_results_path,
    )
    original_lifecycle = data_operations.run_incident_lifecycle
    lifecycle_count = 0

    def fail_post_recovery_lifecycle(
        lifecycle_request: DataOperationRequest,
        baseline: ProfileSnapshot,
    ) -> LifecycleResult:
        nonlocal lifecycle_count
        lifecycle_count += 1
        if lifecycle_count == 3:
            raise ArtifactProjectionLockError("post-recovery artifact lock failed")
        return original_lifecycle(lifecycle_request, baseline)

    monkeypatch.setattr(
        data_operations,
        "run_incident_lifecycle",
        fail_post_recovery_lifecycle,
    )

    result = _evaluate_null_spike(
        request=request,
        source_paths=(source_path,),
        workspace=tmp_path / "run",
        target_column="income",
        null_fraction=0.2,
        approve=_approved,
        validate_candidate=lambda _request: "sha256:candidate",
        validate_target=lambda _request: "sha256:target",
    )

    assert result.recovery is not None
    assert result.replay is not None
    assert result.post_recovery_case.failure_stage == "after_partition_mutation"
    assert result.post_recovery_case.target_mutated is True
    assert result.post_recovery_case.reconciliation_action == "resume_verification"
    assert result.post_recovery_case.artifact_projection_ids == [initial_projection_id]
    assert any(
        "ArtifactProjectionLockError" in evidence
        for evidence in result.post_recovery_case.evidence_refs
    )


@pytest.mark.integration
def test_null_spike_failed_replay_quality_preserves_replay_result(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A failed replay content validation remains available for reconciliation."""

    source_path, request = _null_spike_fixture(tmp_path)
    original_recovery = null_spike_evaluation.execute_approved_backfill
    recovery_count = 0
    failed_replay: BackfillValidationResult | None = None

    def fail_replay_validation(connection, recovery_request):
        nonlocal recovery_count, failed_replay
        recovery_count += 1
        recovery = original_recovery(connection, recovery_request)
        if recovery_count == 2:
            failed_replay = recovery.model_copy(update={"validation_passed": False})
            return failed_replay
        return recovery

    monkeypatch.setattr(
        null_spike_evaluation,
        "execute_approved_backfill",
        fail_replay_validation,
    )

    result = _evaluate_null_spike(
        request=request,
        source_paths=(source_path,),
        workspace=tmp_path / "run",
        target_column="income",
        null_fraction=0.2,
        approve=_approved,
        validate_candidate=lambda _request: "sha256:candidate",
        validate_target=lambda _request: "sha256:target",
    )

    assert failed_replay is not None
    assert result.recovery is not None
    assert result.recovery.mutation_state == "partition_changed"
    assert result.replay == failed_replay
    assert result.replay.validation_passed is False
    assert result.post_recovery_case.failure_stage == "after_partition_mutation"
    assert result.post_recovery_case.target_mutated is True
    assert result.post_recovery_case.reconciliation_action == (
        "request_new_validation_and_approval"
    )


@pytest.mark.integration
def test_null_spike_diverged_replay_requests_new_validation_and_approval(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A target changed after first recovery cannot reuse the old approval."""

    source_path, request = _null_spike_fixture(tmp_path)
    original_recovery = null_spike_evaluation.execute_approved_backfill
    recovery_count = 0

    def diverge_after_first_recovery(connection, recovery_request):
        nonlocal recovery_count
        recovery_count += 1
        recovery = original_recovery(connection, recovery_request)
        if recovery_count == 1:
            connection.execute("UPDATE raw.hmda_loans SET income = income + 1")
        return recovery

    monkeypatch.setattr(
        null_spike_evaluation,
        "execute_approved_backfill",
        diverge_after_first_recovery,
    )

    try:
        result = _evaluate_null_spike(
            request=request,
            source_paths=(source_path,),
            workspace=tmp_path / "run",
            target_column="income",
            null_fraction=0.2,
            approve=_approved,
            validate_candidate=lambda _request: "sha256:candidate",
            validate_target=lambda _request: "sha256:target",
        )
    except ApprovalGateError:
        pytest.fail(
            "diverged replay must return request_new_validation_and_approval evidence",
            pytrace=False,
        )

    assert result.recovery is not None
    assert result.recovery.mutation_state == "partition_changed"
    assert result.replay is None
    assert result.post_recovery_case.case_name == "replay_failure"
    assert result.post_recovery_case.failure_stage == "after_partition_mutation"
    assert result.post_recovery_case.target_mutated is True
    assert result.post_recovery_case.reconciliation_action == (
        "request_new_validation_and_approval"
    )


@pytest.mark.integration
@pytest.mark.parametrize(
    ("gate", "expected_case", "expected_action"),
    [
        pytest.param("incomplete", "incomplete_approval", None, id="incomplete"),
        pytest.param(
            "stale",
            "stale_target",
            "request_new_validation_and_approval",
            id="stale",
        ),
        pytest.param(
            "diverged",
            "diverged_target",
            "request_new_validation_and_approval",
            id="diverged",
        ),
    ],
)
def test_null_spike_pre_mutation_gates_return_safety_evidence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    gate: str,
    expected_case: str,
    expected_action: str | None,
) -> None:
    """Representative approval and target gates fail without recovery mutation."""

    source_path, request = _null_spike_fixture(tmp_path)
    if gate == "stale":
        original_load = recovery_executor.load_hmda_loans_partition
        load_count = 0

        def raise_stale_on_target_load(
            connection: duckdb.DuckDBPyConnection,
            source_paths: Sequence[str | Path],
            source_year: int,
            *,
            source_file: str | None = None,
            table_name: str = "raw.hmda_loans",
            expected_identity: PartitionContentIdentity | None = None,
            preserve_source_metadata: bool = False,
        ) -> int:
            nonlocal load_count
            load_count += 1
            if load_count == 2:
                raise HMDAStalePartitionError("stale")
            return original_load(
                connection,
                source_paths,
                source_year,
                source_file=source_file,
                table_name=table_name,
                expected_identity=expected_identity,
                preserve_source_metadata=preserve_source_metadata,
            )

        monkeypatch.setattr(
            recovery_executor,
            "load_hmda_loans_partition",
            raise_stale_on_target_load,
        )

    def approve(proposal: RecoveryProposal) -> Approval:
        approval = _approved(proposal)
        if gate == "incomplete":
            return approval.model_copy(
                update={"requested_actions": ("overwrite_partition",)}
            )
        if gate == "diverged":
            with DuckDBConnectionManager(request.database_path) as connection:
                connection.execute("UPDATE raw.hmda_loans SET income = income + 1")
        return approval

    try:
        result = _evaluate_null_spike(
            request=request,
            source_paths=(source_path,),
            workspace=tmp_path / "run",
            target_column="income",
            null_fraction=0.2,
            approve=approve,
            validate_candidate=lambda _request: "sha256:candidate",
            validate_target=lambda _request: "sha256:target",
        )
    except ApprovalGateError:
        pytest.fail(
            f"{gate} gate must return pre-mutation safety evidence",
            pytrace=False,
        )

    assert result.recovery is None
    assert result.replay is None
    assert result.post_recovery_case.case_name == expected_case
    assert result.post_recovery_case.failure_stage == "before_target_mutation"
    assert result.post_recovery_case.target_mutated is False
    assert result.post_recovery_case.reconciliation_action == expected_action
    assert any(
        "ApprovalGateError" in ref for ref in result.post_recovery_case.evidence_refs
    )


@pytest.mark.integration
def test_null_spike_candidate_dbt_failure_preserves_target_and_projection(
    tmp_path: Path,
) -> None:
    """Candidate dbt failure leaves target data and canonical artifacts unchanged."""

    source_path, request = _null_spike_fixture(tmp_path)
    initial_projection_id = artifact_projection_id(
        request.dbt_manifest_path,
        request.dbt_run_results_path,
    )
    target_identity_before_failure: PartitionContentIdentity | None = None

    def fail_candidate(_request: DataOperationRequest) -> str:
        nonlocal target_identity_before_failure
        with DuckDBConnectionManager(
            request.database_path,
            read_only=True,
        ) as connection:
            target_identity_before_failure = partition_content_identity(
                connection,
                table_name=request.raw_table_name,
                source_year=request.source_year,
                source_file=request.source_file,
            )
        raise DataOperationError(
            "candidate dbt failed",
            context={"run_target_path": str(tmp_path / "candidate-failed-run")},
        )

    try:
        result = _evaluate_null_spike(
            request=request,
            source_paths=(source_path,),
            workspace=tmp_path / "run",
            target_column="income",
            null_fraction=0.2,
            approve=_approved,
            validate_candidate=fail_candidate,
            validate_target=lambda _request: "sha256:target",
        )
    except DataOperationError:
        pytest.fail(
            "candidate dbt failure must return unchanged target/projection evidence",
            pytrace=False,
        )

    assert result.recovery is None
    assert result.replay is None
    assert result.candidate_dbt_projection_id is None
    assert result.post_recovery_case.case_name == "candidate_validation_failure"
    assert result.post_recovery_case.failure_stage == "before_target_mutation"
    assert result.post_recovery_case.target_mutated is False
    assert result.post_recovery_case.artifact_projection_ids == [initial_projection_id]
    with DuckDBConnectionManager(request.database_path, read_only=True) as connection:
        assert (
            partition_content_identity(
                connection,
                table_name=request.raw_table_name,
                source_year=request.source_year,
                source_file=request.source_file,
            )
            == target_identity_before_failure
        )
    assert (
        artifact_projection_id(
            request.dbt_manifest_path,
            request.dbt_run_results_path,
        )
        == initial_projection_id
    )


@pytest.mark.integration
def test_null_spike_target_dbt_failure_records_mutation_and_projection(
    tmp_path: Path,
) -> None:
    """Target dbt failure retains recovered data and current projection evidence."""

    source_path, request = _null_spike_fixture(tmp_path)
    initial_projection_id = artifact_projection_id(
        request.dbt_manifest_path,
        request.dbt_run_results_path,
    )

    def fail_target(_request: DataOperationRequest) -> str:
        raise DataOperationError(
            "target dbt failed",
            context={"run_target_path": str(tmp_path / "target-failed-run")},
        )

    try:
        result = _evaluate_null_spike(
            request=request,
            source_paths=(source_path,),
            workspace=tmp_path / "run",
            target_column="income",
            null_fraction=0.2,
            approve=_approved,
            validate_candidate=lambda _request: "sha256:candidate",
            validate_target=fail_target,
        )
    except DataOperationError:
        pytest.fail(
            "target dbt failure must return post-mutation projection evidence",
            pytrace=False,
        )

    assert result.recovery is not None
    assert result.recovery.mutation_state == "partition_changed"
    assert result.target_dbt_projection_id is None
    assert result.target_dbt_failure == "target dbt failed"
    assert result.post_recovery_case.case_name == "recovery_dbt_failure"
    assert result.post_recovery_case.failure_stage == "after_partition_mutation"
    assert result.post_recovery_case.target_mutated is True
    assert result.post_recovery_case.reconciliation_action == "resume_verification"
    assert result.post_recovery_case.artifact_projection_ids == [initial_projection_id]
    assert result.recovery.actual_identity == result.expected_recovery_identity
    _assert_exact_null_rate_evidence(result.post_recovery_case.evidence_refs)


@pytest.mark.integration
def test_null_spike_target_value_error_returns_structured_failure(
    tmp_path: Path,
) -> None:
    """Target ValueError preserves recovery, replay, and actual projection."""

    source_path, request = _null_spike_fixture(tmp_path)
    prior_projection_id = artifact_projection_id(
        request.dbt_manifest_path,
        request.dbt_run_results_path,
    )
    promoted_projection_id: str | None = None

    def fail_target(target_request: DataOperationRequest) -> str:
        nonlocal promoted_projection_id
        run_target = tmp_path / "value-error-run"
        run_target.mkdir()
        run_manifest = run_target / "manifest.json"
        run_results = run_target / "run_results.json"
        run_manifest.write_text("value-error-manifest", encoding="utf-8")
        run_results.write_text("value-error-results", encoding="utf-8")
        promoted_projection_id = artifact_projection_id(run_manifest, run_results)
        promote_dbt_artifacts(
            DbtBuildResult(
                command=["dbt", "build"],
                return_code=0,
                manifest_path=run_manifest,
                run_results_path=run_results,
                projection_id=promoted_projection_id,
                succeeded=True,
            ),
            target_request,
        )
        raise ValueError("target validation rejected")

    try:
        result = _evaluate_null_spike(
            request=request,
            source_paths=(source_path,),
            workspace=tmp_path / "run",
            target_column="income",
            null_fraction=0.2,
            approve=_approved,
            validate_candidate=lambda _request: "sha256:candidate",
            validate_target=fail_target,
        )
    except ValueError:
        pytest.fail(
            "target ValueError must return structured post-mutation evidence",
            pytrace=False,
        )

    assert promoted_projection_id is not None
    assert result.recovery is not None
    assert result.recovery.mutation_state == "partition_changed"
    assert result.recovery.actual_identity == result.expected_recovery_identity
    assert result.replay is not None
    assert result.replay.mutation_state == "already_recovered"
    assert result.replay.actual_identity == result.recovery.actual_identity
    assert result.target_dbt_projection_id is None
    assert result.target_dbt_failure == "target validation rejected"
    assert result.target_dbt_failure_context is None
    assert result.post_recovery_case.case_name == "recovery_dbt_failure"
    assert result.post_recovery_case.failure_stage == "after_partition_mutation"
    assert result.post_recovery_case.target_mutated is True
    assert result.post_recovery_case.reconciliation_action == "resume_verification"
    assert result.post_recovery_case.artifact_projection_ids == [promoted_projection_id]
    assert prior_projection_id not in result.post_recovery_case.artifact_projection_ids
    assert any(
        "ValueError" in evidence for evidence in result.post_recovery_case.evidence_refs
    )
    _assert_exact_null_rate_evidence(result.post_recovery_case.evidence_refs)


@pytest.mark.integration
def test_null_spike_post_promotion_failure_reports_actual_projection(
    tmp_path: Path,
) -> None:
    """A domain failure after promotion reports the actual canonical projection."""

    source_path, request = _null_spike_fixture(tmp_path)
    prior_projection_id = artifact_projection_id(
        request.dbt_manifest_path,
        request.dbt_run_results_path,
    )
    promoted_projection_id: str | None = None

    def fail_after_promotion(target_request: DataOperationRequest) -> str:
        nonlocal promoted_projection_id
        run_target = tmp_path / "promoted-run"
        run_target.mkdir()
        run_manifest = run_target / "manifest.json"
        run_results = run_target / "run_results.json"
        run_manifest.write_text("promoted-manifest", encoding="utf-8")
        run_results.write_text("promoted-results", encoding="utf-8")
        promoted_projection_id = artifact_projection_id(run_manifest, run_results)
        promote_dbt_artifacts(
            DbtBuildResult(
                command=["dbt", "build"],
                return_code=0,
                manifest_path=run_manifest,
                run_results_path=run_results,
                projection_id=promoted_projection_id,
                succeeded=True,
            ),
            target_request,
        )
        raise DataOperationError(
            "post-promotion observation failed",
            context={"run_target_path": str(run_target)},
        )

    try:
        result = _evaluate_null_spike(
            request=request,
            source_paths=(source_path,),
            workspace=tmp_path / "run",
            target_column="income",
            null_fraction=0.2,
            approve=_approved,
            validate_candidate=lambda _request: "sha256:candidate",
            validate_target=fail_after_promotion,
        )
    except DataOperationError:
        pytest.fail(
            "post-promotion failure must return actual projection evidence",
            pytrace=False,
        )

    assert promoted_projection_id is not None
    assert result.recovery is not None
    assert result.recovery.mutation_state == "partition_changed"
    assert result.post_recovery_case.failure_stage == "after_partition_mutation"
    assert result.post_recovery_case.reconciliation_action == "resume_verification"
    assert result.post_recovery_case.artifact_projection_ids == [promoted_projection_id]
    assert prior_projection_id not in result.post_recovery_case.artifact_projection_ids


def _assert_exact_null_rate_evidence(evidence_refs: Sequence[str]) -> None:
    for rate in ("baseline", "recovery", "replay"):
        assert f"{rate}-null-rate:income:0.0" in evidence_refs


def _evaluate_null_spike(
    *,
    request: DataOperationRequest,
    source_paths: Sequence[str | Path],
    workspace: str | Path,
    target_column: str,
    approve: Callable[[RecoveryProposal], Approval],
    validate_candidate: Callable[[DataOperationRequest], str],
    validate_target: Callable[[DataOperationRequest], str],
    null_fraction: float = 0.2,
) -> null_spike_evaluation.NullSpikeVerticalSliceResult:
    return null_spike_evaluation.evaluate_null_spike_vertical_slice(
        request=request,
        source_paths=source_paths,
        workspace=workspace,
        target_column=target_column,
        approve=approve,
        validate_candidate=validate_candidate,
        validate_target=validate_target,
        null_fraction=null_fraction,
    )


def _null_spike_fixture(
    tmp_path: Path,
    *,
    row_count: int = 10,
) -> tuple[Path, DataOperationRequest]:
    source_path = tmp_path / "year_2025.csv"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(
        "\n".join(
            [
                "activity_year,loan_purpose,action_taken,loan_amount,income,state_code,county_code",
                *[f"2025,1,1,{index},100,CA,06001" for index in range(row_count)],
            ]
        ),
        encoding="utf-8",
    )
    target = tmp_path / "dbt" / "target"
    target.mkdir(parents=True)
    (target / "manifest.json").write_text(
        '{"sources":{"source.hmda_reliability.raw.hmda_loans":{"name":"hmda_loans","schema":"raw","resource_type":"source","depends_on":{"nodes":[]}}},"nodes":{}}',
        encoding="utf-8",
    )
    (target / "run_results.json").write_text("{}", encoding="utf-8")
    return source_path, DataOperationRequest(
        database_path=tmp_path / "target.duckdb",
        source_root=tmp_path,
        profile_columns=("income",),
        dbt_manifest_path=target / "manifest.json",
        dbt_run_results_path=target / "run_results.json",
        dbt_run_target_path=target / "runs",
        observed_at=datetime(2026, 6, 10, 0, 0, tzinfo=UTC),
    )


def _approved(proposal: RecoveryProposal) -> Approval:
    approved_at = datetime(2026, 6, 10, 0, 0, tzinfo=UTC)
    return Approval(
        approval_id="approval_null_spike",
        incident_id=proposal.incident_id,
        status=ApprovalStatus.APPROVED,
        requested_by="data-platform",
        requested_at=approved_at,
        approved_by="data-owner",
        approved_at=approved_at,
        requested_actions=proposal.target_actions,
        recovery_proposal=proposal,
    )
