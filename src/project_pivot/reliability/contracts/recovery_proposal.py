"""Exact recovery proposal contract."""

from pydantic import Field, model_validator

from project_pivot.hmda_data import PartitionContentIdentity
from project_pivot.reliability.contracts.base import ReliabilityContract


class RecoveryProposal(ReliabilityContract):
    """Immutable target, candidate, evidence, and action set presented for approval."""

    proposal_id: str
    incident_id: str
    table_name: str
    source_year: int = Field(ge=2000, le=2100)
    source_file: str | None = None
    candidate_identity: PartitionContentIdentity
    approved_before_identity: PartitionContentIdentity
    expected_after_identity: PartitionContentIdentity
    validation_evidence_refs: tuple[str, ...] = Field(min_length=1)
    dbt_projection_id: str
    target_actions: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _validate_partition_scope(self) -> "RecoveryProposal":
        identities = (
            self.candidate_identity,
            self.approved_before_identity,
            self.expected_after_identity,
        )
        if any(
            identity.table_name != self.table_name
            or identity.source_year != self.source_year
            or identity.source_file != self.source_file
            for identity in identities
        ):
            raise ValueError("recovery proposal identity scope must match target")
        if self.candidate_identity != self.expected_after_identity:
            raise ValueError("validated candidate must equal expected recovery state")
        return self
