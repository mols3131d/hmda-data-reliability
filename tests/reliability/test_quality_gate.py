"""Profile 기반 quality gate policy tests."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from hmda_reliability.reliability import (
    FreshnessMeasurementStatus,
    ProfileSnapshot,
    QualityGateError,
    evaluate_profile_quality_gate,
)

pytestmark = pytest.mark.unit

_ACCEPTED_2025_INCOME_NULL_RATE = 0.16168766279822375


def _profile(
    *,
    row_count: int = 1000,
    null_rates: dict[str, float] | None = None,
    freshness_at: datetime | None = None,
) -> ProfileSnapshot:
    return ProfileSnapshot(
        snapshot_id="profile_raw_hmda_loans_2025",
        asset_name="source.hmda_reliability.raw.hmda_loans",
        partition="2025",
        observed_at=datetime(2026, 9, 4, tzinfo=UTC),
        row_count=row_count,
        null_rates=null_rates or {"income": 0.002, "loan_amount": 0.0},
        schema_hash="sha256:test-schema",
        freshness_at=freshness_at,
        freshness_status=(
            FreshnessMeasurementStatus.MEASURED
            if freshness_at is not None
            else FreshnessMeasurementStatus.UNAVAILABLE
        ),
    )


def test_quality_gate_passes_when_no_anomaly_detected(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO)

    evaluate_profile_quality_gate(_profile())

    assert any(
        "품질 게이트 통과" in record.message
        and getattr(record, "status", None) == "clean"
        for record in caplog.records
    )


def test_quality_gate_accepts_exact_2025_baseline() -> None:
    evaluate_profile_quality_gate(
        _profile(
            null_rates={
                "income": _ACCEPTED_2025_INCOME_NULL_RATE,
                "loan_amount": 0.0,
            }
        )
    )


def test_quality_gate_blocks_exact_five_percentage_point_delta() -> None:
    with pytest.raises(QualityGateError) as exc_info:
        evaluate_profile_quality_gate(
            _profile(
                null_rates={
                    "income": _ACCEPTED_2025_INCOME_NULL_RATE,
                    "loan_amount": 0.05,
                }
            )
        )

    assert exc_info.value.detected_incident_types == ["null_spike(loan_amount)"]


def test_quality_gate_raises_on_null_spike(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING)

    with pytest.raises(QualityGateError) as exc_info:
        evaluate_profile_quality_gate(
            _profile(null_rates={"income": 0.4, "loan_amount": 0.0})
        )

    assert "null_spike(income)" in str(exc_info.value)
    assert exc_info.value.detected_incident_types == ["null_spike(income)"]
    assert any(
        "품질 게이트 실패" in record.message
        and getattr(record, "detected_incident_types", None) == ["null_spike(income)"]
        for record in caplog.records
    )


def test_quality_gate_ignores_volume_drop_by_design() -> None:
    evaluate_profile_quality_gate(_profile(row_count=5))


def test_quality_gate_ignores_freshness_delay_by_design() -> None:
    evaluate_profile_quality_gate(
        _profile(freshness_at=datetime(2026, 9, 3, tzinfo=UTC))
    )


@pytest.mark.parametrize(
    "incident_type",
    ["volume_drop", "schema_drift", "freshness_delay"],
)
def test_quality_gate_ignores_non_blocking_detector_results(
    monkeypatch: pytest.MonkeyPatch,
    incident_type: str,
) -> None:
    import hmda_reliability.reliability.quality_gate as quality_gate_module

    result = SimpleNamespace(
        incident=SimpleNamespace(incident_type=incident_type),
        evidence=SimpleNamespace(payload={}),
    )
    monkeypatch.setattr(
        quality_gate_module,
        "detect_basic_incidents",
        lambda _request: [result],
    )

    evaluate_profile_quality_gate(_profile())


def test_quality_gate_raises_on_empty_partition(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING)

    with pytest.raises(QualityGateError, match="empty_partition") as exc_info:
        evaluate_profile_quality_gate(_profile(row_count=0))

    assert exc_info.value.detected_incident_types == ["empty_partition"]
    assert any(
        "품질 게이트 실패: 빈 파티션 감지됨" in record.message
        for record in caplog.records
    )


def test_quality_gate_rejects_unsupported_profile_columns(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING)

    with pytest.raises(ValueError, match="baseline을 지원하지 않습니다.*loan_purpose"):
        evaluate_profile_quality_gate(
            _profile(
                null_rates={
                    "income": 0.002,
                    "loan_amount": 0.0,
                    "loan_purpose": 0.0,
                }
            )
        )

    assert any(
        getattr(record, "source_year", None) == "2025"
        and getattr(record, "asset_name", None)
        == "source.hmda_reliability.raw.hmda_loans"
        and getattr(record, "detected_incident_types", None)
        == ["unsupported_profile_columns"]
        for record in caplog.records
    )


def test_quality_gate_rejects_missing_required_profile_columns(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING)

    with pytest.raises(ValueError, match="필수 프로파일 컬럼.*income"):
        evaluate_profile_quality_gate(_profile(null_rates={"loan_amount": 0.0}))

    assert any(
        getattr(record, "source_year", None) == "2025"
        and getattr(record, "asset_name", None)
        == "source.hmda_reliability.raw.hmda_loans"
        and getattr(record, "detected_incident_types", None)
        == ["missing_profile_columns"]
        for record in caplog.records
    )
