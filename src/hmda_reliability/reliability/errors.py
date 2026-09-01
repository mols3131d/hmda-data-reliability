"""신뢰성(Reliability) 도메인 예외 정의 모듈."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError


class ReliabilityError(Exception):
    """신뢰성 애플리케이션 예외의 기본 클래스."""


class ProfileSnapshotError(ReliabilityError):
    """프로파일 스냅샷 계산 실패 시 발생하는 예외."""


class TableStateIdentityError(ReliabilityError):
    """전체 테이블 상태 식별자 계산 실패 시 발생하는 예외."""


class SchemaRecoveryCandidateError(ReliabilityError):
    """타깃 접근 전 스키마 복구 후보 사전 점검 실패 시 발생하는 예외."""

    def __init__(
        self,
        message: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.context = dict(context or {})


class SchemaRecoveryValidationError(ReliabilityError):
    """스키마 복구 대상 정합성 검증 또는 유효성 검증 실패 시 발생하는 예외."""

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
    """승인 게이트에서 실행이 거부되었을 때 발생하는 예외."""


class BackfillValidationError(ReliabilityError):
    """승인된 backfill 검증 실패 시 발생하는 예외."""

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
    """테이블 메타데이터 증거 조회 실패 시 발생하는 예외."""


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
