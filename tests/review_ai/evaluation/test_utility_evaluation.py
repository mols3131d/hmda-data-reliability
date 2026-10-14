"""Human-rubric utility evaluation and comparison contract tests."""

from __future__ import annotations

import json
from importlib import import_module
from pathlib import Path

import pytest
from pydantic import ValidationError

from hmda_reliability.review_ai.contracts import (
    AgenticReviewOutput,
    AgenticReviewUtilityContribution,
    UtilityContributionKind,
)
from hmda_reliability.review_ai.evaluation import (
    RUBRIC_V1,
    HumanDecision,
    ReviewValueAssessment,
    ReviewValueComparisonEvidence,
    ReviewValueComparisonStatus,
    RubricCriterion,
    RubricScore,
    compare_review_value,
    render_review_value_comparison_markdown,
    review_output_digest,
)

pytestmark = pytest.mark.unit


def _scores(value: int) -> tuple[RubricScore, ...]:
    return tuple(
        RubricScore(
            criterion=criterion,
            score=value,
            rationale=f"Human rationale for {criterion.value}.",
        )
        for criterion in RubricCriterion
    )


def _output(*, utility: bool = False) -> AgenticReviewOutput:
    contributions = (
        (
            AgenticReviewUtilityContribution(
                kind=UtilityContributionKind.EVIDENCE_GAP,
                description="Lineage evidence remains unconfirmed.",
                evidence_refs=("ev-1",),
            ),
        )
        if utility
        else ()
    )
    return AgenticReviewOutput(
        incident_id="incident-1",
        incident_type="null_spike",
        target_column="income",
        deterministic_facts={
            "baseline_null_rate": 0.01,
            "current_null_rate": 0.21,
            "delta": 0.2,
            "threshold": 0.1,
        },
        review_summary=(
            "The output adds an evidence gap."
            if utility
            else "The output restates the deterministic facts."
        ),
        evidence_used=("ev-1",),
        findings=(),
        uncertainties=("Root cause remains unconfirmed.",),
        advisory_recommendation="needs_human_review",
        utility_contributions=contributions,
    )


def _evaluation(
    *,
    evaluation_id: str,
    invocation_id: str,
    output_kind: str,
    score: int,
    case_id: str = "null-spike-case",
    case_version: str = "v1",
    project_revision: str = "revision-1",
    output: AgenticReviewOutput | None = None,
) -> ReviewValueAssessment:
    output = output or _output(utility=output_kind == "candidate")
    return ReviewValueAssessment(
        evaluation_id=evaluation_id,
        case_id=case_id,
        case_version=case_version,
        invocation_id=invocation_id,
        project_revision=project_revision,
        rubric_id=RUBRIC_V1.rubric_id,
        output_kind=output_kind,
        output_fixture_id=f"fixture-{output_kind}",
        output_digest=review_output_digest(output),
        output=output,
        scores=_scores(score),
    )


def _compare(
    *,
    baseline: ReviewValueAssessment | None = None,
    candidate: ReviewValueAssessment | None = None,
    decision: HumanDecision = HumanDecision.ACCEPT,
) -> ReviewValueComparisonEvidence:
    return compare_review_value(
        comparison_id="comparison-1",
        baseline=baseline
        or _evaluation(
            evaluation_id="evaluation-baseline",
            invocation_id="invocation-baseline",
            output_kind="baseline",
            score=0,
        ),
        candidate=candidate
        or _evaluation(
            evaluation_id="evaluation-candidate",
            invocation_id="invocation-candidate",
            output_kind="candidate",
            score=2,
        ),
        change_under_test="Add bounded context utility contribution.",
        decision=decision,
        rationale="The candidate adds an actionable, evidence-bound contribution.",
    )


def test_review_value_api_exposes_only_intended_names() -> None:
    value_api = import_module("hmda_reliability.review_ai.evaluation.value")
    evaluation_api = import_module("hmda_reliability.review_ai.evaluation")
    public_api = import_module("hmda_reliability.review_ai")

    assert evaluation_api.ReviewValueRubric is value_api.ReviewValueRubric
    assert set(evaluation_api.__all__) == {
        "RUBRIC_V1",
        "CriterionDelta",
        "HumanDecision",
        "ReviewValueAssessment",
        "ReviewValueComparisonEvidence",
        "ReviewValueComparisonStatus",
        "ReviewValueRubric",
        "RubricCriterion",
        "RubricScore",
        "compare_review_value",
        "render_review_value_comparison_markdown",
        "review_output_digest",
    }
    assert "HumanUtilityEvaluation" not in evaluation_api.__all__
    assert "ReviewValueAssessment" in public_api.__all__
    assert "ReviewValueComparisonEvidence" in public_api.__all__
    assert "HumanUtilityEvaluation" not in public_api.__all__


@pytest.mark.parametrize(
    ("decision", "case_version", "golden_key"),
    [
        ("accept", "v1", "compared"),
        ("reject", "v1", "compared"),
        ("no_change", "v1", "compared"),
        ("accept", "v2", "blocked"),
    ],
)
def test_comparison_json_matches_pre_refactor_golden(
    decision: str, case_version: str, golden_key: str
) -> None:
    """Compare complete JSON to the captured 6e64cc7 API, including nested types."""
    fixture = Path(__file__).with_name("fixtures") / "utility_comparison_6e64cc7.json"
    expected = json.loads(fixture.read_text(encoding="utf-8"))[golden_key]
    if golden_key == "compared":
        expected["decision"] = decision

    candidate = _evaluation(
        evaluation_id="evaluation-candidate",
        invocation_id="invocation-candidate",
        output_kind="candidate",
        score=2,
        case_version=case_version,
    )
    actual = _compare(candidate=candidate, decision=HumanDecision(decision))

    # JSON text also distinguishes bool/int and int/float values that Python equals.
    assert json.dumps(actual.model_dump(mode="json"), sort_keys=True) == json.dumps(
        expected, sort_keys=True
    )


def test_rubric_and_evaluation_require_all_five_human_scores() -> None:
    evaluation = _evaluation(
        evaluation_id="evaluation-complete",
        invocation_id="invocation-complete",
        output_kind="candidate",
        score=1,
    )

    assert RUBRIC_V1.criteria == tuple(RubricCriterion)
    assert evaluation.total_score == 5

    payload = evaluation.model_dump(mode="json")
    payload["scores"] = payload["scores"][:-1]

    with pytest.raises(ValidationError, match="at least 5 items"):
        ReviewValueAssessment.model_validate(payload)


def test_evaluation_digest_is_bound_to_exact_review_output() -> None:
    evaluation = _evaluation(
        evaluation_id="evaluation-digest",
        invocation_id="invocation-digest",
        output_kind="candidate",
        score=1,
    )
    payload = evaluation.model_dump(mode="json")
    payload["output_digest"] = "sha256:" + "0" * 64

    with pytest.raises(ValidationError, match="output digest"):
        ReviewValueAssessment.model_validate(payload)


def test_rubric_fixtures_distinguish_added_value_from_restatement_and_hedging() -> None:
    def fixture_scores(
        scores: tuple[tuple[RubricCriterion, int], ...],
        *,
        label: str,
    ) -> tuple[RubricScore, ...]:
        scores_by_criterion = dict(scores)
        return tuple(
            RubricScore(
                criterion=criterion,
                score=scores_by_criterion[criterion],
                rationale=f"Human fixture score for {label}: {criterion.value}.",
            )
            for criterion in RubricCriterion
        )

    positive_output = _output(utility=True)
    restatement_output = _output(utility=False)
    hedging_output = AgenticReviewOutput.model_validate(
        {
            **restatement_output.model_dump(mode="python"),
            "review_summary": "More evidence may be needed before any next step.",
            "utility_contributions": [],
        }
    )
    positive = ReviewValueAssessment(
        evaluation_id="fixture-positive",
        case_id="null-spike-case",
        case_version="v1",
        invocation_id="invocation-positive",
        project_revision="fixture-revision",
        rubric_id=RUBRIC_V1.rubric_id,
        output_kind="candidate",
        output_fixture_id="positive-output",
        output_digest=review_output_digest(positive_output),
        output=positive_output,
        scores=_scores(2),
    )
    restatement = ReviewValueAssessment(
        evaluation_id="fixture-restatement",
        case_id="null-spike-case",
        case_version="v1",
        invocation_id="invocation-restatement",
        project_revision="fixture-revision",
        rubric_id=RUBRIC_V1.rubric_id,
        output_kind="baseline",
        output_fixture_id="restatement-output",
        output_digest=review_output_digest(restatement_output),
        output=restatement_output,
        scores=fixture_scores(
            tuple((criterion, 0) for criterion in RubricCriterion),
            label="restatement",
        ),
    )
    hedging_scores = fixture_scores(
        tuple(
            (
                criterion,
                0
                if criterion
                in {
                    RubricCriterion.ACTIONABILITY,
                    RubricCriterion.PRIORITIZATION,
                }
                else 1,
            )
            for criterion in RubricCriterion
        ),
        label="hedging",
    )
    hedging = ReviewValueAssessment(
        evaluation_id="fixture-hedging",
        case_id="null-spike-case",
        case_version="v1",
        invocation_id="invocation-hedging",
        project_revision="fixture-revision",
        rubric_id=RUBRIC_V1.rubric_id,
        output_kind="baseline",
        output_fixture_id="hedging-output",
        output_digest=review_output_digest(hedging_output),
        output=hedging_output,
        scores=hedging_scores,
    )

    assert positive.output.utility_contributions
    assert not restatement.output.utility_contributions
    assert not hedging.output.utility_contributions
    assert positive.total_score > restatement.total_score
    assert positive.scores[1].score > hedging.scores[1].score
    assert positive.scores[4].score > hedging.scores[4].score


def test_comparison_records_human_deltas_and_round_trips() -> None:
    comparison = _compare()

    assert comparison.status is ReviewValueComparisonStatus.COMPARED
    assert comparison.baseline_evaluation_id == "evaluation-baseline"
    assert comparison.candidate_invocation_id == "invocation-candidate"
    assert comparison.total_delta == 10
    assert [delta.delta for delta in comparison.criterion_deltas] == [2] * 5
    assert comparison.decision is HumanDecision.ACCEPT
    assert (
        ReviewValueComparisonEvidence.model_validate_json(comparison.model_dump_json())
        == comparison
    )
    assert "Add bounded context utility contribution." in (
        render_review_value_comparison_markdown(comparison)
    )


def test_comparison_evidence_preserves_evaluation_roles() -> None:
    comparison = _compare()

    assert comparison.baseline_output_kind == "baseline"
    assert comparison.candidate_output_kind == "candidate"

    payload = comparison.model_dump(mode="json")
    payload["baseline_output_kind"] = "candidate"
    with pytest.raises(ValidationError, match="baseline output role"):
        ReviewValueComparisonEvidence.model_validate(payload)


@pytest.mark.parametrize(
    ("baseline_kind", "candidate_kind"),
    [("candidate", "candidate"), ("baseline", "baseline")],
)
def test_comparison_blocks_evaluations_with_wrong_roles(
    baseline_kind: str,
    candidate_kind: str,
) -> None:
    comparison = _compare(
        baseline=_evaluation(
            evaluation_id="evaluation-baseline-role",
            invocation_id="invocation-baseline-role",
            output_kind=baseline_kind,
            score=0,
        ),
        candidate=_evaluation(
            evaluation_id="evaluation-candidate-role",
            invocation_id="invocation-candidate-role",
            output_kind=candidate_kind,
            score=2,
        ),
    )

    assert comparison.status is ReviewValueComparisonStatus.BLOCKED
    assert comparison.blocker_code == "evaluation_role_mismatch"
    assert comparison.decision is None


def test_comparison_rejects_output_digest_tampering_even_when_blocked() -> None:
    candidate = _evaluation(
        evaluation_id="evaluation-candidate-tampered",
        invocation_id="invocation-candidate-tampered",
        output_kind="candidate",
        score=2,
    ).model_copy(update={"output_digest": "sha256:" + "0" * 64})

    with pytest.raises(ValidationError, match="comparison output digest"):
        _compare(candidate=candidate)


@pytest.mark.parametrize(
    ("case_id", "case_version", "project_revision", "expected_blocker"),
    [
        ("other-case", "v1", "revision-1", "case_mismatch"),
        ("null-spike-case", "v2", "revision-1", "case_mismatch"),
        (
            "null-spike-case",
            "v1",
            "revision-2",
            "project_revision_mismatch",
        ),
    ],
)
def test_comparison_blocks_mismatched_attribution(
    case_id: str,
    case_version: str,
    project_revision: str,
    expected_blocker: str,
) -> None:
    candidate = _evaluation(
        evaluation_id="evaluation-candidate-mismatch",
        invocation_id="invocation-candidate-mismatch",
        output_kind="candidate",
        score=2,
        case_id=case_id,
        case_version=case_version,
        project_revision=project_revision,
    )

    comparison = _compare(candidate=candidate)

    assert comparison.status is ReviewValueComparisonStatus.BLOCKED
    assert comparison.blocker_code == expected_blocker
    assert comparison.decision is None


def test_comparison_blocks_different_deterministic_facts() -> None:
    candidate_output = _output(utility=True)
    changed_facts = candidate_output.deterministic_facts.model_copy(
        update={"current_null_rate": 0.88}
    )
    candidate = _evaluation(
        evaluation_id="evaluation-candidate-facts",
        invocation_id="invocation-candidate-facts",
        output_kind="candidate",
        score=2,
        output=candidate_output.model_copy(
            update={"deterministic_facts": changed_facts}
        ),
    )

    comparison = _compare(candidate=candidate)

    assert comparison.status is ReviewValueComparisonStatus.BLOCKED
    assert comparison.blocker_code == "same_case_fact_mismatch"


@pytest.mark.parametrize("tampering", ["duplicate_criterion", "wrong_total"])
def test_comparison_evidence_rejects_inconsistent_deltas(tampering: str) -> None:
    comparison = _compare()
    payload = comparison.model_dump(mode="json")
    if tampering == "duplicate_criterion":
        payload["criterion_deltas"][0]["criterion"] = payload["criterion_deltas"][1][
            "criterion"
        ]
        expected_error = "one delta per rubric criterion"
    else:
        payload["candidate_total"] -= 1
        payload["total_delta"] -= 1
        expected_error = "comparison totals must match criterion deltas"

    with pytest.raises(ValidationError, match=expected_error):
        ReviewValueComparisonEvidence.model_validate(payload)
