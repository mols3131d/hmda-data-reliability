"""단계별 텍스트 실행의 원문 없는 기록과 반환 계약."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from hmda_reliability.reliability.contracts.base import ReliabilityContract
from hmda_reliability.review_ai.evidence import SanitizedAgenticReviewConfiguration
from hmda_reliability.review_ai.staged.contracts import (
    STAGE_IDS,
    StagedReviewOutput,
    StageId,
)
from hmda_reliability.review_ai.staged.settings import StagedExecutionSettings
from hmda_reliability.runtime_ai.contracts import (
    ProviderResponseMetadata,
    ProviderUsage,
)

StagedReviewStatus = Literal[
    "completed",
    "input_rejected",
    "unavailable",
    "validation_failed",
    "provenance_failed",
]


class StageRecord(ReliabilityContract):
    """원문을 별도 파일로 연결하는 단계별 checkpoint."""

    stage_id: StageId
    status: StagedReviewStatus
    prompt_digest: str | None = Field(default=None, pattern=r"^sha256:[0-9a-f]{64}$")
    prompt_bytes: int = Field(default=0, ge=0)
    response_digest: str | None = Field(default=None, pattern=r"^sha256:[0-9a-f]{64}$")
    response_path: Path | None = None
    record_path: Path | None = None
    failure_code: str | None = None
    attempt_count: int = Field(default=0, ge=0)
    latency_ms: float = Field(default=0, ge=0)
    budget_seconds: float | None = Field(default=None, ge=0)
    elapsed_ms: float | None = Field(default=None, ge=0)
    usage: ProviderUsage | None = None
    response_metadata: ProviderResponseMetadata | None = None


class StagedReviewManifest(ReliabilityContract):
    """한 사례의 단계 기록과 코드가 조립한 output의 출처."""

    workflow_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")
    workflow_version: Literal["staged-v1"] = "staged-v1"
    project_revision: str = Field(min_length=1, max_length=256)
    status: StagedReviewStatus
    configuration: SanitizedAgenticReviewConfiguration
    execution_settings: StagedExecutionSettings
    elapsed_ms: float = Field(ge=0)
    canonical_input: dict[str, object]
    stages: tuple[StageRecord, ...]
    physical_attempts: int = Field(ge=0)
    max_physical_attempts: int = Field(ge=3, le=18)
    output_digest: str | None = Field(default=None, pattern=r"^sha256:[0-9a-f]{64}$")
    output_path: Path | None = None
    failure_code: str | None = None

    @model_validator(mode="after")
    def _validate_run(self) -> StagedReviewManifest:
        if (
            tuple(stage.stage_id for stage in self.stages)
            != STAGE_IDS[: len(self.stages)]
        ):
            raise ValueError("stage records must be an ordered prefix")
        if self.physical_attempts != sum(stage.attempt_count for stage in self.stages):
            raise ValueError("physical attempt total must match stage records")
        if self.physical_attempts > self.max_physical_attempts:
            raise ValueError("physical attempts exceed the configured workflow bound")
        if self.status == "completed" and (
            len(self.stages) != len(STAGE_IDS)
            or any(stage.status != "completed" for stage in self.stages)
            or self.output_path is None
            or self.output_digest is None
            or self.failure_code is not None
        ):
            raise ValueError(
                "completed workflow requires three stages and a persisted output"
            )
        return self


class StagedReviewResult(ReliabilityContract):
    """수집 완료와 사람의 품질 판정을 구별하는 결과."""

    status: StagedReviewStatus
    workflow_id: str | None = None
    workflow_path: Path | None = None
    output_path: Path | None = None
    output: StagedReviewOutput | None = None
    stages: tuple[StageRecord, ...] = ()
    failure_code: str | None = None
