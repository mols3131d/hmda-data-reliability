"""Incident contract tests."""

import pytest
from pydantic import ValidationError

from project_pivot.reliability.contracts import (
    Incident,
    IncidentSeverity,
    IncidentStatus,
)


def test_incident_requires_evidence_ref() -> None:
    """Incident가 최소 1개 evidence 참조를 요구하는지 검증한다."""
    with pytest.raises(ValidationError):
        Incident(
            incident_id="inc_without_evidence",
            asset_name="mart.hmda_loan_outcomes",
            partition="2026-06-05",
            incident_type="volume_drop",
            severity=IncidentSeverity.HIGH,
            status=IncidentStatus.DETECTED,
            owner="data-platform",
            evidence_refs=[],
        )
