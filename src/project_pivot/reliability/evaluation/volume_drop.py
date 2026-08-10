"""Deterministic volume-drop recovery evaluation."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING

import duckdb
from pydantic import BaseModel, ConfigDict

from project_pivot.data_platform.artifacts import (
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
    recovery: BackfillValidationResult
    replay: BackfillValidationResult
    candidate_dbt_projection_id: str
    target_dbt_projection_id: str | None = None
    target_dbt_failure: str | None = None


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
    """Run clean, controlled volume-drop, approved recovery, and replay."""

    from project_pivot.data_operations import run_incident_lifecycle

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
    candidate_projection_id = validate_candidate(candidate_request)
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
    approval = approve(proposal)
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
        recovery = execute_approved_backfill(connection, recovery_request)
        replay = execute_approved_backfill(connection, recovery_request)
    post_recovery_lifecycle = run_incident_lifecycle(target_request, baseline)
    with artifact_projection_lock(
        target_request.dbt_manifest_path.parent,
        exclusive=False,
    ):
        prior_target_projection_id = artifact_projection_id(
            target_request.dbt_manifest_path,
            target_request.dbt_run_results_path,
        )
    try:
        target_projection_id = validate_target(target_request)
        target_dbt_failure = None
        post_recovery_case = _case_result("post_recovery", post_recovery_lifecycle)
    except Exception as exc:
        target_projection_id = None
        target_dbt_failure = str(exc)
        post_recovery_case = build_recovery_evaluation_case(
            case_name="recovery_dbt_failure",
            expected_incident_types=[],
            detected_incident_types=post_recovery_lifecycle.detected_incident_types,
            recovery=recovery,
            failure_stage="after_partition_mutation",
            evidence_refs=[target_dbt_failure],
            artifact_projection_ids=[prior_target_projection_id],
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
    )


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
