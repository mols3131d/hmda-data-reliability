"""Synthetic reliability contract fixtures."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import NamedTuple

import pytest

from project_pivot.reliability.contracts import (
    Approval,
    ApprovalStatus,
    Evidence,
    EvidenceSource,
    HumanReviewStatus,
    Incident,
    IncidentSeverity,
    IncidentStatus,
    LineageEvidence,
    ProfileSnapshot,
)


class SyntheticIncidentFixture(NamedTuple):
    incident: Incident
    evidence: Evidence
    profile_snapshot: ProfileSnapshot
    lineage_evidence: LineageEvidence
    approval: Approval


@pytest.fixture
def synthetic_incident_fixture() -> SyntheticIncidentFixture:
    observed_at = datetime(2026, 6, 6, 0, 0, tzinfo=UTC)
    asset_name = "mart.hmda_loan_outcomes"
    partition = "2026-06-05"
    evidence_id = "ev_profile_hmda_loan_outcomes_2026_06_05"

    evidence = Evidence(
        evidence_id=evidence_id,
        source=EvidenceSource.PROFILE,
        asset_name=asset_name,
        partition=partition,
        observed_at=observed_at,
        summary="row_count가 baseline 대비 급감했다.",
        payload={"baseline_row_count": 100_000, "current_row_count": 12_000},
    )
    profile_snapshot = ProfileSnapshot(
        snapshot_id="profile_hmda_loan_outcomes_2026_06_05",
        asset_name=asset_name,
        partition=partition,
        observed_at=observed_at,
        row_count=12_000,
        null_rates={"loan_amount": 0.02},
        schema_hash="sha256:synthetic-schema",
        freshness_at=observed_at,
        metric_values={"baseline_row_count": 100_000.0, "row_count_drop_ratio": 0.88},
    )
    lineage_evidence = LineageEvidence(
        lineage_id="lineage_hmda_loan_outcomes_2026_06_05",
        upstream_asset=asset_name,
        downstream_assets=["mart.revenue_dashboard", "mart.driver_payouts"],
        dbt_manifest_path="target/manifest.json",
        dbt_run_results_path="target/run_results.json",
    )
    incident = Incident(
        incident_id="inc_hmda_loan_outcomes_2026_06_05",
        asset_name=asset_name,
        partition=partition,
        incident_type="volume_drop",
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.DETECTED,
        owner="data-platform",
        evidence_refs=[evidence_id],
        affected_assets=lineage_evidence.downstream_assets,
        recommended_actions=["validate_source_partition", "prepare_partition_backfill"],
        human_review_status=HumanReviewStatus.PENDING,
    )
    approval = Approval(
        approval_id="approval_hmda_loan_outcomes_2026_06_05",
        incident_id=incident.incident_id,
        status=ApprovalStatus.PENDING,
        requested_by="data-platform",
        requested_at=observed_at,
        requested_actions=["partition_overwrite", "validation"],
    )
    return SyntheticIncidentFixture(
        incident=incident,
        evidence=evidence,
        profile_snapshot=profile_snapshot,
        lineage_evidence=lineage_evidence,
        approval=approval,
    )
