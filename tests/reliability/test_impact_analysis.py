"""dbt impact analysis 테스트."""

from __future__ import annotations

import json
from pathlib import Path

from project_pivot.reliability import (
    ImpactAnalysisRequest,
    Incident,
    IncidentSeverity,
    IncidentStatus,
    analyze_dbt_impact,
)


def test_impact_analysis_finds_downstream_from_source(tmp_path: Path) -> None:
    """source asset에서 staging/mart downstream을 계산한다."""
    manifest_path = _write_manifest(tmp_path)
    run_results_path = _write_run_results(tmp_path)
    incident = _incident("source.project_pivot.raw.yellow_tripdata")

    result = analyze_dbt_impact(
        ImpactAnalysisRequest(
            incident=incident,
            dbt_manifest_path=manifest_path,
            dbt_run_results_path=run_results_path,
        )
    )

    assert result.lineage_evidence.downstream_assets == [
        "stg_yellow_tripdata",
        "mart_daily_taxi_trips",
    ]
    assert result.incident.affected_assets == [
        "stg_yellow_tripdata",
        "mart_daily_taxi_trips",
    ]


def test_impact_analysis_resolves_model_name_and_node_id(tmp_path: Path) -> None:
    """model name과 node id 입력을 모두 dbt asset으로 해석한다."""
    manifest_path = _write_manifest(tmp_path)
    run_results_path = _write_run_results(tmp_path)

    by_name = analyze_dbt_impact(
        ImpactAnalysisRequest(
            incident=_incident("stg_yellow_tripdata"),
            dbt_manifest_path=manifest_path,
            dbt_run_results_path=run_results_path,
        )
    )
    by_node_id = analyze_dbt_impact(
        ImpactAnalysisRequest(
            incident=_incident("model.project_pivot.stg_yellow_tripdata"),
            dbt_manifest_path=manifest_path,
            dbt_run_results_path=run_results_path,
        )
    )

    assert by_name.incident.affected_assets == ["mart_daily_taxi_trips"]
    assert by_node_id.incident.affected_assets == ["mart_daily_taxi_trips"]


def test_impact_analysis_builds_lineage_evidence_paths(tmp_path: Path) -> None:
    """LineageEvidence path와 incident 연결을 검증한다."""
    manifest_path = _write_manifest(tmp_path)
    run_results_path = _write_run_results(tmp_path)
    incident = _incident("source.project_pivot.raw.yellow_tripdata")

    result = analyze_dbt_impact(
        ImpactAnalysisRequest(
            incident=incident,
            dbt_manifest_path=manifest_path,
            dbt_run_results_path=run_results_path,
        )
    )

    assert result.lineage_evidence.upstream_asset == incident.asset_name
    assert result.lineage_evidence.dbt_manifest_path == str(manifest_path)
    assert result.lineage_evidence.dbt_run_results_path == str(run_results_path)
    assert result.incident.evidence_refs == incident.evidence_refs


def _incident(asset_name: str) -> Incident:
    return Incident(
        incident_id="inc_2024_01_01",
        asset_name=asset_name,
        partition="2024-01-01",
        incident_type="volume_drop",
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.DETECTED,
        owner="data-platform",
        evidence_refs=["ev_2024_01_01"],
    )


def _write_manifest(tmp_path: Path) -> Path:
    manifest_path = tmp_path / "manifest.json"
    manifest = {
        "sources": {
            "source.project_pivot.raw.yellow_tripdata": {
                "name": "yellow_tripdata",
                "schema": "raw",
                "resource_type": "source",
                "depends_on": {"nodes": []},
            }
        },
        "nodes": {
            "model.project_pivot.stg_yellow_tripdata": {
                "name": "stg_yellow_tripdata",
                "alias": "stg_yellow_tripdata",
                "schema": "staging",
                "resource_type": "model",
                "depends_on": {
                    "nodes": ["source.project_pivot.raw.yellow_tripdata"]
                },
            },
            "model.project_pivot.mart_daily_taxi_trips": {
                "name": "mart_daily_taxi_trips",
                "alias": "mart_daily_taxi_trips",
                "schema": "marts",
                "resource_type": "model",
                "depends_on": {
                    "nodes": ["model.project_pivot.stg_yellow_tripdata"]
                },
            },
        },
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


def _write_run_results(tmp_path: Path) -> Path:
    run_results_path = tmp_path / "run_results.json"
    run_results_path.write_text("{}", encoding="utf-8")
    return run_results_path
