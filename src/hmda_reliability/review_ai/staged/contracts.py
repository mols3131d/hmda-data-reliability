"""원문 단계 답변과 코드가 조립하는 검토 collection의 계약."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator, model_validator

from hmda_reliability.reliability.contracts.base import ReliabilityContract
from hmda_reliability.review_ai.contracts import AgenticReviewInput, NullSpikeFacts

StageId = Literal["evidence_review", "draft_critique", "synthesis"]
STAGE_IDS: tuple[StageId, ...] = ("evidence_review", "draft_critique", "synthesis")


class StageAnswer(ReliabilityContract):
    stage_id: StageId
    text: str = Field(min_length=1)

    @field_validator("text")
    @classmethod
    def _reject_blank_text(cls, value: str) -> str:
        if not value.strip():
            msg = "stage answer text must not be blank"
            raise ValueError(msg)
        return value


class StagedReviewOutput(ReliabilityContract):
    workflow_version: Literal["staged-v1"] = "staged-v1"
    incident_id: str
    incident_type: Literal["null_spike"]
    target_column: str
    deterministic_facts: NullSpikeFacts
    stages: tuple[StageAnswer, ...] = Field(min_length=3, max_length=3)

    @model_validator(mode="after")
    def _validate_stage_order(self) -> StagedReviewOutput:
        if tuple(answer.stage_id for answer in self.stages) != STAGE_IDS:
            msg = "stage answers must follow the complete fixed stage order"
            raise ValueError(msg)
        return self


def assemble_staged_output(
    review_input: AgenticReviewInput, stages: tuple[StageAnswer, ...]
) -> StagedReviewOutput:
    return StagedReviewOutput(
        incident_id=review_input.incident.incident_id,
        incident_type="null_spike",
        target_column=review_input.target_column,
        deterministic_facts=review_input.deterministic_facts.model_copy(deep=True),
        stages=stages,
    )
