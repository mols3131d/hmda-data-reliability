"""Versioned human rubric과 Review AI utility comparison을 소유한다."""

from __future__ import annotations

import hashlib
import json
from enum import StrEnum

from pydantic import Field, field_validator, model_validator

from hmda_reliability.reliability.contracts.base import ReliabilityContract
from hmda_reliability.review_ai.contracts import (
    AgenticReviewOutput,
    NullSpikeFacts,
    UtilityContributionKind,
)


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
    INCONCLUSIVE = "inconclusive"


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
    output_kind: str = Field(
        pattern=r"^(positive_control|negative_control|baseline|candidate)$"
    )
    output_fixture_id: str = Field(min_length=1, max_length=256)
    output_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    contribution_kinds: tuple[UtilityContributionKind, ...] = Field(
        max_length=4,
    )
    output: AgenticReviewOutput
    scores: tuple[RubricScore, ...] = Field(max_length=5)

    @field_validator("project_revision")
    @classmethod
    def _normalize_revision(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            msg = "project_revision must be non-empty"
            raise ValueError(msg)
        return normalized

    @model_validator(mode="after")
    def _validate_unique_criteria(self) -> HumanUtilityEvaluation:
        criteria = [score.criterion for score in self.scores]
        if len(criteria) != len(set(criteria)):
            msg = "rubric criteria must be unique"
            raise ValueError(msg)
        if len(self.contribution_kinds) != len(set(self.contribution_kinds)):
            msg = "utility contribution kinds must be unique"
            raise ValueError(msg)
        if utility_output_digest(self.output) != self.output_digest:
            msg = "evaluation output digest does not match its output"
            raise ValueError(msg)
        if utility_contribution_kinds(self.output) != self.contribution_kinds:
            msg = "evaluation contribution kinds must match its output"
            raise ValueError(msg)
        return self

    @property
    def is_complete(self) -> bool:
        return {score.criterion for score in self.scores} == set(RubricCriterion)

    @property
    def total_score(self) -> int:
        return sum(score.score for score in self.scores)

    def passed(self, rubric: UtilityRubric = RUBRIC_V1) -> bool:
        return self.is_complete and all(
            score.score >= rubric.pass_score for score in self.scores
        )


class UtilityControl(ReliabilityContract):
    control_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
    case_id: str = Field(min_length=1, max_length=256)
    case_version: str = Field(min_length=1, max_length=64)
    expected_outcome: str = Field(pattern=r"^(pass|fail)$")
    output_fixture_id: str = Field(min_length=1, max_length=256)
    output: AgenticReviewOutput
    expected_incident_id: str = Field(min_length=1, max_length=256)
    expected_target_column: str = Field(min_length=1, max_length=256)
    expected_deterministic_facts: NullSpikeFacts
    expected_contributions: tuple[UtilityContributionKind, ...] = Field(max_length=4)
    evaluation: HumanUtilityEvaluation

    @model_validator(mode="after")
    def _validate_output_binding(self) -> UtilityControl:
        observed_contributions = utility_contribution_kinds(self.output)
        output_digest = utility_output_digest(self.output)
        if self.output_fixture_id != self.evaluation.output_fixture_id:
            msg = "control and evaluation output fixture identities must match"
            raise ValueError(msg)
        if output_digest != self.evaluation.output_digest:
            msg = "control output digest does not match its evaluation"
            raise ValueError(msg)
        if self.output != self.evaluation.output:
            msg = "control output must match its evaluation output"
            raise ValueError(msg)
        if (
            self.output.incident_id != self.expected_incident_id
            or self.output.target_column != self.expected_target_column
            or self.output.deterministic_facts != self.expected_deterministic_facts
        ):
            msg = "control output does not match its deterministic oracle"
            raise ValueError(msg)
        if self.expected_contributions != observed_contributions:
            msg = "control expected contributions must match the actual output"
            raise ValueError(msg)
        if self.evaluation.contribution_kinds != observed_contributions:
            msg = "evaluation contribution kinds must match the actual output"
            raise ValueError(msg)
        expected_output_kind = (
            "positive_control"
            if self.expected_outcome == "pass"
            else "negative_control"
        )
        if self.evaluation.output_kind != expected_output_kind:
            msg = "control outcome must match its output kind"
            raise ValueError(msg)
        if self.expected_outcome == "pass" and not observed_contributions:
            msg = "positive control must contain utility contributions"
            raise ValueError(msg)
        if self.expected_outcome == "fail" and observed_contributions:
            msg = "negative control must be a restatement-only output"
            raise ValueError(msg)
        return self


class ControlValidationResult(ReliabilityContract):
    control_id: str
    evaluation_id: str
    invocation_id: str
    project_revision: str
    expected_outcome: str
    observed_outcome: str
    output_fixture_id: str
    output_digest: str
    contribution_kinds: tuple[UtilityContributionKind, ...]
    output: AgenticReviewOutput
    scores: tuple[RubricScore, ...]
    valid: bool


class QualityBasisValidation(ReliabilityContract):
    basis_id: str = "rubric_v1-controls"
    rubric_id: str = "rubric_v1"
    project_revision: str = Field(min_length=1, max_length=256)
    controls: tuple[ControlValidationResult, ...] = Field(max_length=8)
    valid: bool
    failure_code: str | None = Field(default=None, max_length=128)
    basis_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")


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
    baseline_evaluation_id: str = Field(min_length=1, max_length=256)
    baseline_invocation_id: str = Field(min_length=1, max_length=256)
    baseline_output_fixture_id: str = Field(min_length=1, max_length=256)
    baseline_output_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    baseline_contribution_kinds: tuple[UtilityContributionKind, ...] = Field(
        max_length=4,
    )
    candidate_evaluation_id: str = Field(min_length=1, max_length=256)
    candidate_invocation_id: str = Field(min_length=1, max_length=256)
    candidate_output_fixture_id: str = Field(min_length=1, max_length=256)
    candidate_output_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    candidate_contribution_kinds: tuple[UtilityContributionKind, ...] = Field(
        max_length=4,
    )
    baseline_output: AgenticReviewOutput
    candidate_output: AgenticReviewOutput
    change_under_test: str = Field(min_length=1, max_length=1_024)
    status: UtilityComparisonStatus
    quality_basis_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    criterion_deltas: tuple[CriterionDelta, ...] = Field(max_length=5)
    baseline_total: int = Field(ge=0, le=10)
    candidate_total: int = Field(ge=0, le=10)
    total_delta: int = Field(ge=-10, le=10)
    decision: HumanDecision | None = None
    rationale: str = Field(min_length=1, max_length=2_048)
    blocker_code: str | None = Field(default=None, max_length=128)

    @field_validator("project_revision")
    @classmethod
    def _normalize_revision(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            msg = "project_revision must be non-empty"
            raise ValueError(msg)
        return normalized

    @model_validator(mode="after")
    def _validate_comparison_boundary(self) -> UtilityComparisonEvidence:
        if utility_output_digest(self.baseline_output) != self.baseline_output_digest:
            msg = "baseline output digest does not match comparison evidence"
            raise ValueError(msg)
        if utility_output_digest(self.candidate_output) != self.candidate_output_digest:
            msg = "candidate output digest does not match comparison evidence"
            raise ValueError(msg)
        if (
            utility_contribution_kinds(self.baseline_output)
            != self.baseline_contribution_kinds
            or utility_contribution_kinds(self.candidate_output)
            != self.candidate_contribution_kinds
        ):
            msg = "comparison contribution kinds do not match output evidence"
            raise ValueError(msg)
        if self.total_delta != self.candidate_total - self.baseline_total:
            msg = "comparison total delta does not match totals"
            raise ValueError(msg)
        if self.status is UtilityComparisonStatus.COMPARED:
            if self.decision is None or self.blocker_code is not None:
                msg = "compared evidence requires a human decision and no blocker"
                raise ValueError(msg)
            if len(self.criterion_deltas) != len(RubricCriterion):
                msg = "compared evidence requires all rubric criterion deltas"
                raise ValueError(msg)
        elif self.decision is not None or self.blocker_code is None:
            msg = (
                "blocked or inconclusive evidence cannot accept or promote a candidate"
            )
            raise ValueError(msg)
        return self


class UtilityProofCase(ReliabilityContract):
    case_id: str = Field(min_length=1, max_length=256)
    case_version: str = Field(min_length=1, max_length=64)
    fixture_id: str = Field(min_length=1, max_length=256)
    project_revision: str = Field(min_length=1, max_length=256)
    input_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    baseline_output_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    candidate_output_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    expected_contributions: tuple[UtilityContributionKind, ...] = Field(
        min_length=1,
        max_length=4,
    )

    @field_validator("project_revision")
    @classmethod
    def _normalize_revision(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            msg = "project_revision must be non-empty"
            raise ValueError(msg)
        return normalized


class UtilityProofBundle(ReliabilityContract):
    proof_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
    case: UtilityProofCase
    quality_basis: QualityBasisValidation
    comparison: UtilityComparisonEvidence

    @model_validator(mode="after")
    def _validate_bundle_links(self) -> UtilityProofBundle:
        if (
            self.case.case_id != self.comparison.case_id
            or self.case.case_version != self.comparison.case_version
        ):
            msg = "proof case and comparison identity must match"
            raise ValueError(msg)
        if self.comparison.quality_basis_digest != self.quality_basis.basis_digest:
            msg = "proof comparison must reference its quality basis"
            raise ValueError(msg)
        if self.case.project_revision != self.comparison.project_revision:
            msg = "proof case and comparison revision must match"
            raise ValueError(msg)
        if self.quality_basis.valid and (
            self.case.project_revision != self.quality_basis.project_revision
        ):
            msg = "proof case and quality basis revision must match"
            raise ValueError(msg)
        if (
            self.case.baseline_output_digest != self.comparison.baseline_output_digest
            or self.case.candidate_output_digest
            != self.comparison.candidate_output_digest
        ):
            msg = "proof case must reference the compared output digests"
            raise ValueError(msg)
        if tuple(self.case.expected_contributions) != tuple(
            self.comparison.candidate_contribution_kinds
        ):
            msg = "proof case expected contributions must match candidate output"
            raise ValueError(msg)
        return self


def validate_quality_basis(
    controls: list[UtilityControl] | tuple[UtilityControl, ...],
    rubric: UtilityRubric = RUBRIC_V1,
) -> QualityBasisValidation:
    """Positive/negative control 결과가 rubric 판별력을 갖는지 검증한다."""

    results: list[ControlValidationResult] = []
    valid = True
    failure_code: str | None = None
    seen: set[str] = set()
    project_revisions = {control.evaluation.project_revision for control in controls}
    control_case_identities = {
        (control.case_id, control.case_version) for control in controls
    }
    project_revision = next(iter(project_revisions), "unavailable")
    for control in controls:
        observed = "pass" if control.evaluation.passed(rubric) else "fail"
        observed_contributions = utility_contribution_kinds(control.output)
        output_digest = utility_output_digest(control.output)
        item_valid = (
            control.control_id not in seen
            and control.case_id == control.evaluation.case_id
            and control.case_version == control.evaluation.case_version
            and control.evaluation.rubric_id == rubric.rubric_id
            and control.evaluation.is_complete
            and control.evaluation.output_fixture_id == control.output_fixture_id
            and control.evaluation.output_digest == output_digest
            and control.evaluation.contribution_kinds == observed_contributions
            and control.expected_contributions == observed_contributions
            and control.output == control.evaluation.output
            and control.output.incident_id == control.expected_incident_id
            and control.output.target_column == control.expected_target_column
            and control.output.deterministic_facts
            == control.expected_deterministic_facts
            and control.expected_outcome == observed
        )
        seen.add(control.control_id)
        results.append(
            ControlValidationResult(
                control_id=control.control_id,
                evaluation_id=control.evaluation.evaluation_id,
                invocation_id=control.evaluation.invocation_id,
                project_revision=control.evaluation.project_revision,
                expected_outcome=control.expected_outcome,
                observed_outcome=observed,
                output_fixture_id=control.output_fixture_id,
                output_digest=output_digest,
                contribution_kinds=observed_contributions,
                output=control.output,
                scores=control.evaluation.scores,
                valid=item_valid,
            )
        )
        if not item_valid:
            valid = False
            failure_code = failure_code or (
                "control_incomplete"
                if not control.evaluation.is_complete
                else "control_mismatch"
            )

    control_kinds = {control.evaluation.output_kind for control in controls}
    if control_kinds != {"positive_control", "negative_control"}:
        valid = False
        failure_code = failure_code or "controls_incomplete"
    if len(project_revisions) != 1:
        valid = False
        failure_code = failure_code or "control_revision_mismatch"
    if len(control_case_identities) != 1:
        valid = False
        failure_code = failure_code or "control_case_mismatch"
    payload = [result.model_dump(mode="json") for result in results]
    basis_digest = (
        f"sha256:{hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()}"
    )
    return QualityBasisValidation(
        rubric_id=rubric.rubric_id,
        project_revision=project_revision,
        controls=tuple(results),
        valid=valid,
        failure_code=failure_code,
        basis_digest=basis_digest,
    )


def compare_utility_evaluations(
    *,
    comparison_id: str,
    baseline: HumanUtilityEvaluation,
    candidate: HumanUtilityEvaluation,
    quality_basis: QualityBasisValidation,
    change_under_test: str,
    decision: HumanDecision,
    rationale: str,
) -> UtilityComparisonEvidence:
    """동일 case/rubric의 human evaluation을 비교하거나 fail closed한다."""

    blocker: str | None = None
    if not quality_basis.valid:
        blocker = quality_basis.failure_code or "invalid_quality_basis"
    elif (
        baseline.case_id != candidate.case_id
        or baseline.case_version != candidate.case_version
    ):
        blocker = "case_mismatch"
    elif baseline.rubric_id != candidate.rubric_id:
        blocker = "rubric_mismatch"
    elif baseline.project_revision != candidate.project_revision:
        blocker = "project_revision_mismatch"
    elif not baseline.is_complete or not candidate.is_complete:
        blocker = "evaluation_incomplete"

    baseline_by_criterion = {score.criterion: score.score for score in baseline.scores}
    candidate_by_criterion = {
        score.criterion: score.score for score in candidate.scores
    }
    deltas = tuple(
        CriterionDelta(
            criterion=criterion,
            baseline_score=baseline_by_criterion.get(criterion, 0),
            candidate_score=candidate_by_criterion.get(criterion, 0),
            delta=candidate_by_criterion.get(criterion, 0)
            - baseline_by_criterion.get(criterion, 0),
        )
        for criterion in RubricCriterion
        if criterion in baseline_by_criterion and criterion in candidate_by_criterion
    )
    return UtilityComparisonEvidence(
        comparison_id=comparison_id,
        case_id=baseline.case_id,
        case_version=baseline.case_version,
        project_revision=baseline.project_revision,
        rubric_id=baseline.rubric_id,
        baseline_evaluation_id=baseline.evaluation_id,
        baseline_invocation_id=baseline.invocation_id,
        baseline_output_fixture_id=baseline.output_fixture_id,
        baseline_output_digest=baseline.output_digest,
        baseline_contribution_kinds=baseline.contribution_kinds,
        candidate_evaluation_id=candidate.evaluation_id,
        candidate_invocation_id=candidate.invocation_id,
        candidate_output_fixture_id=candidate.output_fixture_id,
        candidate_output_digest=candidate.output_digest,
        candidate_contribution_kinds=candidate.contribution_kinds,
        baseline_output=baseline.output,
        candidate_output=candidate.output,
        change_under_test=change_under_test,
        status="blocked" if blocker else "compared",
        quality_basis_digest=quality_basis.basis_digest,
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
    """사람이 검토할 수 있는 작은 comparison evidence projection을 렌더링한다."""

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
    """Return the replayable digest bound to one exact structured output."""

    payload = _canonical_json_bytes(output.model_dump(mode="json"))
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def utility_contribution_kinds(
    output: AgenticReviewOutput,
) -> tuple[UtilityContributionKind, ...]:
    """Return contribution kinds in the output's stable order without duplicates."""

    return tuple(dict.fromkeys(item.kind for item in output.utility_contributions))
