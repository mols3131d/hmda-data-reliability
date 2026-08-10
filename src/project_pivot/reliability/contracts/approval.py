"""Approval contract models."""

from datetime import datetime
from enum import StrEnum

from pydantic import Field, model_validator

from project_pivot.reliability.contracts.base import ReliabilityContract
from project_pivot.reliability.contracts.recovery_proposal import RecoveryProposal


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Approval(ReliabilityContract):
    approval_id: str
    incident_id: str
    status: ApprovalStatus
    requested_by: str
    requested_at: datetime
    approved_by: str | None = None
    approved_at: datetime | None = None
    rejected_by: str | None = None
    rejected_at: datetime | None = None
    requested_actions: tuple[str, ...] = Field(default_factory=tuple)
    recovery_proposal: RecoveryProposal | None = None
    reason: str | None = None

    @model_validator(mode="after")
    def _validate_review_fields(self) -> "Approval":
        if self.status is ApprovalStatus.APPROVED and (
            self.approved_by is None or self.approved_at is None
        ):
            raise ValueError("approved approval requires approved_by and approved_at")
        if self.status is ApprovalStatus.REJECTED and (
            self.rejected_by is None or self.rejected_at is None
        ):
            raise ValueError("rejected approval requires rejected_by and rejected_at")
        return self

    def allows_execution(self) -> bool:
        return self.status is ApprovalStatus.APPROVED


def can_execute_risky_action(approval: Approval) -> bool:
    return approval.allows_execution()
