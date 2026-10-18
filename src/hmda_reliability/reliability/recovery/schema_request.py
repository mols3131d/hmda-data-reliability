"""승인된 테이블 스키마 복구 실행 요청 모델 정의 모듈."""

from pathlib import Path

from pydantic import field_validator, model_validator

from hmda_reliability.reliability.contracts import (
    ReliabilityContract,
    SchemaRecoveryApproval,
    SchemaRecoveryProposal,
)
from hmda_reliability.reliability.profiling import ProfileSnapshotRequest


class ApprovedSchemaRecoveryRequest(ReliabilityContract):
    """외부 승인된 테이블 제안에 바인딩된 실행 입력 모델."""

    approval: SchemaRecoveryApproval
    proposal: SchemaRecoveryProposal
    target_database_path: Path
    candidate_database_path: Path
    profile_request: ProfileSnapshotRequest

    @field_validator("profile_request")
    @classmethod
    def _align_profile_year(
        cls, value: ProfileSnapshotRequest
    ) -> ProfileSnapshotRequest:
        if value.partition_column not in {"activity_year", "source_year"}:
            raise ValueError(
                "recovery profile partition_column은 activity_year 또는 "
                "source_year여야 합니다."
            )
        return value.model_copy(update={"partition_column": "source_year"})

    @model_validator(mode="after")
    def _validate_exact_approval(self) -> "ApprovedSchemaRecoveryRequest":
        if not self.approval.allows_execution():
            raise ValueError("schema recovery approval status는 approved여야 합니다.")
        if self.approval.recovery_proposal != self.proposal:
            raise ValueError("execution proposal은 approved proposal과 같아야 합니다.")
        if self.approval.requested_actions != self.proposal.target_actions:
            raise ValueError("execution actions는 approved proposal과 같아야 합니다.")
        if self.profile_request.table_name != self.proposal.table_name:
            raise ValueError(
                "profile request table은 schema recovery target과 같아야 합니다."
            )
        if str(self.profile_request.partition) != self.proposal.observation_partition:
            raise ValueError(
                "profile request partition은 incident observation "
                "partition과 같아야 합니다."
            )
        return self
