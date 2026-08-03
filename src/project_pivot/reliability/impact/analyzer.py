"""dbt manifest 기반 impact analysis."""

from project_pivot.reliability.contracts import LineageEvidence
from project_pivot.reliability.errors import ImpactAnalysisError
from project_pivot.reliability.impact.manifest import DbtManifestGraph
from project_pivot.reliability.impact.request import ImpactAnalysisRequest
from project_pivot.reliability.impact.result import ImpactAnalysisResult


class DbtImpactAnalyzer:
    """incident asset의 downstream dbt 영향을 계산한다."""

    def analyze(self, request: ImpactAnalysisRequest) -> ImpactAnalysisResult:
        """LineageEvidence와 affected assets가 채워진 incident를 반환한다."""

        graph = DbtManifestGraph.from_path(request.dbt_manifest_path)
        if not request.dbt_run_results_path.is_file():
            msg = (
                "dbt run results를 찾을 수 없습니다: "
                f"path={request.dbt_run_results_path}"
            )
            raise ImpactAnalysisError(msg)
        downstream_assets = graph.downstream_assets(request.incident.asset_name)
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
    """기본 dbt impact analyzer를 실행한다."""

    return DbtImpactAnalyzer().analyze(request)


def _lineage_id(asset_name: str, partition: str) -> str:
    normalized_asset = "".join(
        character if character.isalnum() else "_" for character in asset_name.lower()
    ).strip("_")
    return f"lineage_{normalized_asset}_{partition.replace('-', '_')}"
