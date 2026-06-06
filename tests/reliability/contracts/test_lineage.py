"""Lineage contract tests."""

from project_pivot.reliability.contracts import (
    Incident,
    IncidentSeverity,
    IncidentStatus,
    LineageEvidence,
)


def test_lineage_evidence_can_feed_incident_affected_assets() -> None:
    """LineageEvidence downstream asset이 incident 영향 범위로 연결되는지 검증한다."""
    lineage = LineageEvidence(
        lineage_id="lineage_daily_taxi_revenue_2026_06_05",
        upstream_asset="mart.daily_taxi_revenue",
        downstream_assets=["mart.revenue_dashboard"],
        dbt_manifest_path="target/manifest.json",
        dbt_run_results_path="target/run_results.json",
    )
    incident = Incident(
        incident_id="inc_daily_taxi_revenue_2026_06_05",
        asset_name=lineage.upstream_asset,
        partition="2026-06-05",
        incident_type="volume_drop",
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.DETECTED,
        owner="data-platform",
        evidence_refs=["ev_profile_daily_taxi_revenue_2026_06_05"],
        affected_assets=lineage.downstream_assets,
    )

    assert incident.affected_assets == ["mart.revenue_dashboard"]
