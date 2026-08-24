"""Incident contract models."""

from enum import StrEnum

from pydantic import Field

from hmda_reliability.reliability.contracts.base import ReliabilityContract


class IncidentSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(StrEnum):
    DETECTED = "detected"
    TRIAGED = "triaged"
    PLANNED = "planned"
    APPROVED = "approved"
    REMEDIATED = "remediated"
    VALIDATED = "validated"
    CLOSED = "closed"


class HumanReviewStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Incident(ReliabilityContract):
    incident_id: str
    asset_name: str
    partition: str
    incident_type: str
    severity: IncidentSeverity
    status: IncidentStatus
    owner: str
    evidence_refs: list[str] = Field(min_length=1)
    affected_assets: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    human_review_status: HumanReviewStatus = HumanReviewStatus.PENDING
