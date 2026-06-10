"""Remediation draft workflow 테스트."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from project_pivot.reliability import (
    Evidence,
    EvidenceSource,
    Incident,
    IncidentSeverity,
    IncidentStatus,
    LineageEvidence,
    RemediationDraftRequest,
    create_remediation_draft,
)


def test_volume_drop_draft_contains_backfill_and_validation_actions() -> None:
    """volume_drop 조치 초안의 필수 action을 검증한다."""
    incident = _incident("volume_drop", recommended_actions=["check_ingestion_run"])
    evidence = _evidence(
        incident_type="volume_drop",
        payload={"drop_ratio": 0.6},
    )

    draft = create_remediation_draft(
        RemediationDraftRequest(
            incident=incident,
            evidence=evidence,
            lineage_evidence=_lineage(),
        )
    )

    assert "validate_source_partition" in draft.recommended_actions
    assert "prepare_partition_backfill" in draft.recommended_actions
    assert draft.backfill_actions == ["prepare_partition_backfill"]
    assert "rerun_profile_snapshot" in draft.validation_actions
    assert draft.requires_approval


def test_null_spike_draft_contains_dbt_test_suggestion() -> None:
    """null_spike 조치 초안의 dbt test 제안을 검증한다."""
    incident = _incident("null_spike")
    evidence = _evidence(
        incident_type="null_spike",
        payload={"column": "total_amount", "current_null_rate": 0.2},
    )

    draft = create_remediation_draft(
        RemediationDraftRequest(incident=incident, evidence=evidence)
    )

    assert "add_dbt_not_null_test" in draft.recommended_actions
    assert draft.dbt_test_suggestions == ["add_not_null_test_for_spiking_column"]
    assert "validate_null_rate" in draft.validation_actions


def test_draft_preserves_affected_assets_and_serializes_to_json() -> None:
    """affected assets 보존과 JSON 직렬화를 검증한다."""
    incident = _incident("schema_drift")
    evidence = _evidence(
        incident_type="schema_drift",
        payload={"current_schema_hash": "sha256:changed"},
    )

    draft = create_remediation_draft(
        RemediationDraftRequest(
            incident=incident,
            evidence=evidence,
            lineage_evidence=_lineage(),
        )
    )
    payload = json.loads(draft.model_dump_json())

    assert draft.affected_assets == ["stg_yellow_tripdata", "mart_daily_taxi_trips"]
    assert payload["incident_type"] == "schema_drift"
    assert payload["evidence_refs"] == ["ev_2024_01_01"]
    assert payload["affected_assets"] == [
        "stg_yellow_tripdata",
        "mart_daily_taxi_trips",
    ]


def _incident(
    incident_type: str,
    *,
    recommended_actions: list[str] | None = None,
) -> Incident:
    return Incident(
        incident_id=f"inc_{incident_type}_2024_01_01",
        asset_name="raw.taxi_trips",
        partition="2024-01-01",
        incident_type=incident_type,
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.DETECTED,
        owner="data-platform",
        evidence_refs=["ev_2024_01_01"],
        recommended_actions=recommended_actions or [],
    )


def _evidence(incident_type: str, payload: dict[str, object]) -> Evidence:
    return Evidence(
        evidence_id="ev_2024_01_01",
        source=EvidenceSource.PROFILE,
        asset_name="raw.taxi_trips",
        partition="2024-01-01",
        observed_at=datetime(2026, 6, 10, 0, 0, tzinfo=UTC),
        summary=f"{incident_type} evidence",
        payload=payload,
    )


def _lineage() -> LineageEvidence:
    return LineageEvidence(
        lineage_id="lineage_raw_taxi_trips_2024_01_01",
        upstream_asset="raw.taxi_trips",
        downstream_assets=["stg_yellow_tripdata", "mart_daily_taxi_trips"],
        dbt_manifest_path="dbt/target/manifest.json",
        dbt_run_results_path="dbt/target/run_results.json",
    )
