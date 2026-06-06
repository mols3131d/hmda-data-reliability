"""Evidence contract tests."""

from datetime import UTC, datetime

from project_pivot.reliability.contracts import Evidence, EvidenceSource


def test_evidence_contract_accepts_structured_payload() -> None:
    """Evidence가 구조화된 payload를 보존하는지 검증한다."""
    observed_at = datetime(2026, 6, 6, 0, 0, tzinfo=UTC)

    evidence = Evidence(
        evidence_id="ev_profile_daily_taxi_revenue_2026_06_05",
        source=EvidenceSource.PROFILE,
        asset_name="mart.daily_taxi_revenue",
        partition="2026-06-05",
        observed_at=observed_at,
        summary="row_count가 baseline 대비 급감했다.",
        payload={"baseline_row_count": 100_000, "current_row_count": 12_000},
    )

    assert evidence.payload["current_row_count"] == 12_000
