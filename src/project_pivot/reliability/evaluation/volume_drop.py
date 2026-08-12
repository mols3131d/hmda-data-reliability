"""Deterministic volume-drop recovery evaluation."""

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
    partition_content_identity,
    row_count_drop,
)
from project_pivot.reliability.contracts import Approval, RecoveryProposal
from project_pivot.reliability.errors import ApprovalGateError, BackfillValidationError
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


class VolumeDropVerticalSliceResult(BaseModel):
    """Deterministic clean and volume-drop recovery evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    fixture_identity: PartitionContentIdentity
    expected_recovery_identity: PartitionContentIdentity
    clean_case: EvaluationCaseResult
    volume_drop_case: EvaluationCaseResult
    post_recovery_case: EvaluationCaseResult
    recovery: BackfillValidationResult | None
    replay: BackfillValidationResult | None
    candidate_dbt_projection_id: str | None
    target_dbt_projection_id: str | None = None
    target_dbt_failure: str | None = None
    target_dbt_failure_context: dict[str, object] | None = None


def evaluate_volume_drop_vertical_slice(
    *,
    request: DataOperationRequest,
    source_paths: Sequence[str | Path],
    workspace: str | Path,
    approve: ApprovalCallback,
    validate_candidate: DbtValidationCallback,
    validate_target: DbtValidationCallback,
    sample_fraction: float = 0.1,
) -> VolumeDropVerticalSliceResult:
    """Exercise controlled volume-drop recovery against request.database_path.

    Evaluation fixtures are written under ``workspace`` and the target partition is
    intentionally replaced with a synthetic defect before candidate validation or
    approval. Approval gates recovery of that target, not defect injection; the same
    approved request is replayed to verify reconciliation.
    """

    from project_pivot.data_operations import run_incident_lifecycle
    from project_pivot.data_operations.errors import DataOperationError

    root = Path(workspace)
    root.mkdir(parents=True, exist_ok=True)
    scoped_source_paths = _scoped_source_paths(source_paths, request.source_file)
    clean_request = request.model_copy(update={"database_path": root / "clean.duckdb"})
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
        defect_path = row_count_drop(
            connection,
            scoped_source_paths,
            root / "synthetic",
            sample_fraction=sample_fraction,
        )
        defect_path = _materialize_defect_source(
            connection,
            defect_path,
            request.source_file
            or f"row_count_drop_{request.source_year}{defect_path.suffix}",
        )
    target_request = request.model_copy(update={"database_path": request.database_path})
    # Defect injection is part of evaluation and occurs before approval; approval gates recovery only.
    with DuckDBConnectionManager(target_request.database_path) as connection:
        load_hmda_loans_partition(
            connection,
            [defect_path],
            target_request.source_year,
            source_file=target_request.source_file,
            table_name=target_request.raw_table_name,
        )
    volume_drop_lifecycle = run_incident_lifecycle(target_request, baseline)
    if volume_drop_lifecycle.target_content_identity is None:
        raise ValueError("volume_drop lifecycle did not produce target identity")

    candidate_request = request.model_copy(
        update={
            "database_path": root / "candidate.duckdb",
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
        expected_identity = partition_content_identity(
            connection,
            table_name=candidate_request.raw_table_name,
            source_year=candidate_request.source_year,
            source_file=candidate_request.source_file,
        )
    try:
        candidate_projection_id = validate_candidate(candidate_request)
    except (DataOperationError, ValueError) as exc:
        return _failure_result(
            clean_lifecycle=clean_lifecycle,
            volume_drop_lifecycle=volume_drop_lifecycle,
            fixture_identity=fixture_identity,
            expected_identity=expected_identity,
            candidate_projection_id=None,
            case_name="candidate_validation_failure",
            exc=exc,
            failure_stage="before_target_mutation",
            target_request=target_request,
        )
    incident_id = _single_volume_drop_incident_id(volume_drop_lifecycle)
    proposal = RecoveryProposal(
        proposal_id=f"recovery_{incident_id}",
        incident_id=incident_id,
        table_name=target_request.raw_table_name,
        source_year=target_request.source_year,
        source_file=target_request.source_file,
        candidate_identity=expected_identity,
        approved_before_identity=volume_drop_lifecycle.target_content_identity,
        expected_after_identity=expected_identity,
        validation_evidence_refs=(
            expected_identity.digest,
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
            volume_drop_lifecycle=volume_drop_lifecycle,
            fixture_identity=fixture_identity,
            expected_identity=expected_identity,
            candidate_projection_id=candidate_projection_id,
            case_name="approval_failure",
            exc=exc,
            failure_stage="before_target_mutation",
            target_request=target_request,
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
            failure_stage = _failure_stage(exc)
            case_name = _recovery_failure_case_name(exc)
            return _failure_result(
                clean_lifecycle=clean_lifecycle,
                volume_drop_lifecycle=volume_drop_lifecycle,
                fixture_identity=fixture_identity,
                expected_identity=expected_identity,
                candidate_projection_id=candidate_projection_id,
                case_name=case_name,
                exc=exc,
                failure_stage=failure_stage,
                reconciliation_action=_reconciliation_action(
                    case_name=case_name,
                    exc=exc,
                    failure_stage=failure_stage,
                ),
                target_request=target_request,
            )
        try:
            replay = execute_approved_backfill(connection, recovery_request)
        except (ApprovalGateError, BackfillValidationError) as exc:
            replay_failure_case = _recovery_failure_case_name(exc)
            return _failure_result(
                clean_lifecycle=clean_lifecycle,
                volume_drop_lifecycle=volume_drop_lifecycle,
                fixture_identity=fixture_identity,
                expected_identity=expected_identity,
                candidate_projection_id=candidate_projection_id,
                case_name="replay_failure",
                exc=exc,
                failure_stage="after_partition_mutation",
                reconciliation_action=_reconciliation_action(
                    case_name=replay_failure_case,
                    exc=exc,
                    failure_stage="after_partition_mutation",
                ),
                target_request=target_request,
                recovery=recovery,
            )
    post_recovery_lifecycle = run_incident_lifecycle(target_request, baseline)
    try:
        target_projection_id = validate_target(target_request)
        target_dbt_failure = None
        target_dbt_failure_context = None
        post_recovery_case = _case_result("post_recovery", post_recovery_lifecycle)
    except DataOperationError as exc:
        target_projection_id = None
        target_dbt_failure = str(exc)
        error_context = getattr(exc, "context", None)
        target_dbt_failure_context = (
            dict(error_context) if isinstance(error_context, dict) else None
        )
        failure_evidence = [target_dbt_failure]
        if target_dbt_failure_context and (
            run_target_path := target_dbt_failure_context.get("run_target_path")
        ):
            failure_evidence.append(f"failed-run:{run_target_path}")
        artifact_ids, observation_evidence = _observe_current_projection(target_request)
        failure_evidence.extend(observation_evidence)
        post_recovery_case = build_recovery_evaluation_case(
            case_name="recovery_dbt_failure",
            expected_incident_types=[],
            detected_incident_types=post_recovery_lifecycle.detected_incident_types,
            recovery=recovery,
            failure_stage="after_partition_mutation",
            reconciliation_action="resume_verification",
            evidence_refs=failure_evidence,
            artifact_projection_ids=artifact_ids,
        )

    return VolumeDropVerticalSliceResult(
        fixture_identity=fixture_identity,
        expected_recovery_identity=expected_identity,
        clean_case=_case_result("clean", clean_lifecycle),
        volume_drop_case=_case_result("volume_drop", volume_drop_lifecycle),
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
    volume_drop_lifecycle: LifecycleResult,
    fixture_identity: PartitionContentIdentity,
    expected_identity: PartitionContentIdentity,
    candidate_projection_id: str | None,
    case_name: str,
    exc: Exception,
    failure_stage: str,
    target_request: DataOperationRequest,
    reconciliation_action: str | None = None,
    recovery: BackfillValidationResult | None = None,
) -> VolumeDropVerticalSliceResult:
    """예상된 safety failure를 실행형 evaluation case로 변환한다."""

    context = getattr(exc, "context", {})
    context = dict(context) if isinstance(context, dict) else {}
    evidence_refs = [f"failure:{type(exc).__name__}", str(exc)]
    if run_target_path := context.get("run_target_path"):
        evidence_refs.append(f"failed-run:{run_target_path}")
    artifact_ids, observation_evidence = _observe_current_projection(target_request)
    evidence_refs.extend(observation_evidence)
    recovery_case = build_recovery_evaluation_case(
        case_name=case_name,
        expected_incident_types=["volume_drop"],
        detected_incident_types=volume_drop_lifecycle.detected_incident_types,
        recovery=recovery,
        failure_stage=failure_stage,
        reconciliation_action=reconciliation_action,
        evidence_refs=evidence_refs,
        artifact_projection_ids=artifact_ids,
    )
    return VolumeDropVerticalSliceResult(
        fixture_identity=fixture_identity,
        expected_recovery_identity=expected_identity,
        clean_case=_case_result("clean", clean_lifecycle),
        volume_drop_case=_case_result("volume_drop", volume_drop_lifecycle),
        post_recovery_case=recovery_case,
        recovery=recovery,
        replay=None,
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


def _profile_request(request: DataOperationRequest) -> ProfileSnapshotRequest:
    if request.observed_at is None:
        raise ValueError("volume-drop evaluation에는 observed_at이 필요합니다.")
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
    detected = list(lifecycle.detected_incident_types)
    actions = [
        *lifecycle.recommended_actions,
        *lifecycle.backfill_actions,
        *lifecycle.validation_actions,
    ]
    return EvaluationCaseResult(
        case_name=case_name,
        expected_incident_types=(["volume_drop"] if case_name == "volume_drop" else []),
        detected_incident_types=detected,
        required_actions=(
            ["prepare_partition_backfill"] if case_name == "volume_drop" else []
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


def _single_volume_drop_incident_id(lifecycle: LifecycleResult) -> str:
    incident_ids = lifecycle.detected_incident_ids
    if len(incident_ids) != 1:
        raise ValueError("volume_drop lifecycle must produce exactly one incident")
    return incident_ids[0]
