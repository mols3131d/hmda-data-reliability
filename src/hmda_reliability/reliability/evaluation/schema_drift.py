"""Deterministic complete-table schema-drift recovery evaluation."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from hmda_reliability.data_platform.duckdb import (
    DuckDBConnectionManager,
    database_mutation_lock,
)
from hmda_reliability.data_platform.sql import qualify_table_name, quote_identifier
from hmda_reliability.hmda_data import load_hmda_loans
from hmda_reliability.reliability.contracts import (
    ReliabilityContract,
    SchemaRecoveryApproval,
    SchemaRecoveryProposal,
    TableStateIdentity,
)
from hmda_reliability.reliability.errors import (
    ApprovalGateError,
    ReliabilityError,
    SchemaRecoveryCandidateError,
    SchemaRecoveryValidationError,
)
from hmda_reliability.reliability.evaluation.case_result import EvaluationCaseResult
from hmda_reliability.reliability.profiling import (
    ProfileSnapshotRequest,
    create_profile_snapshot,
    create_table_state_identity,
)
from hmda_reliability.reliability.recovery import (
    ApprovedSchemaRecoveryRequest,
    SchemaRecoveryValidationResult,
    execute_approved_schema_recovery,
    preflight_schema_recovery_candidate,
)

if TYPE_CHECKING:
    from hmda_reliability.data_operations import (
        DataOperationRequest,
        DbtBuildResult,
        LifecycleResult,
    )

type SchemaApprovalCallback = Callable[[SchemaRecoveryProposal], SchemaRecoveryApproval]
type DbtValidationCallback = Callable[[DataOperationRequest], DbtBuildResult]


class SchemaDriftVerticalSliceResult(ReliabilityContract):
    """Controlled drift setup, recovery, replay, and downstream evidence."""

    baseline_state: TableStateIdentity
    drifted_state: TableStateIdentity
    expected_after_state: TableStateIdentity
    clean_case: EvaluationCaseResult
    schema_drift_case: EvaluationCaseResult
    post_recovery_case: EvaluationCaseResult
    drifted_column: str
    drifted_column_type: str
    recovery: SchemaRecoveryValidationResult | None = None
    replay: SchemaRecoveryValidationResult | None = None
    candidate_dbt_projection_id: str | None = None
    target_dbt_projection_id: str | None = None
    target_dbt_failure: str | None = None
    target_dbt_failure_context: dict[str, object] | None = None


def evaluate_schema_drift_vertical_slice(
    *,
    request: DataOperationRequest,
    source_paths: Sequence[str | Path],
    workspace: str | Path,
    approve: SchemaApprovalCallback,
    validate_candidate: DbtValidationCallback,
    validate_target: DbtValidationCallback,
) -> SchemaDriftVerticalSliceResult:
    """Build clean and drifted complete tables before approved restoration."""

    from hmda_reliability.data_operations import run_incident_lifecycle
    from hmda_reliability.data_operations.errors import DataOperationError

    root = Path(workspace)
    clean_database_path = root / "clean.duckdb"
    candidate_database_path = root / "candidate.duckdb"
    _ensure_disposable_database_paths(
        request.database_path,
        clean_database_path,
        candidate_database_path,
    )
    if request.observed_at is None:
        raise ValueError("schema-drift evaluation에는 observed_at이 필요합니다.")
    root.mkdir(parents=True, exist_ok=True)
    paths = tuple(Path(path) for path in source_paths)

    clean_request = request.model_copy(update={"database_path": clean_database_path})
    with DuckDBConnectionManager(clean_database_path) as connection:
        load_hmda_loans(connection, paths, table_name=request.raw_table_name)
        baseline_profile = create_profile_snapshot(
            connection,
            _profile_request(clean_request),
        )
        baseline_state = create_table_state_identity(
            connection,
            request.raw_table_name,
        )
    clean_lifecycle = run_incident_lifecycle(clean_request, baseline_profile)

    with DuckDBConnectionManager(request.database_path) as connection:
        load_hmda_loans(connection, paths, table_name=request.raw_table_name)
        with database_mutation_lock(request.database_path):
            connection.execute(
                f"ALTER TABLE {qualify_table_name(request.raw_table_name)} "
                f"ALTER COLUMN {quote_identifier('loan_amount')} TYPE VARCHAR"
            )
        drifted_state = create_table_state_identity(
            connection,
            request.raw_table_name,
        )
    schema_drift_lifecycle = run_incident_lifecycle(request, baseline_profile)

    candidate_request = request.model_copy(
        update={
            "database_path": candidate_database_path,
            "dbt_run_target_path": root / "candidate-dbt-runs",
        }
    )
    with DuckDBConnectionManager(candidate_database_path) as connection:
        load_hmda_loans(connection, paths, table_name=request.raw_table_name)
    try:
        candidate_dbt_result = validate_candidate(candidate_request)
        with DuckDBConnectionManager(
            candidate_database_path,
            read_only=True,
        ) as connection:
            candidate_evidence = preflight_schema_recovery_candidate(
                connection,
                expected_after_state=baseline_state,
                dbt_result=candidate_dbt_result,
            )
    except (DataOperationError, SchemaRecoveryCandidateError, ValueError) as exc:
        return _failure_result(
            baseline_state=baseline_state,
            drifted_state=drifted_state,
            clean_lifecycle=clean_lifecycle,
            schema_drift_lifecycle=schema_drift_lifecycle,
            case_name="invalid_candidate",
            failure_stage="before_target_mutation",
            target_mutated=False,
            reconciliation_action="request_new_validation_and_approval",
            exc=exc,
        )

    proposal = SchemaRecoveryProposal(
        proposal_id=f"schema_recovery_{_schema_drift_incident_id(schema_drift_lifecycle)}",
        incident_id=_schema_drift_incident_id(schema_drift_lifecycle),
        observation_partition=str(request.source_year),
        table_name=request.raw_table_name,
        candidate_state=candidate_evidence.candidate_state,
        approved_before_state=drifted_state,
        expected_after_state=baseline_state,
        validation_evidence_refs=candidate_evidence.validation_evidence_refs,
        dbt_projection_id=candidate_evidence.dbt_projection_id,
        target_actions=("replace_table", "rerun_profile_snapshot"),
    )
    try:
        approval = approve(proposal)
    except (ApprovalGateError, ValueError) as exc:
        return _failure_result(
            baseline_state=baseline_state,
            drifted_state=drifted_state,
            clean_lifecycle=clean_lifecycle,
            schema_drift_lifecycle=schema_drift_lifecycle,
            case_name="approval_failure",
            failure_stage="before_target_mutation",
            target_mutated=False,
            reconciliation_action="request_new_validation_and_approval",
            candidate_projection_id=candidate_evidence.dbt_projection_id,
            exc=exc,
        )

    recovery_request = ApprovedSchemaRecoveryRequest(
        approval=approval,
        proposal=proposal,
        target_database_path=request.database_path,
        candidate_database_path=candidate_database_path,
        profile_request=_profile_request(request),
    )
    try:
        recovery = execute_approved_schema_recovery(recovery_request)
    except (
        ApprovalGateError,
        SchemaRecoveryCandidateError,
        SchemaRecoveryValidationError,
    ) as exc:
        return _failure_result(
            baseline_state=baseline_state,
            drifted_state=drifted_state,
            clean_lifecycle=clean_lifecycle,
            schema_drift_lifecycle=schema_drift_lifecycle,
            case_name=_recovery_failure_case_name(exc),
            failure_stage=getattr(exc, "failure_stage", "before_target_mutation"),
            target_mutated=False,
            reconciliation_action=getattr(exc, "reconciliation_action", None),
            candidate_projection_id=candidate_evidence.dbt_projection_id,
            exc=exc,
        )
    try:
        replay = execute_approved_schema_recovery(recovery_request)
    except (
        ApprovalGateError,
        SchemaRecoveryCandidateError,
        SchemaRecoveryValidationError,
    ) as exc:
        return _failure_result(
            baseline_state=baseline_state,
            drifted_state=drifted_state,
            clean_lifecycle=clean_lifecycle,
            schema_drift_lifecycle=schema_drift_lifecycle,
            case_name=(
                "diverged_replay"
                if getattr(exc, "reconciliation_action", None)
                == "request_new_validation_and_approval"
                else "replay_failure"
            ),
            failure_stage="replay_verification",
            target_mutated=recovery.mutation_state == "table_replaced",
            reconciliation_action=getattr(exc, "reconciliation_action", None),
            candidate_projection_id=candidate_evidence.dbt_projection_id,
            recovery=recovery,
            exc=exc,
        )
    try:
        post_recovery_lifecycle = run_incident_lifecycle(request, baseline_profile)
    except (DataOperationError, ReliabilityError) as exc:
        return _failure_result(
            baseline_state=baseline_state,
            drifted_state=drifted_state,
            clean_lifecycle=clean_lifecycle,
            schema_drift_lifecycle=schema_drift_lifecycle,
            case_name="post_recovery_lifecycle_failure",
            failure_stage="after_target_mutation",
            target_mutated=recovery.mutation_state == "table_replaced",
            reconciliation_action="resume_verification",
            candidate_projection_id=candidate_evidence.dbt_projection_id,
            recovery=recovery,
            replay=replay,
            exc=exc,
        )
    try:
        target_dbt_result = validate_target(request)
        if not target_dbt_result.succeeded or target_dbt_result.return_code != 0:
            raise ValueError("target dbt validation이 성공하지 않았습니다.")
    except (DataOperationError, ReliabilityError, ValueError) as exc:
        context = getattr(exc, "context", None)
        target_dbt_context = dict(context) if isinstance(context, dict) else None
        return _failure_result(
            baseline_state=baseline_state,
            drifted_state=drifted_state,
            clean_lifecycle=clean_lifecycle,
            schema_drift_lifecycle=schema_drift_lifecycle,
            case_name="recovery_dbt_failure",
            failure_stage="after_target_mutation",
            target_mutated=recovery.mutation_state == "table_replaced",
            reconciliation_action="resume_verification",
            candidate_projection_id=candidate_evidence.dbt_projection_id,
            recovery=recovery,
            replay=replay,
            post_recovery_lifecycle=post_recovery_lifecycle,
            target_dbt_failure=str(exc),
            target_dbt_failure_context=target_dbt_context,
            exc=exc,
        )
    post_recovery_case = _case_result(
        "post_recovery",
        post_recovery_lifecycle,
        state=recovery.actual_state,
    ).model_copy(
        update={
            "target_mutated": recovery.mutation_state == "table_replaced",
            "reconciliation_action": replay.reconciliation_action,
            "artifact_projection_ids": [target_dbt_result.projection_id],
        }
    )
    return SchemaDriftVerticalSliceResult(
        baseline_state=baseline_state,
        drifted_state=drifted_state,
        expected_after_state=baseline_state,
        clean_case=_case_result("clean", clean_lifecycle, state=baseline_state),
        schema_drift_case=_case_result(
            "schema_drift",
            schema_drift_lifecycle,
            state=drifted_state,
        ),
        post_recovery_case=post_recovery_case,
        drifted_column="loan_amount",
        drifted_column_type="VARCHAR",
        recovery=recovery,
        replay=replay,
        candidate_dbt_projection_id=candidate_evidence.dbt_projection_id,
        target_dbt_projection_id=target_dbt_result.projection_id,
    )


def _ensure_disposable_database_paths(*paths: Path) -> None:
    existing_paths = [path for path in paths if path.exists() or path.is_symlink()]
    if existing_paths:
        joined_paths = ", ".join(str(path) for path in existing_paths)
        raise ValueError(
            f"schema-drift evaluation database는 새 path여야 합니다: {joined_paths}"
        )
    resolved_paths = [path.resolve(strict=False) for path in paths]
    if len(set(resolved_paths)) != len(resolved_paths):
        raise ValueError("schema-drift evaluation database path는 서로 달라야 합니다.")


def _profile_request(request: DataOperationRequest) -> ProfileSnapshotRequest:
    assert request.observed_at is not None
    return ProfileSnapshotRequest(
        asset_name=request.asset_name,
        table_name=request.raw_table_name,
        partition_column=request.partition_column,
        partition=request.source_year,
        profile_columns=request.profile_columns,
        freshness_column=request.freshness_column,
        observed_at=request.observed_at,
    )


def _schema_drift_incident_id(lifecycle: LifecycleResult) -> str:
    schema_drift_ids = [
        incident_id
        for incident_id, incident_type in zip(
            lifecycle.detected_incident_ids,
            lifecycle.detected_incident_types,
            strict=True,
        )
        if incident_type == "schema_drift"
    ]
    if len(schema_drift_ids) != 1:
        raise ValueError(
            "controlled target은 schema_drift incident 하나를 생성해야 합니다."
        )
    return schema_drift_ids[0]


def _case_result(
    case_name: str,
    lifecycle: LifecycleResult,
    *,
    state: TableStateIdentity,
) -> EvaluationCaseResult:
    actions = [
        *lifecycle.recommended_actions,
        *lifecycle.backfill_actions,
        *lifecycle.validation_actions,
    ]
    is_drift = case_name == "schema_drift"
    state_evidence = [
        f"schema:{state.schema_hash}",
        f"row-count:{state.row_count}",
        *(
            f"partition:{identity.source_year}:{identity.digest}"
            for identity in state.partition_identities
        ),
    ]
    return EvaluationCaseResult(
        case_name=case_name,
        expected_incident_types=["schema_drift"] if is_drift else [],
        detected_incident_types=list(lifecycle.detected_incident_types),
        required_actions=(
            ["compare_schema_contract", "validate_dbt_build"] if is_drift else []
        ),
        remediation_actions=list(dict.fromkeys(actions)),
        evidence_refs=[*lifecycle.evidence_refs, *state_evidence],
    )


def _failure_result(
    *,
    baseline_state: TableStateIdentity,
    drifted_state: TableStateIdentity,
    clean_lifecycle: LifecycleResult,
    schema_drift_lifecycle: LifecycleResult,
    case_name: str,
    failure_stage: str,
    target_mutated: bool,
    reconciliation_action: str | None,
    candidate_projection_id: str | None = None,
    recovery: SchemaRecoveryValidationResult | None = None,
    replay: SchemaRecoveryValidationResult | None = None,
    post_recovery_lifecycle: LifecycleResult | None = None,
    target_dbt_failure: str | None = None,
    target_dbt_failure_context: dict[str, object] | None = None,
    exc: Exception,
) -> SchemaDriftVerticalSliceResult:
    context = getattr(exc, "context", None)
    context = dict(context) if isinstance(context, dict) else {}
    evidence_refs = [f"failure:{type(exc).__name__}", str(exc)]
    evidence_refs.extend(f"{key}:{value}" for key, value in context.items())
    observed_lifecycle = post_recovery_lifecycle or schema_drift_lifecycle
    failure_case = EvaluationCaseResult(
        case_name=case_name,
        expected_incident_types=([] if post_recovery_lifecycle else ["schema_drift"]),
        detected_incident_types=list(observed_lifecycle.detected_incident_types),
        failure_stage=failure_stage,
        target_mutated=target_mutated,
        reconciliation_action=reconciliation_action,
        evidence_refs=evidence_refs,
    )
    return SchemaDriftVerticalSliceResult(
        baseline_state=baseline_state,
        drifted_state=drifted_state,
        expected_after_state=baseline_state,
        clean_case=_case_result("clean", clean_lifecycle, state=baseline_state),
        schema_drift_case=_case_result(
            "schema_drift",
            schema_drift_lifecycle,
            state=drifted_state,
        ),
        post_recovery_case=failure_case,
        drifted_column="loan_amount",
        drifted_column_type="VARCHAR",
        recovery=recovery,
        replay=replay,
        candidate_dbt_projection_id=candidate_projection_id,
        target_dbt_failure=target_dbt_failure,
        target_dbt_failure_context=target_dbt_failure_context,
    )


def _recovery_failure_case_name(exc: Exception) -> str:
    if getattr(exc, "mutation_state", None) == "rolled_back":
        return "replacement_rollback"
    if getattr(exc, "reconciliation_action", None) == (
        "request_new_validation_and_approval"
    ):
        return "stale_target"
    return "recovery_failure"
