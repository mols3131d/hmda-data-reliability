"""계통(Lineage) 증거 계약 모델 정의 모듈."""

from pydantic import Field

from hmda_reliability.reliability.contracts.base import ReliabilityContract


class LineageEvidence(ReliabilityContract):
    """dbt 매니페스트 기반의 다운스트림 영향 계통 증거 계약."""

    lineage_id: str
    upstream_asset: str
    downstream_assets: list[str] = Field(default_factory=list)
    dbt_manifest_path: str
    dbt_run_results_path: str
