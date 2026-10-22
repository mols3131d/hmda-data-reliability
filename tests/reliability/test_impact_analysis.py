"""dbt impact analysis 테스트."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hmda_reliability.reliability import (
    ImpactAnalysisError,
    ImpactAnalysisRequest,
    Incident,
    IncidentSeverity,
    IncidentStatus,
    analyze_dbt_impact,
)

pytestmark = pytest.mark.component


def test_impact_analysis_finds_downstream_from_source(tmp_path: Path) -> None:
    """source asset에서 staging/mart downstream을 계산한다."""
    manifest_path = _write_manifest(tmp_path)
    run_results_path = _write_run_results(tmp_path)
    incident = _incident("source.hmda_reliability.raw.hmda_loans")

    result = analyze_dbt_impact(
        ImpactAnalysisRequest(
            incident=incident,
            dbt_manifest_path=manifest_path,
            dbt_run_results_path=run_results_path,
        )
    )

    assert result.lineage_evidence.downstream_assets == [
        "stg_hmda_loans",
        "mart_hmda_loan_outcomes",
    ]
    assert result.incident.affected_assets == [
        "stg_hmda_loans",
        "mart_hmda_loan_outcomes",
    ]


def test_impact_analysis_resolves_model_name_and_node_id(tmp_path: Path) -> None:
    """model name과 node id 입력을 모두 dbt asset으로 해석한다."""
    manifest_path = _write_manifest(tmp_path)
    run_results_path = _write_run_results(tmp_path)

    by_name = analyze_dbt_impact(
        ImpactAnalysisRequest(
            incident=_incident("stg_hmda_loans"),
            dbt_manifest_path=manifest_path,
            dbt_run_results_path=run_results_path,
        )
    )
    by_node_id = analyze_dbt_impact(
        ImpactAnalysisRequest(
            incident=_incident("model.hmda_reliability.stg_hmda_loans"),
            dbt_manifest_path=manifest_path,
            dbt_run_results_path=run_results_path,
        )
    )

    assert by_name.incident.affected_assets == ["mart_hmda_loan_outcomes"]
    assert by_node_id.incident.affected_assets == ["mart_hmda_loan_outcomes"]


def test_impact_analysis_builds_lineage_evidence_paths(tmp_path: Path) -> None:
    """LineageEvidence path와 incident 연결을 검증한다."""
    manifest_path = _write_manifest(tmp_path)
    run_results_path = _write_run_results(tmp_path)
    incident = _incident("source.hmda_reliability.raw.hmda_loans")

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


def test_impact_analysis_wraps_invalid_manifest(tmp_path: Path) -> None:
    """잘못된 dbt manifest를 reliability 도메인 오류로 변환한다."""

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("not-json", encoding="utf-8")

    with pytest.raises(ImpactAnalysisError, match="manifest"):
        analyze_dbt_impact(
            ImpactAnalysisRequest(
                incident=_incident("raw.hmda_loans"),
                dbt_manifest_path=manifest_path,
                dbt_run_results_path=tmp_path / "run_results.json",
            )
        )


@pytest.mark.parametrize("container", ["nodes", "sources"])
@pytest.mark.parametrize(
    "invalid_value",
    [None, [], "bad", 7, False],
    ids=["null", "array", "string", "number", "boolean"],
)
def test_impact_analysis_rejects_malformed_graph_containers(
    tmp_path: Path,
    container: str,
    invalid_value: object,
) -> None:
    manifest_path = _write_manifest(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest[container] = invalid_value
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ImpactAnalysisError, match=container):
        analyze_dbt_impact(
            ImpactAnalysisRequest(
                incident=_incident("source.hmda_reliability.raw.hmda_loans"),
                dbt_manifest_path=manifest_path,
                dbt_run_results_path=_write_run_results(tmp_path),
            )
        )


@pytest.mark.parametrize(
    "manifest",
    [{}, {"nodes": {}}, {"sources": {}}, {"nodes": {}, "sources": {}}],
    ids=["omitted", "nodes-only", "sources-only", "both-empty"],
)
def test_impact_analysis_accepts_valid_empty_graphs(
    tmp_path: Path,
    manifest: dict[str, object],
) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    result = analyze_dbt_impact(
        ImpactAnalysisRequest(
            incident=_incident("raw.hmda_loans"),
            dbt_manifest_path=manifest_path,
            dbt_run_results_path=_write_run_results(tmp_path),
        )
    )

    assert result.incident.affected_assets == []
    assert result.lineage_evidence.downstream_assets == []
    assert result.lineage_evidence.upstream_asset == "raw.hmda_loans"
    assert result.lineage_evidence.dbt_manifest_path == str(manifest_path)


def test_impact_analysis_rejects_missing_manifest(tmp_path: Path) -> None:
    with pytest.raises(ImpactAnalysisError, match="manifest"):
        analyze_dbt_impact(
            ImpactAnalysisRequest(
                incident=_incident("raw.hmda_loans"),
                dbt_manifest_path=tmp_path / "missing.json",
                dbt_run_results_path=_write_run_results(tmp_path),
            )
        )


def test_impact_analysis_rejects_missing_run_results(tmp_path: Path) -> None:
    """존재하지 않는 run results를 lineage evidence로 기록하지 않는다."""

    with pytest.raises(ImpactAnalysisError, match="run results"):
        analyze_dbt_impact(
            ImpactAnalysisRequest(
                incident=_incident("raw.hmda_loans"),
                dbt_manifest_path=_write_manifest(tmp_path),
                dbt_run_results_path=tmp_path / "missing.json",
            )
        )


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
            "source.hmda_reliability.raw.hmda_loans": {
                "name": "hmda_loans",
                "schema": "raw",
                "resource_type": "source",
                "depends_on": {"nodes": []},
            }
        },
        "nodes": {
            "model.hmda_reliability.stg_hmda_loans": {
                "name": "stg_hmda_loans",
                "alias": "stg_hmda_loans",
                "schema": "staging",
                "resource_type": "model",
                "depends_on": {"nodes": ["source.hmda_reliability.raw.hmda_loans"]},
            },
            "model.hmda_reliability.mart_hmda_loan_outcomes": {
                "name": "mart_hmda_loan_outcomes",
                "alias": "mart_hmda_loan_outcomes",
                "schema": "marts",
                "resource_type": "model",
                "depends_on": {"nodes": ["model.hmda_reliability.stg_hmda_loans"]},
            },
        },
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


def _write_run_results(tmp_path: Path) -> Path:
    run_results_path = tmp_path / "run_results.json"
    run_results_path.write_text("{}", encoding="utf-8")
    return run_results_path
