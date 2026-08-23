"""Lineage contract models."""

from pydantic import Field

from project_pivot.reliability.contracts.base import ReliabilityContract


class LineageEvidence(ReliabilityContract):
    lineage_id: str
    upstream_asset: str
    downstream_assets: list[str] = Field(default_factory=list)
    dbt_manifest_path: str
    dbt_run_results_path: str
