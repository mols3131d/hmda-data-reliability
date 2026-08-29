"""공유 아티팩트 reader 락 하에서 dbt 매니페스트 계통(lineage)을 분석한다."""

from hmda_reliability.data_platform.artifacts import (
    ArtifactProjectionLockError,
    artifact_projection_lock,
)
from hmda_reliability.reliability.contracts import LineageEvidence
from hmda_reliability.reliability.errors import ImpactAnalysisError
from hmda_reliability.reliability.impact.manifest import DbtManifestGraph
from hmda_reliability.reliability.impact.request import ImpactAnalysisRequest
from hmda_reliability.reliability.impact.result import ImpactAnalysisResult


class DbtImpactAnalyzer:
    """아티팩트 변경 없이 incident에 downstream dbt 계통 evidence를 연결한다."""

    def analyze(self, request: ImpactAnalysisRequest) -> ImpactAnalysisResult:
        """복사된 incident와 계통 evidence를 반환한다; run-results 파일이 필요하다."""

        try:
            # Share the manifest directory's reader lock with artifact promotion.
            with artifact_projection_lock(
                request.dbt_manifest_path.parent,
                exclusive=False,
            ):
                graph = DbtManifestGraph.from_path(request.dbt_manifest_path)
                if not request.dbt_run_results_path.is_file():
                    msg = (
                        "dbt run results를 찾을 수 없습니다: "
                        f"path={request.dbt_run_results_path}"
                    )
                    raise ImpactAnalysisError(msg)
                downstream_assets = graph.downstream_assets(request.incident.asset_name)
        except ArtifactProjectionLockError as exc:
            raise ImpactAnalysisError(
                "dbt artifact projection lock을 획득할 수 없습니다."
            ) from exc
        lineage_evidence = LineageEvidence(
            lineage_id=_lineage_id(
                request.incident.asset_name,
                request.incident.partition,
            ),
            upstream_asset=request.incident.asset_name,
            downstream_assets=downstream_assets,
            dbt_manifest_path=str(request.dbt_manifest_path),
            dbt_run_results_path=str(request.dbt_run_results_path),
        )
        incident = request.incident.model_copy(
            update={"affected_assets": downstream_assets}
        )
        return ImpactAnalysisResult(
            incident=incident,
            lineage_evidence=lineage_evidence,
        )


def analyze_dbt_impact(request: ImpactAnalysisRequest) -> ImpactAnalysisResult:
    """매니페스트 계통 및 기록된 아티팩트 경로로부터 다운스트림 영향을 계산한다."""

    return DbtImpactAnalyzer().analyze(request)


def _lineage_id(asset_name: str, partition: str) -> str:
    normalized_asset = "".join(
        character if character.isalnum() else "_" for character in asset_name.lower()
    ).strip("_")
    return f"lineage_{normalized_asset}_{partition.replace('-', '_')}"
