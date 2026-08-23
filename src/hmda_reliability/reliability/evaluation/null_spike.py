"""Deterministic null-spike recovery evaluation."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING

import duckdb
from pydantic import BaseModel, ConfigDict

from project_pivot.data_platform.artifacts import (
    ArtifactProjectionLockError,
    ArtifactProjectionReadError,
    artifact_projection_id,
    artifact_projection_lock,
)
from project_pivot.data_platform.duckdb import DuckDBConnectionManager
from project_pivot.data_platform.sql import quote_string_literal
from project_pivot.hmda_data import (
    PartitionContentIdentity,
    load_hmda_loans_partition,
    null_spike,
    partition_content_identity,
)
from project_pivot.reliability.contracts import Approval, RecoveryProposal
from project_pivot.reliability.detection import DetectionThresholds
from project_pivot.reliability.errors import (
    ApprovalGateError,
    BackfillValidationError,
    ReliabilityError,
)
from project_pivot.reliability.evaluation.case_result import EvaluationCaseResult
from project_pivot.reliability.evaluation.recovery_case import (
    build_recovery_evaluation_case,
)
from project_pivot.reliability.profiling import (
    ProfileSnapshotRequest,
    create_profile_snapshot,
)
from project_pivot.reliability.recovery import (
    ApprovedBackfillRequest,
    BackfillValidationResult,
    execute_approved_backfill,
)

if TYPE_CHECKING:
    from project_pivot.data_operations import DataOperationRequest
    from project_pivot.data_operations.lifecycle_result import LifecycleResult

type ApprovalCallback = Callable[[RecoveryProposal], Approval]
type DbtValidationCallback = Callable[[DataOperationRequest], str]


class NullSpikeVerticalSliceResult(BaseModel):
    """Deterministic clean and null-spike recovery evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    fixture_identity: PartitionContentIdentity
    expected_recovery_identity: PartitionContentIdentity
    clean_case: EvaluationCaseResult
    null_spike_case: EvaluationCaseResult
    post_recovery_case: EvaluationCaseResult
    recovery: BackfillValidationResult | None = None
    replay: BackfillValidationResult | None = None
    candidate_dbt_projection_id: str | None = None
    target_dbt_projection_id: str | None = None
    target_dbt_failure: str | None = None
    target_dbt_failure_context: dict[str, object] | None = None


def evaluate_null_spike_vertical_slice(
    *,
    request: DataOperationRequest,
    source_paths: Sequence[str | Path],
    workspace: str | Path,
    target_column: str,
    approve: ApprovalCallback,
    validate_candidate: DbtValidationCallback,
    validate_target: DbtValidationCallback,
    null_fraction: float = 0.2,
) -> NullSpikeVerticalSliceResult:
    """Evaluate a controlled single-column null spike before recovery execution."""

    from project_pivot.data_operations import run_incident_lifecycle
    from project_pivot.data_operations.errors import DataOperationError

    if target_column not in request.profile_columns:
        raise ValueError("target_column은 profile_columns에 포함되어야 합니다.")
    if request.observed_at is None:
        raise ValueError("null-spike evaluation에는 observed_at이 필요합니다.")

    root = Path(workspace)
    clean_database_path = root / "clean.duckdb"
    candidate_database_path = root / "candidate.duckdb"
    _ensure_disposable_database_paths(
        request.database_path,
        clean_database_path,
        candidate_database_path,
    )
    root.mkdir(parents=True, exist_ok=True)
    scoped_source_paths = _scoped_source_paths(source_paths, request.source_file)
    clean_request = request.model_copy(update={"database_path": clean_database_path})
    with DuckDBConnectionManager(clean_request.database_path) as connection:
        load_hmda_loans_partition(
            connection,
            scoped_source_paths,
            clean_request.source_year,
            source_file=clean_request.source_file,
            table_name=clean_request.raw_table_name,
        )
        baseline = create_profile_snapshot(connection, _profile_request(clean_request))
        fixture_identity = partition_content_identity(
            connection,
            table_name=clean_request.raw_table_name,
            source_year=clean_request.source_year,
            source_file=clean_request.source_file,
        )
    clean_lifecycle = run_incident_lifecycle(clean_request, baseline)

    with DuckDBConnectionManager() as connection:
        defect_path = null_spike(
            connection,
            scoped_source_paths,
            root / "synthetic",
            target_column=target_column,
            null_fraction=null_fraction,
            sample_fraction=1.0,
        )
        defect_path = _materialize_defect_source(
            connection,
            defect_path,
            request.source_file
            or f"null_spike_{request.source_year}{defect_path.suffix}",
        )

    target_request = request.model_copy(update={"database_path": request.database_path})
    with DuckDBConnectionManager(target_request.database_path) as connection:
        load_hmda_loans_partition(
            connection,
            [defect_path],
            target_request.source_year,
            source_file=target_request.source_file,
            table_name=target_request.raw_table_name,
        )
    null_spike_lifecycle = run_incident_lifecycle(target_request, baseline)
    with DuckDBConnectionManager(
        target_request.database_path,
        read_only=True,
    ) as connection:
        target_profile = create_profile_snapshot(
            connection,
            _profile_request(target_request),
        )
        target_identity = partition_content_identity(
            connection,
            table_name=target_request.raw_table_name,
            source_year=target_request.source_year,
            source_file=target_request.source_file,
        )

    baseline_null_rate = baseline.null_rates[target_column]
    target_null_rate = target_profile.null_rates[target_column]
    null_rate_delta = target_null_rate - baseline_null_rate
    if (
        target_profile.row_count != baseline.row_count
        or null_rate_delta < DetectionThresholds().null_spike_delta
    ):
        return _failure_result(
            clean_lifecycle=clean_lifecycle,
            null_spike_lifecycle=null_spike_lifecycle,
            fixture_identity=fixture_identity,
            case_name="unachieved_controlled_defect",
            target_request=target_request,
            failure_stage="before_target_mutation",
            evidence_refs=[
                f"baseline-row-count:{baseline.row_count}",
                f"target-row-count:{target_profile.row_count}",
                f"baseline-null-rate:{target_column}:{baseline_null_rate}",
                f"target-null-rate:{target_column}:{target_null_rate}",
                f"null-rate-delta:{target_column}:{null_rate_delta}",
            ],
        )

    if not _is_single_null_spike(null_spike_lifecycle):
        failure_case = build_recovery_evaluation_case(
            case_name="ambiguous_incident_set",
            expected_incident_types=["null_spike"],
            detected_incident_types=null_spike_lifecycle.detected_incident_types,
            failure_stage="before_target_mutation",
            evidence_refs=[
                f"incident-cardinality:{len(null_spike_lifecycle.detected_incident_ids)}",
                *null_spike_lifecycle.evidence_refs,
            ],
        )
        return NullSpikeVerticalSliceResult(
            fixture_identity=fixture_identity,
            expected_recovery_identity=fixture_identity,
            clean_case=_case_result("clean", clean_lifecycle),
            null_spike_case=_case_result("null_spike", null_spike_lifecycle),
            post_recovery_case=failure_case,
        )

    candidate_request = request.model_copy(
        update={
            "database_path": candidate_database_path,
            "dbt_run_target_path": root / "candidate-dbt-target",
        }
    )
    with DuckDBConnectionManager(candidate_request.database_path) as connection:
        load_hmda_loans_partition(
            connection,
            scoped_source_paths,
            candidate_request.source_year,
            source_file=candidate_request.source_file,
            table_name=candidate_request.raw_table_name,
        )
        candidate_identity = partition_content_identity(
            connection,
            table_name=candidate_request.raw_table_name,
            source_year=candidate_request.source_year,
            source_file=candidate_request.source_file,
        )
        candidate_profile = create_profile_snapshot(
            connection,
            _profile_request(candidate_request),
        )
    candidate_null_rate = candidate_profile.null_rates[target_column]
    if (
        candidate_identity != fixture_identity
        or candidate_null_rate != baseline_null_rate
    ):
        return _failure_result(
            clean_lifecycle=clean_lifecycle,
            null_spike_lifecycle=null_spike_lifecycle,
            fixture_identity=fixture_identity,
            case_name="invalid_candidate",
            target_request=target_request,
            evidence_refs=[
                f"candidate-identity:{candidate_identity.digest}",
                f"expected-identity:{fixture_identity.digest}",
                f"candidate-null-rate:{target_column}:{candidate_null_rate}",
                f"baseline-null-rate:{target_column}:{baseline_null_rate}",
            ],
            failure_stage="before_target_mutation",
        )
    try:
        candidate_projection_id = validate_candidate(candidate_request)
    except (DataOperationError, ValueError) as exc:
        return _failure_result(
            clean_lifecycle=clean_lifecycle,
            null_spike_lifecycle=null_spike_lifecycle,
            fixture_identity=fixture_identity,
            case_name="candidate_validation_failure",
            target_request=target_request,
            exc=exc,
            failure_stage="before_target_mutation",
        )
    incident_id = null_spike_lifecycle.detected_incident_ids[0]
    proposal = RecoveryProposal(
        proposal_id=f"recovery_{incident_id}",
        incident_id=incident_id,
        incident_type="null_spike",
        table_name=target_request.raw_table_name,
        source_year=target_request.source_year,
        source_file=target_request.source_file,
        candidate_identity=candidate_identity,
        approved_before_identity=target_identity,
        expected_after_identity=fixture_identity,
        validation_evidence_refs=(
            candidate_identity.digest,
            candidate_projection_id,
        ),
        dbt_projection_id=candidate_projection_id,
        target_actions=("overwrite_partition", "rerun_profile_snapshot"),
    )
    try:
        approval = approve(proposal)
    except (ApprovalGateError, ValueError) as exc:
        return _failure_result(
            clean_lifecycle=clean_lifecycle,
            null_spike_lifecycle=null_spike_lifecycle,
            fixture_identity=fixture_identity,
            case_name="approval_failure",
            target_request=target_request,
            exc=exc,
            failure_stage="before_target_mutation",
            candidate_projection_id=candidate_projection_id,
        )
    recovery_request = ApprovedBackfillRequest(
        approval=approval,
        proposal=proposal,
        source_paths=tuple(Path(path) for path in scoped_source_paths),
        source_year=target_request.source_year,
        source_file=target_request.source_file,
        table_name=target_request.raw_table_name,
        profile_request=_profile_request(target_request),
    )
    with DuckDBConnectionManager(target_request.database_path) as connection:
        try:
            recovery = execute_approved_backfill(connection, recovery_request)
        except (ApprovalGateError, BackfillValidationError) as exc:
            case_name = _recovery_failure_case_name(exc)
            failure_stage = _failure_stage(exc)
            return _failure_result(
                clean_lifecycle=clean_lifecycle,
                null_spike_lifecycle=null_spike_lifecycle,
                fixture_identity=fixture_identity,
                case_name=case_name,
                target_request=target_request,
                exc=exc,
                failure_stage=failure_stage,
                reconciliation_action=_reconciliation_action(
                    case_name=case_name,
                    exc=exc,
                    failure_stage=failure_stage,
                ),
                candidate_projection_id=candidate_projection_id,
            )
        recovery_null_rate = recovery.profile_snapshot.null_rates[target_column]
        if not recovery.validation_passed or recovery_null_rate != baseline_null_rate:
            return _failure_result(
                clean_lifecycle=clean_lifecycle,
                null_spike_lifecycle=null_spike_lifecycle,
                fixture_identity=fixture_identity,
                case_name="failed_recovery_quality",
                target_request=target_request,
                failure_stage="after_partition_mutation",
                reconciliation_action=(
                    "request_new_validation_and_approval"
                    if not recovery.validation_passed
                    else "resume_verification"
                ),
                recovery=recovery,
                candidate_projection_id=candidate_projection_id,
                evidence_refs=[
                    f"content-validation:{recovery.validation_passed}",
                    f"baseline-null-rate:{target_column}:{baseline_null_rate}",
                    f"recovery-null-rate:{target_column}:{recovery_null_rate}",
                ],
            )
        try:
            replay = execute_approved_backfill(connection, recovery_request)
        except (ApprovalGateError, BackfillValidationError) as exc:
            replay_case = _recovery_failure_case_name(exc)
            return _failure_result(
                clean_lifecycle=clean_lifecycle,
                null_spike_lifecycle=null_spike_lifecycle,
                fixture_identity=fixture_identity,
                case_name="replay_failure",
                target_request=target_request,
                exc=exc,
                failure_stage="after_partition_mutation",
                reconciliation_action=_reconciliation_action(
                    case_name=replay_case,
                    exc=exc,
                    failure_stage="after_partition_mutation",
                ),
                recovery=recovery,
                candidate_projection_id=candidate_projection_id,
            )
        replay_null_rate = replay.profile_snapshot.null_rates[target_column]
        if not replay.validation_passed or replay_null_rate != baseline_null_rate:
            return _failure_result(
                clean_lifecycle=clean_lifecycle,
                null_spike_lifecycle=null_spike_lifecycle,
                fixture_identity=fixture_identity,
                case_name="failed_replay_quality",
                target_request=target_request,
                failure_stage="after_partition_mutation",
                reconciliation_action=(
                    "request_new_validation_and_approval"
                    if not replay.validation_passed
                    else "resume_verification"
                ),
                recovery=recovery,
                replay=replay,
                candidate_projection_id=candidate_projection_id,
                evidence_refs=[
                    f"content-validation:{replay.validation_passed}",
                    f"baseline-null-rate:{target_column}:{baseline_null_rate}",
                    f"recovery-null-rate:{target_column}:{recovery_null_rate}",
                    f"replay-null-rate:{target_column}:{replay_null_rate}",
                ],
            )

    try:
        post_recovery_lifecycle = run_incident_lifecycle(target_request, baseline)
    except (ArtifactProjectionLockError, DataOperationError, ReliabilityError) as exc:
        return _failure_result(
            clean_lifecycle=clean_lifecycle,
            null_spike_lifecycle=null_spike_lifecycle,
            fixture_identity=fixture_identity,
            case_name="post_recovery_lifecycle_failure",
            target_request=target_request,
            failure_stage="after_partition_mutation",
            exc=exc,
            reconciliation_action="resume_verification",
            recovery=recovery,
            replay=replay,
            candidate_projection_id=candidate_projection_id,
            evidence_refs=[
                f"baseline-null-rate:{target_column}:{baseline_null_rate}",
                f"recovery-null-rate:{target_column}:{recovery_null_rate}",
                f"replay-null-rate:{target_column}:{replay_null_rate}",
            ],
        )
    try:
        target_projection_id = validate_target(target_request)
        target_dbt_failure = None
        target_dbt_failure_context = None
        post_recovery_case = _case_result(
            "post_recovery",
            post_recovery_lifecycle,
        ).model_copy(
            update={
                "evidence_refs": [
                    *post_recovery_lifecycle.evidence_refs,
                    f"baseline-null-rate:{target_column}:{baseline_null_rate}",
                    f"recovery-null-rate:{target_column}:{recovery_null_rate}",
                    f"replay-null-rate:{target_column}:{replay_null_rate}",
                ]
            }
        )
    except (DataOperationError, ValueError) as exc:
        target_projection_id = None
        target_dbt_failure = str(exc)
        context = getattr(exc, "context", None)
        target_dbt_failure_context = (
            dict(context) if isinstance(context, dict) else None
        )
        evidence_refs = [f"failure:{type(exc).__name__}", str(exc)]
        if target_dbt_failure_context and (
            run_target_path := target_dbt_failure_context.get("run_target_path")
        ):
            evidence_refs.append(f"failed-run:{run_target_path}")
        artifact_ids, observation_evidence = _observe_current_projection(target_request)
        evidence_refs.extend(observation_evidence)
        evidence_refs.extend(
            [
                f"baseline-null-rate:{target_column}:{baseline_null_rate}",
                f"recovery-null-rate:{target_column}:{recovery_null_rate}",
                f"replay-null-rate:{target_column}:{replay_null_rate}",
            ]
        )
        post_recovery_case = build_recovery_evaluation_case(
            case_name="recovery_dbt_failure",
            expected_incident_types=[],
            detected_incident_types=post_recovery_lifecycle.detected_incident_types,
            recovery=recovery,
            failure_stage="after_partition_mutation",
            reconciliation_action="resume_verification",
            evidence_refs=evidence_refs,
            artifact_projection_ids=artifact_ids,
        )

    return NullSpikeVerticalSliceResult(
        fixture_identity=fixture_identity,
        expected_recovery_identity=fixture_identity,
        clean_case=_case_result("clean", clean_lifecycle),
        null_spike_case=_case_result("null_spike", null_spike_lifecycle),
        post_recovery_case=post_recovery_case,
        recovery=recovery,
        replay=replay,
        candidate_dbt_projection_id=candidate_projection_id,
        target_dbt_projection_id=target_projection_id,
        target_dbt_failure=target_dbt_failure,
        target_dbt_failure_context=target_dbt_failure_context,
    )


def _failure_result(
    *,
    clean_lifecycle: LifecycleResult,
    null_spike_lifecycle: LifecycleResult,
    fixture_identity: PartitionContentIdentity,
    case_name: str,
    target_request: DataOperationRequest,
    failure_stage: str,
    exc: Exception | None = None,
    evidence_refs: Sequence[str] = (),
    reconciliation_action: str | None = None,
    recovery: BackfillValidationResult | None = None,
    replay: BackfillValidationResult | None = None,
    candidate_projection_id: str | None = None,
) -> NullSpikeVerticalSliceResult:
    context = getattr(exc, "context", {}) if exc is not None else {}
    context = dict(context) if isinstance(context, dict) else {}
    failure_evidence = list(evidence_refs)
    if exc is not None:
        failure_evidence.extend([f"failure:{type(exc).__name__}", str(exc)])
    if run_target_path := context.get("run_target_path"):
        failure_evidence.append(f"failed-run:{run_target_path}")
    for key in (
        "actual_identity",
        "expected_after_identity",
        "execution_mutation_state",
        "profile_error",
    ):
        if key in context:
            failure_evidence.append(f"{key}:{context[key]}")
    artifact_ids, observation_evidence = _observe_current_projection(target_request)
    failure_evidence.extend(observation_evidence)
    failure_case = build_recovery_evaluation_case(
        case_name=case_name,
        expected_incident_types=["null_spike"],
        detected_incident_types=null_spike_lifecycle.detected_incident_types,
        recovery=recovery,
        failure_stage=failure_stage,
        reconciliation_action=reconciliation_action,
        evidence_refs=failure_evidence,
        artifact_projection_ids=artifact_ids,
    )
    return NullSpikeVerticalSliceResult(
        fixture_identity=fixture_identity,
        expected_recovery_identity=fixture_identity,
        clean_case=_case_result("clean", clean_lifecycle),
        null_spike_case=_case_result("null_spike", null_spike_lifecycle),
        post_recovery_case=failure_case,
        recovery=recovery,
        replay=replay,
        candidate_dbt_projection_id=candidate_projection_id,
    )


def _failure_stage(exc: Exception) -> str:
    mutation_state = getattr(exc, "mutation_state", None)
    if mutation_state in {"partition_changed", "diverged_after_profile_failure"}:
        return "after_partition_mutation"
    return "before_target_mutation"


def _recovery_failure_case_name(exc: Exception) -> str:
    message = str(exc)
    if "candidate content" in message:
        return "invalid_candidate"
    if "diverged state" in message:
        return "diverged_target"
    if "새 validation과 approval" in message:
        return "stale_target"
    if "필요한 action" in message or "승인되지 않은" in message:
        return "incomplete_approval"
    return "recovery_failure"


def _reconciliation_action(
    *,
    case_name: str,
    exc: Exception,
    failure_stage: str,
) -> str | None:
    if case_name in {"stale_target", "diverged_target"}:
        return "request_new_validation_and_approval"
    exception_action = getattr(exc, "reconciliation_action", None)
    if exception_action == "request_new_validation_and_approval":
        return exception_action
    if failure_stage == "after_partition_mutation":
        return "resume_verification"
    return exception_action


def _observe_current_projection(
    request: DataOperationRequest,
) -> tuple[list[str], list[str]]:
    try:
        with artifact_projection_lock(
            request.dbt_manifest_path.parent,
            exclusive=False,
        ):
            projection_id = artifact_projection_id(
                request.dbt_manifest_path,
                request.dbt_run_results_path,
            )
    except (ArtifactProjectionLockError, ArtifactProjectionReadError) as exc:
        evidence = [f"failure:{type(exc).__name__}", str(exc)]
        if isinstance(exc, ArtifactProjectionReadError):
            evidence.append(f"artifact:{exc.artifact_path}")
        return [], evidence
    return [projection_id], []


def _is_single_null_spike(lifecycle: LifecycleResult) -> bool:
    return (
        lifecycle.detected_incident_types == ["null_spike"]
        and len(lifecycle.detected_incident_ids) == 1
    )


def _ensure_disposable_database_paths(*paths: Path) -> None:
    existing_paths = [path for path in paths if path.exists() or path.is_symlink()]
    if existing_paths:
        joined_paths = ", ".join(str(path) for path in existing_paths)
        raise ValueError(
            f"null-spike evaluation database는 새 path여야 합니다: {joined_paths}"
        )
    resolved_paths = [path.resolve(strict=False) for path in paths]
    if len(set(resolved_paths)) != len(resolved_paths):
        raise ValueError("null-spike evaluation database path는 서로 달라야 합니다.")


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


def _case_result(case_name: str, lifecycle: LifecycleResult) -> EvaluationCaseResult:
    actions = [
        *lifecycle.recommended_actions,
        *lifecycle.backfill_actions,
        *lifecycle.validation_actions,
    ]
    return EvaluationCaseResult(
        case_name=case_name,
        expected_incident_types=(["null_spike"] if case_name == "null_spike" else []),
        detected_incident_types=list(lifecycle.detected_incident_types),
        required_actions=(
            ["add_dbt_not_null_test"] if case_name == "null_spike" else []
        ),
        remediation_actions=list(dict.fromkeys(actions)),
        evidence_refs=list(lifecycle.evidence_refs),
    )


def _scoped_source_paths(
    source_paths: Sequence[str | Path], source_file: str | None
) -> tuple[str | Path, ...]:
    if source_file is None:
        return tuple(source_paths)
    scoped = tuple(path for path in source_paths if Path(path).name == source_file)
    if not scoped:
        raise ValueError(
            f"source_file scope에 해당하는 source가 없습니다: {source_file}"
        )
    return scoped


def _materialize_defect_source(
    connection: duckdb.DuckDBPyConnection,
    defect_path: Path,
    source_file: str,
) -> Path:
    target_path = defect_path.with_name(source_file)
    if target_path.suffix.lower() == defect_path.suffix.lower():
        defect_path.replace(target_path)
        return target_path
    if target_path.suffix.lower() != ".csv":
        raise ValueError(f"지원하지 않는 synthetic target 형식입니다: {target_path}")
    connection.execute(
        f"""
        COPY (SELECT * FROM read_parquet(?))
        TO {quote_string_literal(str(target_path))}
        (FORMAT CSV, HEADER)
        """,
        [str(defect_path)],
    )
    defect_path.unlink()
    return target_path
