"""Deterministic null-spike review fixtures."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import NamedTuple

import pytest

from hmda_reliability.reliability import (
    DetectionRequest,
    DetectionResult,
    FreshnessMeasurementStatus,
    ProfileSnapshot,
    RemediationDraft,
    RemediationDraftRequest,
    create_remediation_draft,
    detect_basic_incidents,
)


class NullSpikeReviewMaterial(NamedTuple):
    detection: DetectionResult
    draft: RemediationDraft


@pytest.fixture
def null_spike_review_material() -> NullSpikeReviewMaterial:
    observed_at = datetime(2026, 8, 27, 0, 0, tzinfo=UTC)
    baseline = ProfileSnapshot(
        snapshot_id="profile-baseline-2025",
        asset_name="raw.hmda_loans",
        partition="2025",
        observed_at=observed_at,
        row_count=100,
        null_rates={"income": 0.01},
        schema_hash="sha256:stable",
        freshness_at=None,
        freshness_status=FreshnessMeasurementStatus.UNAVAILABLE,
    )
    current = ProfileSnapshot(
        snapshot_id="profile-current-2025",
        asset_name="raw.hmda_loans",
        partition="2025",
        observed_at=observed_at,
        row_count=100,
        null_rates={"income": 0.21},
        schema_hash="sha256:stable",
        freshness_at=None,
        freshness_status=FreshnessMeasurementStatus.UNAVAILABLE,
    )
    detection = detect_basic_incidents(
        DetectionRequest(baseline=baseline, current=current)
    )[0]
    draft = create_remediation_draft(
        RemediationDraftRequest(
            incident=detection.incident,
            evidence=detection.evidence,
        )
    )
    return NullSpikeReviewMaterial(detection=detection, draft=draft)
