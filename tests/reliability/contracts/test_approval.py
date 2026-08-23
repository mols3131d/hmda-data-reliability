"""Approval contract tests."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from hmda_reliability.reliability.contracts import (
    Approval,
    ApprovalStatus,
    can_execute_risky_action,
)

pytestmark = pytest.mark.unit


def test_approved_approval_requires_approver_and_time() -> None:
    """승인된 Approval이 승인자와 승인 시각을 요구하는지 검증한다."""
    requested_at = datetime(2026, 6, 6, 0, 0, tzinfo=UTC)

    with pytest.raises(ValidationError):
        Approval(
            approval_id="approval_missing_review",
            incident_id="inc_hmda_loan_outcomes_2026_06_05",
            status=ApprovalStatus.APPROVED,
            requested_by="data-platform",
            requested_at=requested_at,
        )


def test_only_approved_status_allows_execution_gate_to_continue() -> None:
    """승인 상태만 action-specific execution gate 진행을 허용하는지 검증한다."""
    requested_at = datetime(2026, 6, 6, 0, 0, tzinfo=UTC)
    approved = Approval(
        approval_id="approval_approved",
        incident_id="inc_hmda_loan_outcomes_2026_06_05",
        status=ApprovalStatus.APPROVED,
        requested_by="data-platform",
        requested_at=requested_at,
        approved_by="data-owner",
        approved_at=requested_at,
    )
    pending = Approval(
        approval_id="approval_pending",
        incident_id="inc_hmda_loan_outcomes_2026_06_05",
        status=ApprovalStatus.PENDING,
        requested_by="data-platform",
        requested_at=requested_at,
    )

    assert can_execute_risky_action(approved)
    assert not can_execute_risky_action(pending)
