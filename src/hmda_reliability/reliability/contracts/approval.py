"""승인(Approval) 계약 모델 정의 모듈."""

from datetime import datetime
from enum import StrEnum

from pydantic import Field, model_validator

from hmda_reliability.reliability.contracts.base import ReliabilityContract
from hmda_reliability.reliability.contracts.recovery_proposal import RecoveryProposal


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Approval(ReliabilityContract):
    """외부 검토 및 승인 기록 계약; 각 위험 작업 게이트에서 세부 범위를 검증한다."""

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
        """승인 상태가 실행 게이트 통과를 허용하는지 여부를 반환한다."""

        return self.status is ApprovalStatus.APPROVED


def can_execute_risky_action(approval: Approval) -> bool:
    """승인 상태만을 확인하며, 호출자는 작업별 세부 범위를 반드시 추가 검증해야 한다."""

    return approval.allows_execution()
