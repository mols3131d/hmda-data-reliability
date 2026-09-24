"""Versioned human rubric과 Review AI utility comparison 계약."""

from __future__ import annotations

import hashlib
import json
from enum import StrEnum

from pydantic import Field, model_validator

from hmda_reliability.reliability.contracts.base import ReliabilityContract
from hmda_reliability.review_ai.contracts import AgenticReviewOutput


class RubricCriterion(StrEnum):
    ADDED_VALUE = "added_value"
    ACTIONABILITY = "actionability"
    EVIDENCE_AWARENESS = "evidence_awareness"
    UNCERTAINTY_HANDLING = "uncertainty_handling"
    PRIORITIZATION = "prioritization"


class HumanDecision(StrEnum):
    ACCEPT = "accept"
    REJECT = "reject"
    NO_CHANGE = "no_change"


class UtilityComparisonStatus(StrEnum):
    COMPARED = "compared"
    BLOCKED = "blocked"


class UtilityRubric(ReliabilityContract):
    rubric_id: str = Field(pattern=r"^rubric_v1$")
    criteria: tuple[RubricCriterion, ...] = Field(min_length=5, max_length=5)
    score_min: int = Field(ge=0, le=2)
    score_max: int = Field(ge=0, le=2)
    pass_score: int = Field(ge=0, le=2)

    @model_validator(mode="after")
    def _validate_rubric(self) -> UtilityRubric:
        if self.criteria != tuple(RubricCriterion):
            msg = "rubric_v1 must contain all five criteria in stable order"
            raise ValueError(msg)
        if self.score_min >= self.score_max:
            msg = "rubric score range must have a positive width"
            raise ValueError(msg)
        if not self.score_min <= self.pass_score <= self.score_max:
            msg = "rubric pass score must be inside the score range"
            raise ValueError(msg)
        return self


RUBRIC_V1 = UtilityRubric(
    rubric_id="rubric_v1",
    criteria=tuple(RubricCriterion),
    score_min=0,
    score_max=2,
    pass_score=1,
)


class RubricScore(ReliabilityContract):
    criterion: RubricCriterion
    score: int = Field(ge=0, le=2)
    rationale: str = Field(min_length=1, max_length=1_024)

    @model_validator(mode="after")
    def _normalize_rationale(self) -> RubricScore:
        if not self.rationale.strip():
            msg = "rubric rationale must be non-empty"
            raise ValueError(msg)
        return self


class HumanUtilityEvaluation(ReliabilityContract):
    evaluation_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
    case_id: str = Field(min_length=1, max_length=256)
    case_version: str = Field(min_length=1, max_length=64)
    invocation_id: str = Field(min_length=1, max_length=256)
    project_revision: str = Field(min_length=1, max_length=256)
    rubric_id: str = Field(pattern=r"^rubric_v1$")
    output_kind: str = Field(pattern=r"^(baseline|candidate)$")
    output_fixture_id: str = Field(min_length=1, max_length=256)
    output_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    output: AgenticReviewOutput
    scores: tuple[RubricScore, ...] = Field(min_length=5, max_length=5)

    @model_validator(mode="after")
    def _validate_evaluation(self) -> HumanUtilityEvaluation:
        if (
            not self.project_revision
            or self.project_revision != self.project_revision.strip()
        ):
            msg = "project_revision must be non-empty and normalized"
            raise ValueError(msg)
        criteria = [score.criterion for score in self.scores]
        if criteria != list(RubricCriterion):
            msg = "evaluation must score each rubric criterion exactly once in order"
            raise ValueError(msg)
        if utility_output_digest(self.output) != self.output_digest:
            msg = "evaluation output digest does not match its output"
            raise ValueError(msg)
        return self

    @property
    def total_score(self) -> int:
        return sum(score.score for score in self.scores)


class CriterionDelta(ReliabilityContract):
    criterion: RubricCriterion
    baseline_score: int = Field(ge=0, le=2)
    candidate_score: int = Field(ge=0, le=2)
    delta: int = Field(ge=-2, le=2)

    @model_validator(mode="after")
    def _validate_delta(self) -> CriterionDelta:
        if self.delta != self.candidate_score - self.baseline_score:
            msg = "criterion delta does not match baseline and candidate scores"
            raise ValueError(msg)
        return self


class UtilityComparisonEvidence(ReliabilityContract):
    comparison_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
    case_id: str = Field(min_length=1, max_length=256)
    case_version: str = Field(min_length=1, max_length=64)
    project_revision: str = Field(min_length=1, max_length=256)
    rubric_id: str = Field(pattern=r"^rubric_v1$")
    baseline_evaluation_id: str = Field(min_length=1, max_length=128)
    baseline_output_kind: str = Field(pattern=r"^(baseline|candidate)$")
    baseline_invocation_id: str = Field(min_length=1, max_length=256)
    baseline_output_fixture_id: str = Field(min_length=1, max_length=256)
    baseline_output_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    candidate_evaluation_id: str = Field(min_length=1, max_length=128)
    candidate_invocation_id: str = Field(min_length=1, max_length=256)
    candidate_output_fixture_id: str = Field(min_length=1, max_length=256)
    candidate_output_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    baseline_output: AgenticReviewOutput
    candidate_output: AgenticReviewOutput
    candidate_output_kind: str = Field(pattern=r"^(baseline|candidate)$")
    change_under_test: str = Field(min_length=1, max_length=1_024)
    status: UtilityComparisonStatus
    criterion_deltas: tuple[CriterionDelta, ...] = Field(max_length=5)
    baseline_total: int = Field(ge=0, le=10)
    candidate_total: int = Field(ge=0, le=10)
    total_delta: int = Field(ge=-10, le=10)
    decision: HumanDecision | None = None
    rationale: str = Field(min_length=1, max_length=2_048)
    blocker_code: str | None = Field(default=None, max_length=128)

    @model_validator(mode="after")
    def _validate_comparison_boundary(self) -> UtilityComparisonEvidence:
        if self.total_delta != self.candidate_total - self.baseline_total:
            msg = "comparison total delta does not match totals"
            raise ValueError(msg)
        if (
            utility_output_digest(self.baseline_output) != self.baseline_output_digest
            or utility_output_digest(self.candidate_output)
            != self.candidate_output_digest
        ):
            msg = "comparison output digest does not match output"
            raise ValueError(msg)
        if self.status is UtilityComparisonStatus.COMPARED:
            if self.decision is None or self.blocker_code is not None:
                msg = "compared evidence requires a human decision and no blocker"
                raise ValueError(msg)
            if (
                self.baseline_output_kind != "baseline"
                or self.candidate_output_kind != "candidate"
            ):
                msg = (
                    "compared evidence requires baseline output role and "
                    "candidate output role"
                )
                raise ValueError(msg)
            criteria = [delta.criterion for delta in self.criterion_deltas]
            if criteria != list(RubricCriterion):
                msg = "compared evidence requires one delta per rubric criterion"
                raise ValueError(msg)
            if (
                sum(delta.baseline_score for delta in self.criterion_deltas)
                != self.baseline_total
                or sum(delta.candidate_score for delta in self.criterion_deltas)
                != self.candidate_total
                or sum(delta.delta for delta in self.criterion_deltas)
                != self.total_delta
            ):
                msg = "comparison totals must match criterion deltas"
                raise ValueError(msg)
            if (
                self.baseline_output.incident_id != self.candidate_output.incident_id
                or self.baseline_output.target_column
                != self.candidate_output.target_column
                or self.baseline_output.deterministic_facts
                != self.candidate_output.deterministic_facts
            ):
                msg = "compared outputs must share deterministic incident facts"
                raise ValueError(msg)
        elif self.decision is not None or self.blocker_code is None:
            msg = "blocked evidence cannot accept or promote a candidate"
            raise ValueError(msg)
        return self


def compare_utility_evaluations(
    *,
    comparison_id: str,
    baseline: HumanUtilityEvaluation,
    candidate: HumanUtilityEvaluation,
    change_under_test: str,
    decision: HumanDecision,
    rationale: str,
) -> UtilityComparisonEvidence:
    """동일 case/rubric의 human evaluation을 비교하거나 fail closed한다."""

    blocker: str | None = None
    if baseline.output_kind != "baseline" or candidate.output_kind != "candidate":
        blocker = "evaluation_role_mismatch"
    elif (
        baseline.case_id != candidate.case_id
        or baseline.case_version != candidate.case_version
    ):
        blocker = "case_mismatch"
    elif baseline.rubric_id != candidate.rubric_id:
        blocker = "rubric_mismatch"
    elif baseline.project_revision != candidate.project_revision:
        blocker = "project_revision_mismatch"
    elif (
        baseline.output.incident_id != candidate.output.incident_id
        or baseline.output.target_column != candidate.output.target_column
        or baseline.output.deterministic_facts != candidate.output.deterministic_facts
    ):
        blocker = "same_case_fact_mismatch"

    baseline_scores = {score.criterion: score.score for score in baseline.scores}
    candidate_scores = {score.criterion: score.score for score in candidate.scores}
    deltas = tuple(
        CriterionDelta(
            criterion=criterion,
            baseline_score=baseline_scores[criterion],
            candidate_score=candidate_scores[criterion],
            delta=candidate_scores[criterion] - baseline_scores[criterion],
        )
        for criterion in RubricCriterion
    )
    return UtilityComparisonEvidence(
        comparison_id=comparison_id,
        case_id=baseline.case_id,
        case_version=baseline.case_version,
        project_revision=baseline.project_revision,
        rubric_id=baseline.rubric_id,
        baseline_evaluation_id=baseline.evaluation_id,
        baseline_output_kind=baseline.output_kind,
        baseline_invocation_id=baseline.invocation_id,
        baseline_output_fixture_id=baseline.output_fixture_id,
        baseline_output_digest=baseline.output_digest,
        candidate_evaluation_id=candidate.evaluation_id,
        candidate_invocation_id=candidate.invocation_id,
        candidate_output_fixture_id=candidate.output_fixture_id,
        candidate_output_digest=candidate.output_digest,
        baseline_output=baseline.output,
        candidate_output=candidate.output,
        candidate_output_kind=candidate.output_kind,
        change_under_test=change_under_test,
        status=UtilityComparisonStatus.BLOCKED
        if blocker
        else UtilityComparisonStatus.COMPARED,
        criterion_deltas=deltas,
        baseline_total=baseline.total_score,
        candidate_total=candidate.total_score,
        total_delta=candidate.total_score - baseline.total_score,
        decision=None if blocker else decision,
        rationale=rationale,
        blocker_code=blocker,
    )


def render_utility_comparison_markdown(
    comparison: UtilityComparisonEvidence,
) -> str:
    """사람이 검토할 수 있는 작은 comparison projection을 렌더링한다."""

    lines = [
        "# Review AI Utility Comparison",
        "",
        f"- Case: `{comparison.case_id}` ({comparison.case_version})",
        f"- Rubric: `{comparison.rubric_id}`",
        f"- Status: `{comparison.status.value}`",
        "- Decision: `"
        f"{comparison.decision.value if comparison.decision else 'blocked'}`",
        f"- Change under test: {comparison.change_under_test}",
        "",
        "| Criterion | Baseline | Candidate | Delta |",
        "|---|---:|---:|---:|",
    ]
    lines.extend(
        f"| {delta.criterion.value} | {delta.baseline_score} | "
        f"{delta.candidate_score} | {delta.delta:+d} |"
        for delta in comparison.criterion_deltas
    )
    lines.extend(["", f"Rationale: {comparison.rationale}", ""])
    if comparison.blocker_code:
        lines.extend([f"Blocker: `{comparison.blocker_code}`", ""])
    return "\n".join(lines)


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def utility_output_digest(output: AgenticReviewOutput) -> str:
    """Return a replayable digest bound to one exact structured output."""

    payload = _canonical_json_bytes(output.model_dump(mode="json"))
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"
