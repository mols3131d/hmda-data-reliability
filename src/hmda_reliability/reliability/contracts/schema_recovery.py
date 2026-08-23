"""Exact table-schema recovery proposal and approval contracts."""

from datetime import datetime

from pydantic import Field, model_validator

from project_pivot.reliability.contracts.approval import ApprovalStatus
from project_pivot.reliability.contracts.base import ReliabilityContract
from project_pivot.reliability.contracts.table_state import TableStateIdentity

_SCHEMA_RECOVERY_ACTIONS = ("replace_table", "rerun_profile_snapshot")


class SchemaRecoveryProposal(ReliabilityContract):
    """Exact table target, states, evidence, and actions presented for approval."""

    proposal_id: str = Field(min_length=1)
    incident_id: str = Field(min_length=1)
    observation_partition: str = Field(min_length=1)
    table_name: str = Field(min_length=1)
    candidate_state: TableStateIdentity
    approved_before_state: TableStateIdentity
    expected_after_state: TableStateIdentity
    validation_evidence_refs: tuple[str, ...] = Field(min_length=1)
    dbt_projection_id: str = Field(min_length=1)
    target_actions: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_exact_table_scope(self) -> "SchemaRecoveryProposal":
        states = (
            self.candidate_state,
            self.approved_before_state,
            self.expected_after_state,
        )
        if any(state.table_name != self.table_name for state in states):
            raise ValueError(
                "schema recovery state table_name은 target과 같아야 합니다."
            )
        if self.candidate_state != self.expected_after_state:
            raise ValueError(
                "validated candidate state는 expected after state와 같아야 합니다."
            )
        if self.target_actions != _SCHEMA_RECOVERY_ACTIONS:
            raise ValueError(
                "schema recovery actions는 replace_table과 "
                "rerun_profile_snapshot이어야 합니다."
            )
        return self


class SchemaRecoveryApproval(ReliabilityContract):
    """External review bound to one exact schema recovery proposal."""

    approval_id: str = Field(min_length=1)
    incident_id: str = Field(min_length=1)
    status: ApprovalStatus
    requested_by: str = Field(min_length=1)
    requested_at: datetime
    approved_by: str | None = None
    approved_at: datetime | None = None
    rejected_by: str | None = None
    rejected_at: datetime | None = None
    requested_actions: tuple[str, ...] = Field(min_length=1)
    recovery_proposal: SchemaRecoveryProposal
    reason: str | None = None

    @model_validator(mode="after")
    def _validate_exact_review(self) -> "SchemaRecoveryApproval":
        if self.status is ApprovalStatus.APPROVED and (
            self.approved_by is None or self.approved_at is None
        ):
            raise ValueError("approved approval requires approved_by and approved_at")
        if self.status is ApprovalStatus.REJECTED and (
            self.rejected_by is None or self.rejected_at is None
        ):
            raise ValueError("rejected approval requires rejected_by and rejected_at")
        if self.incident_id != self.recovery_proposal.incident_id:
            raise ValueError(
                "approval incident_id는 recovery proposal과 같아야 합니다."
            )
        if self.requested_actions != self.recovery_proposal.target_actions:
            raise ValueError("approval actions는 recovery proposal과 같아야 합니다.")
        return self

    def allows_execution(self) -> bool:
        """Return whether external review permits schema recovery execution."""

        return self.status is ApprovalStatus.APPROVED
