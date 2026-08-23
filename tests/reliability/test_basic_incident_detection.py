"""기본 incident detector 테스트."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from hmda_reliability.reliability import (
    DetectionRequest,
    DetectionThresholds,
    FreshnessMeasurementStatus,
    ProfileSnapshot,
    detect_basic_incidents,
)

pytestmark = pytest.mark.unit


def test_detector_returns_no_incident_for_normal_profile() -> None:
    """threshold를 넘지 않는 profile pair는 incident를 만들지 않는다."""
    baseline = _snapshot(row_count=100, null_rates={"loan_amount": 0.01})
    current = _snapshot(row_count=95, null_rates={"loan_amount": 0.02})

    results = detect_basic_incidents(
        DetectionRequest(
            baseline=baseline,
            current=current,
            thresholds=DetectionThresholds(
                volume_drop_ratio=0.5,
                null_spike_delta=0.1,
                freshness_max_age_minutes=60,
            ),
        )
    )

    assert results == []


def test_detector_creates_volume_drop_incident_and_evidence() -> None:
    """row count 급감 incident와 evidence payload를 검증한다."""
    baseline = _snapshot(row_count=100)
    current = _snapshot(row_count=40)

    result = detect_basic_incidents(
        DetectionRequest(baseline=baseline, current=current)
    )[0]

    assert result.incident.incident_type == "volume_drop"
    assert result.incident.severity == "high"
    assert result.evidence.source == "profile"
    assert result.evidence.payload["baseline_row_count"] == 100
    assert result.evidence.payload["current_row_count"] == 40
    assert result.evidence.payload["drop_ratio"] == 0.6


def test_detector_creates_null_spike_incident_and_evidence() -> None:
    """null spike incident와 대상 컬럼 payload를 검증한다."""
    baseline = _snapshot(row_count=100, null_rates={"loan_amount": 0.01})
    current = _snapshot(row_count=100, null_rates={"loan_amount": 0.20})

    result = detect_basic_incidents(
        DetectionRequest(baseline=baseline, current=current)
    )[0]

    assert result.incident.incident_type == "null_spike"
    assert result.incident.severity == "medium"
    assert result.evidence.payload["column"] == "loan_amount"
    assert result.evidence.payload["baseline_null_rate"] == 0.01
    assert result.evidence.payload["current_null_rate"] == 0.20


def test_detector_creates_schema_drift_incident_and_evidence() -> None:
    """schema hash 변경 incident를 검증한다."""
    baseline = _snapshot(row_count=100, schema_hash="sha256:baseline")
    current = _snapshot(row_count=100, schema_hash="sha256:current")

    result = detect_basic_incidents(
        DetectionRequest(baseline=baseline, current=current)
    )[0]

    assert result.incident.incident_type == "schema_drift"
    assert result.evidence.payload["baseline_schema_hash"] == "sha256:baseline"
    assert result.evidence.payload["current_schema_hash"] == "sha256:current"


def test_detector_creates_freshness_delay_at_exact_max_age() -> None:
    """Current observation age가 exact boundary면 incident를 생성한다."""
    observed_at = datetime(2026, 6, 10, 0, 0, tzinfo=UTC)
    baseline = _snapshot(
        row_count=100,
        observed_at=observed_at,
        freshness_at=datetime(2026, 6, 9, 23, 0, tzinfo=UTC),
    )
    current = _snapshot(
        row_count=100,
        observed_at=observed_at,
        freshness_at=datetime(2026, 6, 9, 23, 0, tzinfo=UTC),
    )

    result = detect_basic_incidents(
        DetectionRequest(
            baseline=baseline,
            current=current,
            thresholds=DetectionThresholds(freshness_max_age_minutes=60),
        )
    )[0]

    assert result.incident.incident_type == "freshness_delay"
    assert result.evidence.payload == {
        "rule": "freshness_delay",
        "snapshot_id": current.snapshot_id,
        "observed_at": "2026-06-10T00:00:00+00:00",
        "freshness_at": "2026-06-09T23:00:00+00:00",
        "freshness_status": "measured",
        "freshness_age_minutes": 60.0,
        "max_age_minutes": 60.0,
    }


def test_detector_ignores_freshness_below_max_age() -> None:
    current = _snapshot(
        row_count=100,
        freshness_at=datetime(2026, 6, 9, 23, 1, tzinfo=UTC),
    )

    results = detect_basic_incidents(
        DetectionRequest(
            baseline=current,
            current=current,
            thresholds=DetectionThresholds(freshness_max_age_minutes=60),
        )
    )

    assert results == []


def test_detector_skips_unavailable_freshness_but_keeps_other_rules() -> None:
    baseline = _snapshot(row_count=100)
    current = _snapshot(
        row_count=40,
        freshness_at=None,
        freshness_status=FreshnessMeasurementStatus.UNAVAILABLE,
    )

    results = detect_basic_incidents(
        DetectionRequest(baseline=baseline, current=current)
    )

    assert [result.incident.incident_type for result in results] == ["volume_drop"]


def test_detection_result_links_incident_to_evidence() -> None:
    """incident.evidence_refs가 result evidence id를 포함하는지 검증한다."""
    baseline = _snapshot(row_count=100)
    current = _snapshot(row_count=40)

    result = detect_basic_incidents(
        DetectionRequest(baseline=baseline, current=current)
    )[0]

    assert result.incident.evidence_refs == [result.evidence.evidence_id]
    assert result.evidence.asset_name == result.incident.asset_name
    assert result.evidence.partition == result.incident.partition


def test_detection_request_rejects_different_partitions() -> None:
    """서로 다른 partition의 profile 비교를 거부한다."""

    baseline = _snapshot(row_count=100)
    current = _snapshot(row_count=40).model_copy(update={"partition": "2025-01-01"})

    with pytest.raises(ValueError, match="partition"):
        DetectionRequest(baseline=baseline, current=current)


def _snapshot(
    *,
    row_count: int,
    null_rates: dict[str, float] | None = None,
    schema_hash: str = "sha256:stable",
    freshness_at: datetime | None = None,
    freshness_status: FreshnessMeasurementStatus = FreshnessMeasurementStatus.MEASURED,
    observed_at: datetime | None = None,
) -> ProfileSnapshot:
    observed_at = observed_at or datetime(2026, 6, 10, 0, 0, tzinfo=UTC)
    resolved_freshness = (
        None
        if freshness_status is FreshnessMeasurementStatus.UNAVAILABLE
        else freshness_at or datetime(2026, 6, 9, 23, 30, tzinfo=UTC)
    )
    return ProfileSnapshot(
        snapshot_id="profile_raw_hmda_loans_2025",
        asset_name="raw.hmda_loans",
        partition="2024-01-01",
        observed_at=observed_at,
        row_count=row_count,
        null_rates=null_rates or {"loan_amount": 0.01},
        schema_hash=schema_hash,
        freshness_at=resolved_freshness,
        freshness_status=freshness_status,
        metric_values={"row_count": float(row_count)},
    )
