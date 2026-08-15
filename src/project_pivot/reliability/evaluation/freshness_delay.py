"""Deterministic Bronze ingestion freshness-delay evaluation."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import duckdb
from pydantic import BaseModel, ConfigDict

from project_pivot.data_platform.artifacts import ArtifactProjectionLockError
from project_pivot.data_platform.duckdb import DuckDBConnectionManager
from project_pivot.data_platform.sql import qualify_table_name, quote_string_literal
from project_pivot.hmda_data import (
    PartitionContentIdentity,
    load_hmda_loans_partition,
    partition_content_identity,
    partition_max_ingested_at,
)
from project_pivot.reliability.contracts import (
    Approval,
    FreshnessMeasurementStatus,
    FreshnessObservation,
    RecoveryProposal,
)
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
    from project_pivot.reliability.contracts import ProfileSnapshot

type ApprovalCallback = Callable[[RecoveryProposal], Approval]
type DbtValidationCallback = Callable[[DataOperationRequest], str]


class FreshnessDelayVerticalSliceResult(BaseModel):
    """Controlled delay, recovery, replay, and failure evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    fixture_identity: PartitionContentIdentity
    expected_recovery_identity: PartitionContentIdentity
    clean_case: EvaluationCaseResult
    freshness_delay_case: EvaluationCaseResult
    post_recovery_case: EvaluationCaseResult
    clean_freshness: FreshnessObservation
    delayed_freshness: FreshnessObservation
    recovery_freshness: FreshnessObservation | None = None
    replay_freshness: FreshnessObservation | None = None
    failure_freshness: FreshnessObservation | None = None
    recovery: BackfillValidationResult | None = None
    replay: BackfillValidationResult | None = None
    candidate_dbt_projection_id: str | None = None
    target_dbt_projection_id: str | None = None
    target_dbt_failure: str | None = None
    target_dbt_failure_context: dict[str, object] | None = None


def evaluate_freshness_delay_vertical_slice(
    *,
    request: DataOperationRequest,
    source_paths: Sequence[str | Path],
    workspace: str | Path,
    approve: ApprovalCallback,
    validate_candidate: DbtValidationCallback,
    validate_target: DbtValidationCallback,
    max_age_minutes: float = 60.0,
    delay_minutes: float = 120.0,
) -> FreshnessDelayVerticalSliceResult:
    """Evaluate a controlled Bronze ingestion delay and approved recovery."""

    from project_pivot.data_operations import run_incident_lifecycle
    from project_pivot.data_operations.errors import DataOperationError

    if request.observed_at is None:
        raise ValueError("freshness evaluation에는 observed_at이 필요합니다.")
    if max_age_minutes < 0:
        raise ValueError("max_age_minutes는 0 이상이어야 합니다.")
    if delay_minutes < max_age_minutes:
        raise ValueError("delay_minutes는 max_age_minutes 이상이어야 합니다.")

    root = Path(workspace)
    clean_database_path = root / "clean.duckdb"
    candidate_database_path = root / "candidate.duckdb"
    candidate_artifact_path = root / "freshness-candidate.parquet"
    _ensure_disposable_paths(
        request.database_path,
        clean_database_path,
        candidate_database_path,
        candidate_artifact_path,
    )
    root.mkdir(parents=True, exist_ok=True)

    scoped_source_paths = _scoped_source_paths(source_paths, request.source_file)
    thresholds = DetectionThresholds(freshness_max_age_minutes=max_age_minutes)
    target_request = request.model_copy(update={"freshness_column": "ingested_at"})
    clean_request = target_request.model_copy(
        update={"database_path": clean_database_path}
    )
    candidate_request = target_request.model_copy(
        update={
            "database_path": candidate_database_path,
            "dbt_run_target_path": root / "candidate-dbt-target",
        }
    )

    with DuckDBConnectionManager(clean_request.database_path) as connection:
        load_hmda_loans_partition(
            connection,
            scoped_source_paths,
            clean_request.source_year,
            source_file=clean_request.source_file,
            table_name=clean_request.raw_table_name,
        )
        _set_partition_ingested_at(connection, clean_request, minutes_ago=0.0)
        baseline = create_profile_snapshot(connection, _profile_request(clean_request))
        clean_freshness = _snapshot_observation(baseline)
        fixture_identity = partition_content_identity(
            connection,
            table_name=clean_request.raw_table_name,
            source_year=clean_request.source_year,
            source_file=clean_request.source_file,
        )
    clean_lifecycle = run_incident_lifecycle(
        clean_request,
        baseline,
        thresholds=thresholds,
    )

    with DuckDBConnectionManager(target_request.database_path) as connection:
        load_hmda_loans_partition(
            connection,
            scoped_source_paths,
            target_request.source_year,
            source_file=target_request.source_file,
            table_name=target_request.raw_table_name,
        )
        _set_partition_ingested_at(
            connection,
            target_request,
            minutes_ago=delay_minutes,
        )
        delayed_profile = create_profile_snapshot(
            connection,
            _profile_request(target_request),
        )
        delayed_freshness = _snapshot_observation(delayed_profile)
        target_identity = partition_content_identity(
            connection,
            table_name=target_request.raw_table_name,
            source_year=target_request.source_year,
            source_file=target_request.source_file,
        )
    delayed_lifecycle = run_incident_lifecycle(
        target_request,
        baseline,
        thresholds=thresholds,
    )

    with DuckDBConnectionManager(candidate_request.database_path) as connection:
        load_hmda_loans_partition(
            connection,
            scoped_source_paths,
            candidate_request.source_year,
            source_file=candidate_request.source_file,
            table_name=candidate_request.raw_table_name,
        )
        _set_partition_ingested_at(connection, candidate_request, minutes_ago=0.0)
        candidate_profile = create_profile_snapshot(
            connection,
            _profile_request(candidate_request),
        )
        candidate_freshness = _snapshot_observation(candidate_profile)
        candidate_identity = partition_content_identity(
            connection,
            table_name=candidate_request.raw_table_name,
            source_year=candidate_request.source_year,
            source_file=candidate_request.source_file,
        )

    control_failure = _controlled_case_failure(
        clean_lifecycle=clean_lifecycle,
        delayed_lifecycle=delayed_lifecycle,
        baseline=baseline,
        delayed_profile=delayed_profile,
        candidate_profile=candidate_profile,
        fixture_identity=fixture_identity,
        target_identity=target_identity,
        candidate_identity=candidate_identity,
        clean_freshness=clean_freshness,
        delayed_freshness=delayed_freshness,
        candidate_freshness=candidate_freshness,
        target_request=target_request,
        delay_minutes=delay_minutes,
    )
    if control_failure is not None:
        return control_failure
    candidate_freshness_at = candidate_freshness.freshness_at
    if candidate_freshness_at is None:
        raise AssertionError("controlled candidate freshness must be measured")

    try:
        candidate_projection_id = validate_candidate(candidate_request)
    except (DataOperationError, ValueError) as exc:
        return _failure_result(
            clean_lifecycle=clean_lifecycle,
            delayed_lifecycle=delayed_lifecycle,
            fixture_identity=fixture_identity,
            expected_identity=candidate_identity,
            clean_freshness=clean_freshness,
            delayed_freshness=delayed_freshness,
            target_request=target_request,
            case_name="candidate_validation_failure",
            exc=exc,
            failure_stage="before_target_mutation",
        )

    with DuckDBConnectionManager(
        candidate_request.database_path,
        read_only=True,
    ) as connection:
        connection.execute(
            f"COPY {qualify_table_name(candidate_request.raw_table_name)} "
            f"TO {quote_string_literal(candidate_artifact_path.as_posix())} "
            "(FORMAT PARQUET)"
        )

    incident_id = delayed_lifecycle.detected_incident_ids[0]
    proposal = RecoveryProposal(
        proposal_id=f"recovery_{incident_id}",
        incident_id=incident_id,
        incident_type="freshness_delay",
        table_name=target_request.raw_table_name,
        source_year=target_request.source_year,
        source_file=target_request.source_file,
        candidate_identity=candidate_identity,
        approved_before_identity=target_identity,
        expected_after_identity=candidate_identity,
        validation_evidence_refs=(
            candidate_identity.digest,
            candidate_projection_id,
            f"candidate-freshness:{candidate_freshness_at.isoformat()}",
        ),
        dbt_projection_id=candidate_projection_id,
        target_actions=("overwrite_partition", "rerun_profile_snapshot"),
        freshness_binding={
            "approved_before": delayed_freshness,
            "expected_after_freshness_at": candidate_freshness_at,
            "max_age_minutes": max_age_minutes,
        },
    )
    try:
        approval = approve(proposal)
    except (ApprovalGateError, ValueError) as exc:
        return _failure_result(
            clean_lifecycle=clean_lifecycle,
            delayed_lifecycle=delayed_lifecycle,
            fixture_identity=fixture_identity,
            expected_identity=candidate_identity,
            clean_freshness=clean_freshness,
            delayed_freshness=delayed_freshness,
            target_request=target_request,
            case_name="approval_failure",
            exc=exc,
            failure_stage="before_target_mutation",
            candidate_projection_id=candidate_projection_id,
        )

    recovery_request = ApprovedBackfillRequest(
        approval=approval,
        proposal=proposal,
        source_paths=(candidate_artifact_path,),
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
            return _failure_result(
                clean_lifecycle=clean_lifecycle,
                delayed_lifecycle=delayed_lifecycle,
                fixture_identity=fixture_identity,
                expected_identity=candidate_identity,
                clean_freshness=clean_freshness,
                delayed_freshness=delayed_freshness,
                target_request=target_request,
                case_name=_recovery_failure_case_name(exc),
                exc=exc,
                failure_stage=failure_stage,
                reconciliation_action=_reconciliation_action(exc, failure_stage),
                candidate_projection_id=candidate_projection_id,
            )
        recovery_validation_evidence = _validation_failure_evidence(
            recovery,
            candidate_identity,
        )
        if recovery_validation_evidence:
            return _failure_result(
                clean_lifecycle=clean_lifecycle,
                delayed_lifecycle=delayed_lifecycle,
                fixture_identity=fixture_identity,
                expected_identity=candidate_identity,
                clean_freshness=clean_freshness,
                delayed_freshness=delayed_freshness,
                target_request=target_request,
                case_name="recovery_validation_failure",
                failure_stage="after_partition_mutation",
                reconciliation_action="resume_verification",
                recovery=recovery,
                candidate_projection_id=candidate_projection_id,
                evidence_refs=recovery_validation_evidence,
            )
        try:
            replay = execute_approved_backfill(connection, recovery_request)
        except (ApprovalGateError, BackfillValidationError) as exc:
            return _failure_result(
                clean_lifecycle=clean_lifecycle,
                delayed_lifecycle=delayed_lifecycle,
                fixture_identity=fixture_identity,
                expected_identity=candidate_identity,
                clean_freshness=clean_freshness,
                delayed_freshness=delayed_freshness,
                target_request=target_request,
                case_name="replay_failure",
                exc=exc,
                failure_stage="after_partition_mutation",
                reconciliation_action=_reconciliation_action(
                    exc,
                    "after_partition_mutation",
                ),
                recovery=recovery,
                candidate_projection_id=candidate_projection_id,
            )
        replay_validation_evidence = _validation_failure_evidence(
            replay,
            candidate_identity,
        )
        if replay_validation_evidence:
            return _failure_result(
                clean_lifecycle=clean_lifecycle,
                delayed_lifecycle=delayed_lifecycle,
                fixture_identity=fixture_identity,
                expected_identity=candidate_identity,
                clean_freshness=clean_freshness,
                delayed_freshness=delayed_freshness,
                target_request=target_request,
                case_name="replay_validation_failure",
                failure_stage="after_partition_mutation",
                reconciliation_action="resume_verification",
                recovery=recovery,
                replay=replay,
                candidate_projection_id=candidate_projection_id,
                evidence_refs=replay_validation_evidence,
            )

    try:
        post_lifecycle = run_incident_lifecycle(
            target_request,
            baseline,
            thresholds=thresholds,
        )
    except (ArtifactProjectionLockError, DataOperationError, ReliabilityError) as exc:
        return _failure_result(
            clean_lifecycle=clean_lifecycle,
            delayed_lifecycle=delayed_lifecycle,
            fixture_identity=fixture_identity,
            expected_identity=candidate_identity,
            clean_freshness=clean_freshness,
            delayed_freshness=delayed_freshness,
            target_request=target_request,
            case_name="post_recovery_lifecycle_failure",
            exc=exc,
            failure_stage="after_partition_mutation",
            reconciliation_action="resume_verification",
            recovery=recovery,
            replay=replay,
            candidate_projection_id=candidate_projection_id,
        )
    if post_lifecycle.detected_incident_types:
        return _failure_result(
            clean_lifecycle=clean_lifecycle,
            delayed_lifecycle=delayed_lifecycle,
            fixture_identity=fixture_identity,
            expected_identity=candidate_identity,
            clean_freshness=clean_freshness,
            delayed_freshness=delayed_freshness,
            target_request=target_request,
            case_name="unresolved_post_recovery_incident",
            failure_stage="after_partition_mutation",
            reconciliation_action="resume_verification",
            recovery=recovery,
            replay=replay,
            candidate_projection_id=candidate_projection_id,
            detected_incident_types=post_lifecycle.detected_incident_types,
            evidence_refs=post_lifecycle.evidence_refs,
        )

    try:
        target_projection_id = validate_target(target_request)
    except (DataOperationError, ValueError) as exc:
        context = getattr(exc, "context", None)
        failure_context = dict(context) if isinstance(context, dict) else None
        result = _failure_result(
            clean_lifecycle=clean_lifecycle,
            delayed_lifecycle=delayed_lifecycle,
            fixture_identity=fixture_identity,
            expected_identity=candidate_identity,
            clean_freshness=clean_freshness,
            delayed_freshness=delayed_freshness,
            target_request=target_request,
            case_name="recovery_dbt_failure",
            exc=exc,
            failure_stage="after_partition_mutation",
            reconciliation_action="resume_verification",
            recovery=recovery,
            replay=replay,
            candidate_projection_id=candidate_projection_id,
            detected_incident_types=post_lifecycle.detected_incident_types,
        )
        return result.model_copy(
            update={
                "target_dbt_failure": str(exc),
                "target_dbt_failure_context": failure_context,
            }
        )

    return FreshnessDelayVerticalSliceResult(
        fixture_identity=fixture_identity,
        expected_recovery_identity=candidate_identity,
        clean_case=_case_result("clean", clean_lifecycle),
        freshness_delay_case=_case_result("freshness_delay", delayed_lifecycle),
        post_recovery_case=_case_result("post_recovery", post_lifecycle),
        clean_freshness=clean_freshness,
        delayed_freshness=delayed_freshness,
        recovery_freshness=recovery.actual_freshness,
        replay_freshness=replay.actual_freshness,
        recovery=recovery,
        replay=replay,
        candidate_dbt_projection_id=candidate_projection_id,
        target_dbt_projection_id=target_projection_id,
    )


def _validation_failure_evidence(
    result: BackfillValidationResult,
    expected_identity: PartitionContentIdentity,
) -> list[str]:
    if (
        result.validation_passed
        and result.actual_identity == expected_identity
        and result.freshness_validation_passed is True
        and result.actual_freshness is not None
    ):
        return []
    return [
        f"content-validation:{result.validation_passed}",
        f"freshness-validation:{result.freshness_validation_passed}",
        f"actual-identity:{result.actual_identity.model_dump_json()}",
        f"expected-identity:{expected_identity.model_dump_json()}",
        (
            "actual-freshness:"
            + (
                result.actual_freshness.model_dump_json()
                if result.actual_freshness is not None
                else "None"
            )
        ),
    ]


def _controlled_case_failure(
    *,
    clean_lifecycle: LifecycleResult,
    delayed_lifecycle: LifecycleResult,
    baseline: ProfileSnapshot,
    delayed_profile: ProfileSnapshot,
    candidate_profile: ProfileSnapshot,
    fixture_identity: PartitionContentIdentity,
    target_identity: PartitionContentIdentity,
    candidate_identity: PartitionContentIdentity,
    clean_freshness: FreshnessObservation,
    delayed_freshness: FreshnessObservation,
    candidate_freshness: FreshnessObservation,
    target_request: DataOperationRequest,
    delay_minutes: float,
) -> FreshnessDelayVerticalSliceResult | None:
    evidence: list[str] = []
    if clean_lifecycle.detected_incident_types:
        evidence.append(f"clean-incidents:{clean_lifecycle.detected_incident_types}")
    if (
        delayed_lifecycle.detected_incident_types != ["freshness_delay"]
        or len(delayed_lifecycle.detected_incident_ids) != 1
    ):
        evidence.append(
            f"delayed-incidents:{delayed_lifecycle.detected_incident_types}"
        )
    if not fixture_identity == target_identity == candidate_identity:
        evidence.append("content-identity-mismatch")
    schema_hashes = {
        baseline.schema_hash,
        delayed_profile.schema_hash,
        candidate_profile.schema_hash,
    }
    if len(schema_hashes) != 1:
        evidence.append("schema-hash-mismatch")
    assert target_request.observed_at is not None
    expected_clean_freshness_at = target_request.observed_at
    expected_delayed_freshness_at = target_request.observed_at - timedelta(
        minutes=delay_minutes
    )
    if clean_freshness.freshness_at != expected_clean_freshness_at:
        evidence.append(
            "clean-freshness-mismatch:"
            f"expected={expected_clean_freshness_at.isoformat()}:"
            f"actual={_timestamp_text(clean_freshness.freshness_at)}"
        )
    if delayed_freshness.freshness_at != expected_delayed_freshness_at:
        evidence.append(
            "delayed-freshness-mismatch:"
            f"expected={expected_delayed_freshness_at.isoformat()}:"
            f"actual={_timestamp_text(delayed_freshness.freshness_at)}"
        )
    if candidate_freshness.freshness_at != expected_clean_freshness_at:
        evidence.append(
            "candidate-freshness-mismatch:"
            f"expected={expected_clean_freshness_at.isoformat()}:"
            f"actual={_timestamp_text(candidate_freshness.freshness_at)}"
        )
    if candidate_freshness.freshness_status is FreshnessMeasurementStatus.UNAVAILABLE:
        evidence.append("candidate-freshness-unavailable")
    if not evidence:
        return None
    return _failure_result(
        clean_lifecycle=clean_lifecycle,
        delayed_lifecycle=delayed_lifecycle,
        fixture_identity=fixture_identity,
        expected_identity=candidate_identity,
        clean_freshness=clean_freshness,
        delayed_freshness=delayed_freshness,
        target_request=target_request,
        case_name="unachieved_controlled_defect",
        failure_stage="before_target_mutation",
        evidence_refs=[
            *evidence,
            f"freshness:candidate:{candidate_freshness.model_dump_json()}",
        ],
    )


def _failure_result(
    *,
    clean_lifecycle: LifecycleResult,
    delayed_lifecycle: LifecycleResult,
    fixture_identity: PartitionContentIdentity,
    expected_identity: PartitionContentIdentity,
    clean_freshness: FreshnessObservation,
    delayed_freshness: FreshnessObservation,
    target_request: DataOperationRequest,
    case_name: str,
    failure_stage: str,
    exc: Exception | None = None,
    evidence_refs: Sequence[str] = (),
    reconciliation_action: str | None = None,
    recovery: BackfillValidationResult | None = None,
    replay: BackfillValidationResult | None = None,
    candidate_projection_id: str | None = None,
    detected_incident_types: Sequence[str] | None = None,
) -> FreshnessDelayVerticalSliceResult:
    evidence = list(evidence_refs)
    if exc is not None:
        evidence.extend((f"failure:{type(exc).__name__}", str(exc)))
        context = getattr(exc, "context", None)
        if isinstance(context, dict):
            evidence.extend(f"{key}:{value}" for key, value in sorted(context.items()))
    failure_freshness = _observe_target_freshness(target_request)
    for stage, observation in (
        ("clean", clean_freshness),
        ("delayed", delayed_freshness),
        ("recovery", recovery.actual_freshness if recovery is not None else None),
        ("replay", replay.actual_freshness if replay is not None else None),
        ("failure", failure_freshness),
    ):
        if observation is not None:
            evidence.append(f"freshness:{stage}:{observation.model_dump_json()}")
    failure_case = build_recovery_evaluation_case(
        case_name=case_name,
        expected_incident_types=([] if recovery is not None else ["freshness_delay"]),
        detected_incident_types=(
            list(detected_incident_types)
            if detected_incident_types is not None
            else delayed_lifecycle.detected_incident_types
        ),
        recovery=recovery,
        failure_stage=failure_stage,
        reconciliation_action=reconciliation_action,
        evidence_refs=evidence,
    )
    return FreshnessDelayVerticalSliceResult(
        fixture_identity=fixture_identity,
        expected_recovery_identity=expected_identity,
        clean_case=_case_result("clean", clean_lifecycle),
        freshness_delay_case=_case_result("freshness_delay", delayed_lifecycle),
        post_recovery_case=failure_case,
        clean_freshness=clean_freshness,
        delayed_freshness=delayed_freshness,
        recovery_freshness=recovery.actual_freshness if recovery is not None else None,
        replay_freshness=replay.actual_freshness if replay is not None else None,
        failure_freshness=failure_freshness,
        recovery=recovery,
        replay=replay,
        candidate_dbt_projection_id=candidate_projection_id,
    )


def _set_partition_ingested_at(
    connection: duckdb.DuckDBPyConnection,
    request: DataOperationRequest,
    *,
    minutes_ago: float,
) -> None:
    assert request.observed_at is not None
    source_file_filter = (
        "" if request.source_file is None else "AND source_file_name = ?"
    )
    params: list[object] = [
        request.observed_at - timedelta(minutes=minutes_ago),
        request.source_year,
    ]
    if request.source_file is not None:
        params.append(request.source_file)
    connection.execute(
        f"""
        UPDATE {qualify_table_name(request.raw_table_name)}
        SET ingested_at = ?
        WHERE source_year = ?
        {source_file_filter}
        """,
        params,
    )


def _profile_request(request: DataOperationRequest) -> ProfileSnapshotRequest:
    assert request.observed_at is not None
    return ProfileSnapshotRequest(
        asset_name=request.asset_name,
        table_name=request.raw_table_name,
        partition_column=request.partition_column,
        partition=request.source_year,
        profile_columns=request.profile_columns,
        freshness_column="ingested_at",
        observed_at=request.observed_at,
    )


def _snapshot_observation(snapshot: ProfileSnapshot) -> FreshnessObservation:
    return FreshnessObservation(
        freshness_status=snapshot.freshness_status,
        freshness_at=snapshot.freshness_at,
        observed_at=snapshot.observed_at,
    )


def _observe_target_freshness(
    request: DataOperationRequest,
) -> FreshnessObservation | None:
    assert request.observed_at is not None
    try:
        with DuckDBConnectionManager(
            request.database_path,
            read_only=True,
        ) as connection:
            freshness_at = partition_max_ingested_at(
                connection,
                table_name=request.raw_table_name,
                source_year=request.source_year,
                source_file=request.source_file,
            )
        return FreshnessObservation(
            freshness_status=(
                FreshnessMeasurementStatus.MEASURED
                if freshness_at is not None
                else FreshnessMeasurementStatus.UNAVAILABLE
            ),
            freshness_at=freshness_at,
            observed_at=request.observed_at,
        )
    except (OSError, duckdb.Error, ValueError):
        return None


def _case_result(case_name: str, lifecycle: LifecycleResult) -> EvaluationCaseResult:
    actions = list(
        dict.fromkeys(
            [
                *lifecycle.recommended_actions,
                *lifecycle.backfill_actions,
                *lifecycle.validation_actions,
            ]
        )
    )
    is_delay = case_name == "freshness_delay"
    return EvaluationCaseResult(
        case_name=case_name,
        expected_incident_types=["freshness_delay"] if is_delay else [],
        detected_incident_types=list(lifecycle.detected_incident_types),
        required_actions=["check_bronze_ingestion_freshness"] if is_delay else [],
        remediation_actions=actions,
        evidence_refs=list(lifecycle.evidence_refs),
    )


def _ensure_disposable_paths(*paths: Path) -> None:
    existing_paths = [path for path in paths if path.exists() or path.is_symlink()]
    if existing_paths:
        joined_paths = ", ".join(str(path) for path in existing_paths)
        raise ValueError(
            f"freshness evaluation artifact는 새 path여야 합니다: {joined_paths}"
        )
    resolved_paths = [path.resolve(strict=False) for path in paths]
    if len(set(resolved_paths)) != len(resolved_paths):
        raise ValueError("freshness evaluation path는 서로 달라야 합니다.")


def _scoped_source_paths(
    source_paths: Sequence[str | Path],
    source_file: str | None,
) -> tuple[str | Path, ...]:
    if source_file is None:
        return tuple(source_paths)
    scoped = tuple(path for path in source_paths if Path(path).name == source_file)
    if not scoped:
        raise ValueError(
            f"source_file scope에 해당하는 source가 없습니다: {source_file}"
        )
    return scoped


def _failure_stage(exc: Exception) -> str:
    if getattr(exc, "mutation_state", None) in {
        "partition_changed",
        "diverged_after_profile_failure",
    }:
        return "after_partition_mutation"
    return "before_target_mutation"


def _recovery_failure_case_name(exc: Exception) -> str:
    message = str(exc)
    if "candidate freshness" in message or "candidate content" in message:
        return "invalid_candidate"
    if "새 validation" in message or "compound state" in message:
        return "stale_target"
    if "필요한 action" in message or "승인되지 않은" in message:
        return "incomplete_approval"
    return "recovery_failure"


def _reconciliation_action(exc: Exception, failure_stage: str) -> str | None:
    exception_action = getattr(exc, "reconciliation_action", None)
    if exception_action is not None:
        return exception_action
    if "새 validation" in str(exc) or "compound state" in str(exc):
        return "request_new_validation_and_approval"
    if failure_stage == "after_partition_mutation":
        return "resume_verification"
    return None


def _timestamp_text(value: datetime | None) -> str:
    return value.isoformat() if value is not None else "None"
