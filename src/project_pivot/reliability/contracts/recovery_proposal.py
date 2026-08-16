"""Exact content and freshness recovery proposal contracts."""

from datetime import UTC, datetime, timedelta

from pydantic import Field, field_validator, model_validator

from project_pivot.hmda_data import PartitionContentIdentity
from project_pivot.reliability.contracts.base import ReliabilityContract
from project_pivot.reliability.contracts.profile import FreshnessMeasurementStatus


class FreshnessObservation(ReliabilityContract):
    """A freshness measurement tied to its observation clock."""

    freshness_status: FreshnessMeasurementStatus
    freshness_at: datetime | None
    observed_at: datetime

    @field_validator("freshness_at", "observed_at")
    @classmethod
    def _normalize_timestamp(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def _validate_measurement(self) -> "FreshnessObservation":
        if (
            self.freshness_status is FreshnessMeasurementStatus.MEASURED
            and self.freshness_at is None
        ):
            raise ValueError("measured freshness observation requires freshness_at")
        if (
            self.freshness_status is FreshnessMeasurementStatus.UNAVAILABLE
            and self.freshness_at is not None
        ):
            raise ValueError("unavailable freshness observation forbids freshness_at")
        if self.freshness_at is not None and self.freshness_at > self.observed_at:
            raise ValueError("freshness observation cannot be in the future")
        return self


class FreshnessRecoveryBinding(ReliabilityContract):
    """Approved stale state and exact expected recovery timestamp."""

    approved_before: FreshnessObservation
    expected_after_freshness_at: datetime
    max_age_minutes: float = Field(ge=0.0)

    @field_validator("expected_after_freshness_at")
    @classmethod
    def _normalize_expected_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def _validate_stale_before(self) -> "FreshnessRecoveryBinding":
        before = self.approved_before
        if (
            before.freshness_status is not FreshnessMeasurementStatus.MEASURED
            or before.freshness_at is None
        ):
            raise ValueError("freshness recovery approved before must be measured")
        age = before.observed_at - before.freshness_at
        if age < timedelta(minutes=self.max_age_minutes):
            raise ValueError(
                "freshness recovery approved before must be stale at max_age"
            )
        return self


class RecoveryProposal(ReliabilityContract):
    """Immutable target, candidate, evidence, and action set presented for approval."""

    proposal_id: str
    incident_id: str
    incident_type: str = Field(min_length=1)
    table_name: str
    source_year: int = Field(ge=2000, le=2100)
    source_file: str | None = None
    candidate_identity: PartitionContentIdentity
    approved_before_identity: PartitionContentIdentity
    expected_after_identity: PartitionContentIdentity
    validation_evidence_refs: tuple[str, ...] = Field(min_length=1)
    dbt_projection_id: str
    target_actions: tuple[str, ...] = Field(min_length=1)
    freshness_binding: FreshnessRecoveryBinding | None = None

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
        if self.incident_type == "freshness_delay" and self.freshness_binding is None:
            raise ValueError(
                "freshness_delay recovery proposal requires freshness binding"
            )
        if (
            self.incident_type != "freshness_delay"
            and self.freshness_binding is not None
        ):
            raise ValueError("content recovery proposal forbids freshness binding")
        return self
