"""Current profile 기반 incident lifecycle을 analysis-only 경계로 조합한다.

이 module은 detection, impact analysis, remediation draft까지만 계산하며 raw partition,
approval, recovery, evaluation 또는 report output을 변경하지 않는다. dbt artifact
일관성을 위한 shared lock은 lock file I/O를 수행할 수 있다.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import cast

from project_pivot.data_operations.errors import DataOperationError
from project_pivot.data_operations.lifecycle_result import LifecycleResult
from project_pivot.data_operations.request import DataOperationRequest
from project_pivot.data_platform.artifacts import (
    ArtifactProjectionLockError,
    ArtifactProjectionReadError,
    artifact_projection_id,
    artifact_projection_lock,
)
from project_pivot.data_platform.duckdb import DuckDBConnectionManager
from project_pivot.hmda_data import PartitionContentIdentity, partition_content_identity
from project_pivot.reliability import (
    DetectionRequest,
    DetectionResult,
    DetectionThresholds,
    ImpactAnalysisRequest,
    ImpactAnalysisResult,
    ProfileSnapshot,
    ProfileSnapshotRequest,
    RemediationDraft,
    RemediationDraftRequest,
    TableMetadataEvidenceRequest,
    analyze_dbt_impact,
    create_profile_snapshot,
    create_remediation_draft,
    create_table_metadata_evidence,
    detect_basic_incidents,
)

type _IncidentAnalysis = tuple[
    DetectionResult,
    ImpactAnalysisResult,
    RemediationDraft,
]


def run_incident_lifecycle(
    request: DataOperationRequest,
    baseline: ProfileSnapshot,
    *,
    thresholds: DetectionThresholds | None = None,
) -> LifecycleResult:
    """Baseline과 실제 current를 비교해 incident 분석 요약을 반환한다.

    Baseline은 current와 같은 asset과 partition이어야 한다. 실행은 raw partition,
    approval, recovery, evaluation output을 변경하지 않는 analysis-only 경계다.
    Current dbt artifact를 일관되게 읽기 위한 shared lock file I/O는 수행할 수 있다.
    Detection이 없으면 recovery proposal input identity도 반환하지 않는다.
    """

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
    with DuckDBConnectionManager(request.database_path, read_only=True) as connection:
        metadata_evidence = create_table_metadata_evidence(
            connection,
            TableMetadataEvidenceRequest(
                asset_name=request.asset_name,
                table_name=request.raw_table_name,
                observed_at=observed_at,
            ),
        )
        current = create_profile_snapshot(connection, profile_request)
        _validate_profile_compatibility(baseline, current)
        detections = detect_basic_incidents(
            DetectionRequest(
                baseline=baseline,
                current=current,
                thresholds=thresholds or DetectionThresholds(),
            )
        )
        # Impact와 projection identity가 같은 current artifact projection을 보도록
        # shared lock을 유지한 채 detection 전체를 분석한다.
        with artifact_projection_lock(
            request.dbt_manifest_path.parent,
            exclusive=False,
        ):
            analyses = [
                _analyze_detection(request, detection) for detection in detections
            ]
            dbt_projection_id = _dbt_projection_id(request) if analyses else None
        # Recovery proposal의 target identity는 실제 incident가 있을 때만 필요하다.
        target_content_identity = (
            partition_content_identity(
                connection,
                table_name=request.raw_table_name,
                source_year=request.source_year,
                source_file=request.source_file,
            )
            if analyses
            else None
        )

    return _build_lifecycle_result(
        metadata_row_count=int(cast(int, metadata_evidence.payload["row_count"])),
        baseline=baseline,
        current=current,
        analyses=analyses,
        target_content_identity=target_content_identity,
        dbt_projection_id=dbt_projection_id,
    )


def _analyze_detection(
    request: DataOperationRequest,
    detection: DetectionResult,
) -> _IncidentAnalysis:
    impact = analyze_dbt_impact(
        ImpactAnalysisRequest(
            incident=detection.incident,
            dbt_manifest_path=request.dbt_manifest_path,
            dbt_run_results_path=request.dbt_run_results_path,
        )
    )
    draft = create_remediation_draft(
        RemediationDraftRequest(
            incident=impact.incident,
            evidence=detection.evidence,
            lineage_evidence=impact.lineage_evidence,
        )
    )
    return detection, impact, draft


def _build_lifecycle_result(
    *,
    metadata_row_count: int,
    baseline: ProfileSnapshot,
    current: ProfileSnapshot,
    analyses: list[_IncidentAnalysis],
    target_content_identity: PartitionContentIdentity | None,
    dbt_projection_id: str | None,
) -> LifecycleResult:
    """Incident별 분석을 최초 관측 순서를 유지하는 caller summary로 평탄화한다."""

    return LifecycleResult(
        metadata_row_count=metadata_row_count,
        baseline_row_count=baseline.row_count,
        current_row_count=current.row_count,
        detected_incident_ids=_unique(
            detection.incident.incident_id for detection, _, _ in analyses
        ),
        detected_incident_types=_unique(
            detection.incident.incident_type for detection, _, _ in analyses
        ),
        evidence_refs=_unique(
            ref
            for detection, impact, _ in analyses
            for ref in (
                detection.evidence.evidence_id,
                impact.lineage_evidence.lineage_id,
            )
        ),
        affected_assets=_unique(
            asset
            for _, impact, _ in analyses
            for asset in impact.incident.affected_assets
        ),
        recommended_actions=_unique(
            action for _, _, draft in analyses for action in draft.recommended_actions
        ),
        backfill_actions=_unique(
            action for _, _, draft in analyses for action in draft.backfill_actions
        ),
        validation_actions=_unique(
            action for _, _, draft in analyses for action in draft.validation_actions
        ),
        target_content_identity=target_content_identity,
        dbt_projection_id=dbt_projection_id,
    )


def _dbt_projection_id(request: DataOperationRequest) -> str:
    try:
        with artifact_projection_lock(
            request.dbt_manifest_path.parent,
            exclusive=False,
        ):
            return artifact_projection_id(
                request.dbt_manifest_path,
                request.dbt_run_results_path,
            )
    except ArtifactProjectionLockError as exc:
        raise DataOperationError(
            "dbt artifact projection lock을 획득할 수 없습니다.",
            context={"directory": str(request.dbt_manifest_path.parent)},
        ) from exc
    except ArtifactProjectionReadError as exc:
        raise DataOperationError(
            "dbt artifact를 읽을 수 없습니다.",
            context={
                "run_target_path": str(request.dbt_manifest_path.parent),
                "artifact_path": str(exc.artifact_path),
            },
        ) from exc


def _validate_profile_compatibility(
    baseline: ProfileSnapshot,
    current: ProfileSnapshot,
) -> None:
    if (
        baseline.asset_name == current.asset_name
        and baseline.partition == current.partition
    ):
        return
    msg = (
        "baseline과 current profile이 호환되지 않습니다: "
        f"baseline_asset={baseline.asset_name}, current_asset={current.asset_name}, "
        f"baseline_partition={baseline.partition}, "
        f"current_partition={current.partition}"
    )
    raise DataOperationError(msg)


def _unique(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(values))
