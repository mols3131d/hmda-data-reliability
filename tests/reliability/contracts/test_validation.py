"""Validation tests."""

import pytest

from project_pivot.reliability.contracts import Incident, validate_contract
from project_pivot.reliability.errors import ContractValidationError

pytestmark = pytest.mark.unit


def test_validate_contract_wraps_pydantic_validation_error() -> None:
    """Contract validation 실패가 domain exception으로 감싸지는지 검증한다."""
    with pytest.raises(ContractValidationError) as exc_info:
        validate_contract(
            Incident,
            {
                "incident_id": "inc_without_evidence",
                "asset_name": "mart.hmda_loan_outcomes",
                "partition": "2026-06-05",
                "incident_type": "volume_drop",
                "severity": "high",
                "status": "detected",
                "owner": "data-platform",
                "evidence_refs": [],
            },
        )

    assert exc_info.value.contract_name == "Incident"
    assert "evidence_refs" in exc_info.value.details[0]
