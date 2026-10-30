"""점수 모델 없이 사례·실행·정확한 출력의 연결만 확인한다."""

import hashlib
from dataclasses import dataclass

from hmda_reliability.review_ai.contracts import AgenticReviewInput
from hmda_reliability.review_ai.prompt import canonical_json_bytes
from hmda_reliability.review_ai.staged.contracts import StagedReviewOutput

CRITERIA = (
    "added_value",
    "actionability",
    "evidence_awareness",
    "uncertainty_handling",
    "prioritization",
)


def digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def case_payload_digest(value: AgenticReviewInput) -> str:
    return digest(
        value.model_dump(mode="json", include={"incident", "evidence", "draft"})
    )


def review_output_digest(value: StagedReviewOutput) -> str:
    return digest(value.model_dump(mode="json"))


@dataclass(frozen=True)
class ReviewTarget:
    case_id: str
    case_version: str
    case_digest: str
    workflow_id: str
    project_revision: str
    canonical_input_digest: str
    output_digest: str
    trace_id: str
    observation_id: str
    run_id: str


def check_comparable_targets(
    baseline: ReviewTarget, candidate: ReviewTarget
) -> str | None:
    if (baseline.case_id, baseline.case_version, baseline.case_digest) != (
        candidate.case_id,
        candidate.case_version,
        candidate.case_digest,
    ):
        return "case_mismatch"
    if (
        baseline.workflow_id == candidate.workflow_id
        and baseline.output_digest != candidate.output_digest
    ):
        return "workflow_output_conflict"
    return None
