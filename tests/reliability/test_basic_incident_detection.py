"""기본 탐지 계약과 실제 양의 악화·독립 규칙의 threshold 경계를 검증한다."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

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


@pytest.mark.parametrize(
    ("field", "value"),
    [("partition", "2025-01-01"), ("asset_name", "raw.other_loans")],
)
def test_detection_request_rejects_different_populations(
    field: str, value: str
) -> None:
    """서로 다른 asset 또는 partition의 profile 비교를 거부한다."""

    baseline = _snapshot(row_count=100)
    current = _snapshot(row_count=40).model_copy(update={field: value})

    with pytest.raises(ValueError, match=field):
        DetectionRequest(baseline=baseline, current=current)


@pytest.mark.parametrize(
    ("row_count", "null_rate", "expected_types"),
    [
        (100, 0.125, []),
        (99, 0.125, ["volume_drop"]),
        (100, 0.25, ["null_spike"]),
        (99, 0.25, ["volume_drop", "null_spike"]),
        (101, 0.0, []),
        (100, 0.0, []),
        (101, 0.125, []),
    ],
    ids=[
        "unchanged",
        "volume-only",
        "null-only",
        "both",
        "both-improve",
        "null-improves",
        "volume-improves",
    ],
)
def test_zero_thresholds_detect_only_positive_degradation(
    row_count: int,
    null_rate: float,
    expected_types: list[str],
) -> None:
    baseline = _snapshot(row_count=100, null_rates={"loan_amount": 0.125})
    current = _snapshot(row_count=row_count, null_rates={"loan_amount": null_rate})

    results = detect_basic_incidents(
        DetectionRequest(
            baseline=baseline,
            current=current,
            thresholds=DetectionThresholds(volume_drop_ratio=0, null_spike_delta=0),
        )
    )

    assert [result.incident.incident_type for result in results] == expected_types
    for result in results:
        assert result.evidence.payload["threshold"] == 0
        assert result.incident.evidence_refs == [result.evidence.evidence_id]
        if result.incident.incident_type == "volume_drop":
            assert result.evidence.payload["baseline_row_count"] == 100
            assert result.evidence.payload["current_row_count"] == 99
            assert result.evidence.payload["drop_ratio"] == 0.01
        else:
            assert result.evidence.payload["column"] == "loan_amount"
            assert result.evidence.payload["baseline_null_rate"] == 0.125
            assert result.evidence.payload["current_null_rate"] == 0.25
            assert result.evidence.payload["delta"] == 0.125


@pytest.mark.parametrize(
    ("row_count", "null_rate", "expected_type", "metric", "expected_value"),
    [
        (50, 0.125, "volume_drop", "drop_ratio", 0.5),
        (100, 0.25, "null_spike", "delta", 0.125),
    ],
)
def test_positive_threshold_equality_remains_inclusive(
    row_count: int,
    null_rate: float,
    expected_type: str,
    metric: str,
    expected_value: float,
) -> None:
    results = detect_basic_incidents(
        DetectionRequest(
            baseline=_snapshot(row_count=100, null_rates={"loan_amount": 0.125}),
            current=_snapshot(
                row_count=row_count, null_rates={"loan_amount": null_rate}
            ),
            thresholds=DetectionThresholds(
                volume_drop_ratio=0.5, null_spike_delta=0.125
            ),
        )
    )

    assert [result.incident.incident_type for result in results] == [expected_type]
    assert results[0].evidence.payload[metric] == expected_value
    assert results[0].evidence.payload["threshold"] == expected_value


@pytest.mark.parametrize(
    ("row_count", "null_rate", "expected_types"),
    [(0, 0.125, []), (1, 0.125, []), (1, 0.25, ["null_spike"])],
)
def test_zero_row_baseline_skips_only_volume_comparison(
    row_count: int,
    null_rate: float,
    expected_types: list[str],
) -> None:
    results = detect_basic_incidents(
        DetectionRequest(
            baseline=_snapshot(row_count=0, null_rates={"loan_amount": 0.125}),
            current=_snapshot(
                row_count=row_count, null_rates={"loan_amount": null_rate}
            ),
            thresholds=DetectionThresholds(volume_drop_ratio=0, null_spike_delta=0),
        )
    )

    assert [result.incident.incident_type for result in results] == expected_types


@pytest.mark.parametrize(
    ("age_minutes", "max_age", "schema_hash", "freshness_status", "expected_types"),
    [
        (
            0,
            0,
            "sha256:stable",
            FreshnessMeasurementStatus.MEASURED,
            ["freshness_delay"],
        ),
        (
            60,
            60,
            "sha256:stable",
            FreshnessMeasurementStatus.MEASURED,
            ["freshness_delay"],
        ),
        (
            30,
            60,
            "sha256:changed",
            FreshnessMeasurementStatus.MEASURED,
            ["schema_drift"],
        ),
        (0, 0, "sha256:stable", FreshnessMeasurementStatus.UNAVAILABLE, []),
        (
            60,
            60,
            "sha256:changed",
            FreshnessMeasurementStatus.MEASURED,
            ["schema_drift", "freshness_delay"],
        ),
    ],
    ids=[
        "zero-age-equality",
        "unchanged-stale-time",
        "schema",
        "unavailable",
        "schema-and-freshness",
    ],
)
def test_zero_thresholds_preserve_independent_rules(
    age_minutes: int,
    max_age: int,
    schema_hash: str,
    freshness_status: FreshnessMeasurementStatus,
    expected_types: list[str],
) -> None:
    observed_at = datetime(2026, 6, 10, tzinfo=UTC)
    freshness_at = observed_at - timedelta(minutes=age_minutes)
    baseline = _snapshot(
        row_count=100, observed_at=observed_at, freshness_at=freshness_at
    )
    current = _snapshot(
        row_count=100,
        schema_hash=schema_hash,
        observed_at=observed_at,
        freshness_at=freshness_at,
        freshness_status=freshness_status,
    )

    results = detect_basic_incidents(
        DetectionRequest(
            baseline=baseline,
            current=current,
            thresholds=DetectionThresholds(
                volume_drop_ratio=0,
                null_spike_delta=0,
                freshness_max_age_minutes=max_age,
            ),
        )
    )

    assert [result.incident.incident_type for result in results] == expected_types
    for result in results:
        if result.incident.incident_type == "freshness_delay":
            assert result.evidence.payload["freshness_age_minutes"] == age_minutes
            assert result.evidence.payload["max_age_minutes"] == max_age


def test_zero_null_threshold_applies_to_each_column_independently() -> None:
    results = detect_basic_incidents(
        DetectionRequest(
            baseline=_snapshot(
                row_count=100, null_rates={"income": 0.125, "loan_amount": 0.125}
            ),
            current=_snapshot(
                row_count=100, null_rates={"income": 0.125, "loan_amount": 0.25}
            ),
            thresholds=DetectionThresholds(volume_drop_ratio=0, null_spike_delta=0),
        )
    )

    assert [result.incident.incident_type for result in results] == ["null_spike"]
    assert results[0].evidence.payload["column"] == "loan_amount"
    assert results[0].evidence.payload["delta"] == 0.125


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
