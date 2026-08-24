"""Reliability domain exceptions."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError


class ReliabilityError(Exception):
    """Reliability application error base class."""


class ProfileSnapshotError(ReliabilityError):
    """Profile snapshot calculation failed."""


class TableStateIdentityError(ReliabilityError):
    """Complete table state identity calculation failed."""


class SchemaRecoveryCandidateError(ReliabilityError):
    """Schema recovery candidate preflight failed before target access."""

    def __init__(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.context = dict(context or {})


class SchemaRecoveryValidationError(ReliabilityError):
    """Schema recovery target reconciliation or validation failed."""

    def __init__(
        self,
        message: str,
        *,
        failure_stage: str,
        mutation_state: str | None = None,
        reconciliation_action: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.failure_stage = failure_stage
        self.mutation_state = mutation_state
        self.reconciliation_action = reconciliation_action
        self.context = dict(context or {})


class ApprovalGateError(ReliabilityError):
    """Approval gate rejected execution."""


class BackfillValidationError(ReliabilityError):
    """Approved backfill validation failed."""

    def __init__(
        self,
        message: str,
        *,
        mutation_state: str | None = None,
        reconciliation_action: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.mutation_state = mutation_state
        self.reconciliation_action = reconciliation_action
        self.context = dict(context or {})


class TableMetadataEvidenceError(ReliabilityError):
    """Table metadata evidence lookup failed."""


class ImpactAnalysisError(ReliabilityError):
    """dbt artifact 영향 분석 실패를 나타낸다."""


class RemediationError(ReliabilityError):
    """Remediation workflow 실패를 나타낸다."""


class ContractValidationError(ReliabilityError):
    """Contract validation failed."""

    def __init__(self, contract_name: str, details: list[str]) -> None:
        self.contract_name = contract_name
        self.details = details
        message = f"{contract_name} contract validation failed"
        super().__init__(message)

    @classmethod
    def from_validation_error(
        cls,
        contract_name: str,
        error: ValidationError,
    ) -> ContractValidationError:
        details = [
            f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}"
            for item in error.errors()
        ]
        return cls(contract_name=contract_name, details=details)
