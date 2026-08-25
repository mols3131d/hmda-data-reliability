"""Evidence contract tests."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from hmda_reliability.reliability.contracts import Evidence, EvidenceSource

pytestmark = pytest.mark.unit


def test_evidence_contract_accepts_structured_payload() -> None:
    """Evidence가 구조화된 payload를 보존하는지 검증한다."""
    observed_at = datetime(2026, 6, 6, 0, 0, tzinfo=UTC)

    evidence = Evidence(
        evidence_id="ev_profile_hmda_loan_outcomes_2026_06_05",
        source=EvidenceSource.PROFILE,
        asset_name="mart.hmda_loan_outcomes",
        partition="2026-06-05",
        observed_at=observed_at,
        summary="row_count가 baseline 대비 급감했다.",
        payload={"baseline_row_count": 100_000, "current_row_count": 12_000},
    )

    assert evidence.payload["current_row_count"] == 12_000


def test_evidence_contract_accepts_vendor_neutral_orchestration_source() -> None:
    """Orchestration execution evidence does not expose its vendor."""

    evidence = Evidence(
        evidence_id="ev_orchestration_hmda_2026_06_05",
        source=EvidenceSource.ORCHESTRATION,
        asset_name="hmda/raw/hmda_loans",
        partition="2026",
        observed_at=datetime(2026, 6, 6, 0, 0, tzinfo=UTC),
        summary="raw load task completed",
    )

    assert evidence.source is EvidenceSource.ORCHESTRATION
    assert evidence.model_dump()["source"] == "orchestration"


@pytest.mark.parametrize("vendor_source", ["dagster", "airflow"])
def test_evidence_contract_rejects_vendor_specific_sources(
    vendor_source: str,
) -> None:
    """Reliability contracts reject orchestration vendor names."""

    with pytest.raises(ValidationError):
        Evidence(
            evidence_id="ev_vendor_specific",
            source=vendor_source,
            asset_name="hmda/raw/hmda_loans",
            partition="2026",
            observed_at=datetime(2026, 6, 6, 0, 0, tzinfo=UTC),
            summary="vendor-specific source must not be accepted",
        )
