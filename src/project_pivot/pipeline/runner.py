"""MVP pipeline runner."""

from __future__ import annotations

import os
import subprocess
from datetime import UTC, datetime
from typing import cast

from project_pivot.data_platform.duckdb import DuckDBConnectionManager
from project_pivot.hmda_data import discover_hmda_files, load_hmda_loans_partition
from project_pivot.pipeline.dbt_result import DbtBuildResult
from project_pivot.pipeline.errors import PipelineRuntimeError
from project_pivot.pipeline.lifecycle_result import MvpLifecycleResult
from project_pivot.pipeline.raw_result import RawLoadResult
from project_pivot.pipeline.request import MvpPipelineRunRequest
from project_pivot.pipeline.result import MvpPipelineRunResult
from project_pivot.reliability import (
    Approval,
    ApprovalStatus,
    ApprovedBackfillRequest,
    DetectionRequest,
    EvaluationCaseResult,
    ImpactAnalysisRequest,
    ProfileSnapshotRequest,
    RemediationDraftRequest,
    TableMetadataEvidenceRequest,
    analyze_dbt_impact,
    build_evaluation_report,
    create_profile_snapshot,
    create_remediation_draft,
    create_table_metadata_evidence,
    detect_basic_incidents,
    execute_approved_backfill,
    write_evaluation_report,
)
from project_pivot.reliability.detection import DetectionResult
from project_pivot.reliability.impact import ImpactAnalysisResult


def run_mvp_pipeline(request: MvpPipelineRunRequest) -> MvpPipelineRunResult:
    """raw load부터 evaluation report까지 MVP pipeline을 실행한다."""

    raw_load = load_raw_data(request)
    dbt_build = run_dbt_build(request) if request.run_dbt_build else None
    lifecycle = run_incident_lifecycle(request)
    return MvpPipelineRunResult(
        status="completed",
        raw_load=raw_load,
        dbt_build=dbt_build,
        lifecycle=lifecycle,
    )


def load_raw_data(request: MvpPipelineRunRequest) -> RawLoadResult:
    """원천 파일을 DuckDB raw table로 멱등 적재한다."""

    hmda_paths = discover_hmda_files(request.source_root)
    with DuckDBConnectionManager(request.database_path) as connection:
        hmda_loans_row_count = load_hmda_loans_partition(
            connection,
            hmda_paths,
            request.source_year,
            source_file=request.source_file,
            table_name=request.raw_table_name,
        )
    return RawLoadResult(
        database_path=request.database_path,
        source_root=request.source_root,
        source_file_count=len(hmda_paths),
        source_year=request.source_year,
        source_file=request.source_file,
        hmda_loans_row_count=hmda_loans_row_count,
    )


def run_dbt_build(request: MvpPipelineRunRequest) -> DbtBuildResult:
    """dbt build를 실행하고 artifact 경로를 반환한다."""

    command = [
        "dbt",
        "build",
        "--project-dir",
        str(request.dbt_project_dir),
        "--profiles-dir",
        str(request.dbt_profiles_dir),
    ]
    env = os.environ.copy()
    env["PROJECT_PIVOT_DUCKDB_PATH"] = str(request.database_path)
    env["DBT_PROFILES_DIR"] = str(request.dbt_profiles_dir)
    env["DBT_SEND_ANONYMOUS_USAGE_STATS"] = "false"
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        env=env,
        text=True,
    )
    if result.returncode != 0:
        msg = (
            "dbt build 실행에 실패했습니다: "
            f"return_code={result.returncode}, stderr={result.stderr[-1000:]}"
        )
        raise PipelineRuntimeError(msg)
    return DbtBuildResult(
        command=command,
        return_code=result.returncode,
        manifest_path=request.dbt_manifest_path,
        run_results_path=request.dbt_run_results_path,
        succeeded=True,
    )


def run_incident_lifecycle(request: MvpPipelineRunRequest) -> MvpLifecycleResult:
    """evidence, detection, impact, remediation, recovery, evaluation을 실행한다."""

    observed_at = request.observed_at or datetime.now(UTC)
    profile_request = ProfileSnapshotRequest(
        asset_name=request.asset_name,
        table_name=request.raw_table_name,
        partition_column=request.partition_column,
        partition=request.source_year,
        profile_columns=request.profile_columns,
        freshness_column=request.freshness_column,
        observed_at=observed_at,
    )
    with DuckDBConnectionManager(
        request.database_path,
        read_only=not request.run_backfill,
    ) as connection:
        metadata_evidence = create_table_metadata_evidence(
            connection,
            TableMetadataEvidenceRequest(
                asset_name=request.asset_name,
                table_name=request.raw_table_name,
                observed_at=observed_at,
            ),
        )
        baseline = create_profile_snapshot(connection, profile_request)
        current_row_count = max(
            1,
            int(baseline.row_count * request.simulate_row_count_ratio),
        )
        current = baseline.model_copy(
            update={
                "snapshot_id": "profile_mvp_pipeline_current",
                "row_count": current_row_count,
                "metric_values": {"row_count": float(current_row_count)},
            }
        )
        detections = detect_basic_incidents(
            DetectionRequest(baseline=baseline, current=current)
        )
        primary_detection = detections[0] if detections else None

        impact_result = None
        remediation_draft = None
        backfill_result = None
        if primary_detection is not None:
            impact_result = analyze_dbt_impact(
                ImpactAnalysisRequest(
                    incident=primary_detection.incident,
                    dbt_manifest_path=request.dbt_manifest_path,
                    dbt_run_results_path=request.dbt_run_results_path,
                )
            )
            remediation_draft = create_remediation_draft(
                RemediationDraftRequest(
                    incident=impact_result.incident,
                    evidence=primary_detection.evidence,
                    lineage_evidence=impact_result.lineage_evidence,
                )
            )
        if request.run_backfill and primary_detection is not None:
            approval = Approval(
                approval_id=f"approval_{primary_detection.incident.incident_id}",
                incident_id=primary_detection.incident.incident_id,
                status=ApprovalStatus.APPROVED,
                requested_by="mvp_pipeline",
                requested_at=observed_at,
                approved_by="mvp_pipeline",
                approved_at=observed_at,
                requested_actions=["overwrite_partition", "rerun_profile_snapshot"],
                reason="MVP pipeline 자동 복구 검증",
            )
            backfill_result = execute_approved_backfill(
                connection,
                ApprovedBackfillRequest(
                    approval=approval,
                    source_paths=tuple(discover_hmda_files(request.source_root)),
                    source_year=request.source_year,
                    source_file=request.source_file,
                    profile_request=profile_request,
                    table_name=request.raw_table_name,
                ),
            )

    detected_types = [result.incident.incident_type for result in detections]
    evidence_refs = _evidence_refs(primary_detection, impact_result)
    affected_assets = (
        impact_result.incident.affected_assets if impact_result is not None else []
    )
    recommended_actions = (
        remediation_draft.recommended_actions if remediation_draft is not None else []
    )
    backfill_actions = (
        remediation_draft.backfill_actions if remediation_draft is not None else []
    )
    validation_actions = (
        remediation_draft.validation_actions if remediation_draft is not None else []
    )
    report = build_evaluation_report(
        [
            EvaluationCaseResult(
                case_name="mvp_pipeline_volume_drop",
                expected_incident_types=["volume_drop"],
                detected_incident_types=detected_types,
                required_actions=["prepare_partition_backfill"],
                remediation_actions=recommended_actions,
                evidence_refs=evidence_refs,
            )
        ],
        generated_at=observed_at,
    )
    report_path = write_evaluation_report(report, request.report_path)
    return MvpLifecycleResult(
        metadata_row_count=int(cast(int, metadata_evidence.payload["row_count"])),
        baseline_row_count=baseline.row_count,
        current_row_count=current_row_count,
        detected_incident_types=detected_types,
        evidence_refs=evidence_refs,
        affected_assets=affected_assets,
        recommended_actions=recommended_actions,
        backfill_actions=backfill_actions,
        validation_actions=validation_actions,
        backfill_validation_passed=(
            backfill_result.validation_passed if backfill_result is not None else None
        ),
        evaluation_report_path=report_path,
        detection_success_rate=report.detection_success_rate,
        action_success_rate=report.action_success_rate,
    )


def _evidence_refs(
    primary_detection: DetectionResult | None,
    impact_result: ImpactAnalysisResult | None,
) -> list[str]:
    refs: list[str] = []
    if primary_detection is not None:
        refs.append(primary_detection.evidence.evidence_id)
    if impact_result is not None:
        refs.append(impact_result.lineage_evidence.lineage_id)
    return refs
