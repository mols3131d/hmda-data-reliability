"""Read one stable dbt artifact projection to calculate downstream impact."""

from project_pivot.data_platform.artifacts import (
    ArtifactProjectionLockError,
    artifact_projection_lock,
)
from project_pivot.reliability.contracts import LineageEvidence
from project_pivot.reliability.errors import ImpactAnalysisError
from project_pivot.reliability.impact.manifest import DbtManifestGraph
from project_pivot.reliability.impact.request import ImpactAnalysisRequest
from project_pivot.reliability.impact.result import ImpactAnalysisResult


class DbtImpactAnalyzer:
    """Project an incident onto dbt lineage without changing artifact state."""

    def analyze(self, request: ImpactAnalysisRequest) -> ImpactAnalysisResult:
        """Return a copied incident with downstream assets and lineage evidence."""

        try:
            # Manifest and run results must be observed from one stable projection.
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
    """Read current dbt artifacts and calculate downstream impact for an incident."""

    return DbtImpactAnalyzer().analyze(request)


def _lineage_id(asset_name: str, partition: str) -> str:
    normalized_asset = "".join(
        character if character.isalnum() else "_" for character in asset_name.lower()
    ).strip("_")
    return f"lineage_{normalized_asset}_{partition.replace('-', '_')}"
