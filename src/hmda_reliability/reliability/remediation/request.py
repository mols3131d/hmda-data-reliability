"""Remediation draft request model."""

from pydantic import BaseModel, ConfigDict, Field

from hmda_reliability.reliability.contracts import Evidence, Incident, LineageEvidence


class RemediationDraftRequest(BaseModel):
    """Remediation workflow 입력."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    incident: Incident
    evidence: Evidence
    lineage_evidence: LineageEvidence | None = None
    operator: str = Field(default="data-platform")
