"""Human-rubric utility evaluation and comparison contract tests."""

from __future__ import annotations

import json
from importlib import import_module
from pathlib import Path

import pytest
from pydantic import ValidationError

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
from hmda_reliability.review_ai.staged.contracts import (
    STAGE_IDS,
    StageAnswer,
    StagedReviewOutput,
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


def _output(*, utility: bool = False) -> StagedReviewOutput:
    texts = (
        (
            "계보 근거가 없어 원인을 확정할 수 없다.",
            "초안의 원천 점검으로 결측 증가 위치를 먼저 확인한다.",
            "원천에도 증가했다면 수집 경로를, 아니라면 변환 경로를 우선 조사한다.",
        )
        if utility
        else (
            "결측률은 1%에서 21%로 증가했다.",
            "초안은 원천 점검을 권고한다.",
            "원인은 아직 확인되지 않았다.",
        )
    )
    return StagedReviewOutput(
        incident_id="incident-1",
        incident_type="null_spike",
        target_column="income",
        deterministic_facts={
            "baseline_null_rate": 0.01,
            "current_null_rate": 0.21,
            "delta": 0.2,
            "threshold": 0.1,
        },
        stages=tuple(
            StageAnswer(stage_id=stage_id, text=text)
            for stage_id, text in zip(STAGE_IDS, texts, strict=True)
        ),
    )


def _evaluation(
    *,
    evaluation_id: str,
    workflow_id: str,
    output_kind: str,
    score: int,
    case_id: str = "null-spike-case",
    case_version: str = "v1",
    project_revision: str = "revision-1",
    output: StagedReviewOutput | None = None,
) -> ReviewValueAssessment:
    output = output or _output(utility=output_kind == "candidate")
    return ReviewValueAssessment(
        evaluation_id=evaluation_id,
        case_id=case_id,
        case_version=case_version,
        workflow_id=workflow_id,
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
            workflow_id="workflow-baseline",
            output_kind="baseline",
            score=0,
        ),
        candidate=candidate
        or _evaluation(
            evaluation_id="evaluation-candidate",
            workflow_id="workflow-candidate",
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
def test_comparison_json_matches_independent_current_golden(
    decision: str, case_version: str, golden_key: str
) -> None:
    """운영 serializer로 생성하지 않은 정적 current JSON과 전체 shape를 대조한다."""
    fixture = Path(__file__).with_name("fixtures") / "utility_comparison_staged_v1.json"
    expected = json.loads(fixture.read_text(encoding="utf-8"))[golden_key]
    if golden_key == "compared":
        expected["decision"] = decision

    candidate = _evaluation(
        evaluation_id="evaluation-candidate",
        workflow_id="workflow-candidate",
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
        workflow_id="workflow-complete",
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
        workflow_id="workflow-digest",
        output_kind="candidate",
        score=1,
    )
    payload = evaluation.model_dump(mode="json")
    payload["output_digest"] = "sha256:" + "0" * 64

    with pytest.raises(ValidationError, match="output digest"):
        ReviewValueAssessment.model_validate(payload)


@pytest.mark.parametrize("suffix", [" ", "\n", "추가 설명😀"])
def test_evaluation_rejects_stage_text_mutation_without_a_new_digest(
    suffix: str,
) -> None:
    payload = _evaluation(
        evaluation_id="evaluation-exact-text",
        workflow_id="workflow-exact-text",
        output_kind="candidate",
        score=1,
    ).model_dump(mode="json")
    payload["output"]["stages"][1]["text"] += suffix

    with pytest.raises(ValidationError, match="output digest"):
        ReviewValueAssessment.model_validate(payload)


def test_current_evaluation_rejects_removed_invocation_alias() -> None:
    payload = _evaluation(
        evaluation_id="evaluation-workflow",
        workflow_id="workflow-current",
        output_kind="candidate",
        score=1,
    ).model_dump(mode="json")
    payload["invocation_id"] = payload.pop("workflow_id")

    with pytest.raises(ValidationError):
        ReviewValueAssessment.model_validate(payload)


def test_output_digest_covers_stage_order_without_normalizing_text() -> None:
    output = _output(utility=True)
    reversed_output = output.model_copy(
        update={"stages": tuple(reversed(output.stages))}
    )

    assert review_output_digest(output) != review_output_digest(reversed_output)


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
    hedging_output = StagedReviewOutput.model_validate(
        {
            **restatement_output.model_dump(mode="python"),
            "stages": [
                {"stage_id": "evidence_review", "text": "근거가 더 필요할 수 있다."},
                {"stage_id": "draft_critique", "text": "초안을 더 검토할 수 있다."},
                {"stage_id": "synthesis", "text": "결정 전에 확인이 필요할 수 있다."},
            ],
        }
    )
    positive = ReviewValueAssessment(
        evaluation_id="fixture-positive",
        case_id="null-spike-case",
        case_version="v1",
        workflow_id="workflow-positive",
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
        workflow_id="workflow-restatement",
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
        workflow_id="workflow-hedging",
        project_revision="fixture-revision",
        rubric_id=RUBRIC_V1.rubric_id,
        output_kind="baseline",
        output_fixture_id="hedging-output",
        output_digest=review_output_digest(hedging_output),
        output=hedging_output,
        scores=hedging_scores,
    )

    assert positive.output.stages[2].text.startswith("원천에도 증가했다면")
    assert restatement.output.stages[2].text == "원인은 아직 확인되지 않았다."
    assert hedging.output.stages[2].text == "결정 전에 확인이 필요할 수 있다."
    assert positive.total_score > restatement.total_score
    assert positive.scores[1].score > hedging.scores[1].score
    assert positive.scores[4].score > hedging.scores[4].score


def test_comparison_records_human_deltas_and_round_trips() -> None:
    comparison = _compare()

    assert comparison.status is ReviewValueComparisonStatus.COMPARED
    assert comparison.baseline_evaluation_id == "evaluation-baseline"
    assert comparison.candidate_workflow_id == "workflow-candidate"
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


def test_comparison_attributes_heterogeneous_scores_to_each_criterion() -> None:
    evaluations = []
    for role, values in (
        ("baseline", (0, 1, 2, 0, 1)),
        ("candidate", (2, 0, 1, 1, 2)),
    ):
        payload = _evaluation(
            evaluation_id=f"evaluation-{role}",
            workflow_id=f"workflow-{role}",
            output_kind=role,
            score=0,
        ).model_dump(mode="python")
        payload["scores"] = tuple(
            RubricScore(criterion=criterion, score=value, rationale="Fixture score.")
            for criterion, value in zip(RubricCriterion, values, strict=True)
        )
        evaluations.append(ReviewValueAssessment.model_validate(payload))

    comparison = _compare(baseline=evaluations[0], candidate=evaluations[1])

    assert comparison.status is ReviewValueComparisonStatus.COMPARED
    assert (
        comparison.baseline_total,
        comparison.candidate_total,
        comparison.total_delta,
    ) == (4, 6, 2)
    assert [
        (item.criterion.value, item.baseline_score, item.candidate_score, item.delta)
        for item in comparison.criterion_deltas
    ] == [
        ("added_value", 0, 2, 2),
        ("actionability", 1, 0, -1),
        ("evidence_awareness", 2, 1, -1),
        ("uncertainty_handling", 0, 1, 1),
        ("prioritization", 1, 2, 1),
    ]


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
            workflow_id="workflow-baseline-role",
            output_kind=baseline_kind,
            score=0,
        ),
        candidate=_evaluation(
            evaluation_id="evaluation-candidate-role",
            workflow_id="workflow-candidate-role",
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
        workflow_id="workflow-candidate-tampered",
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
        workflow_id="workflow-candidate-mismatch",
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
        workflow_id="workflow-candidate-facts",
        output_kind="candidate",
        score=2,
        output=candidate_output.model_copy(
            update={"deterministic_facts": changed_facts}
        ),
    )

    comparison = _compare(candidate=candidate)

    assert comparison.status is ReviewValueComparisonStatus.BLOCKED
    assert comparison.blocker_code == "same_case_fact_mismatch"


def test_comparison_blocks_conflicting_outputs_for_one_workflow() -> None:
    baseline = _evaluation(
        evaluation_id="evaluation-baseline-workflow-conflict",
        workflow_id="workflow-shared",
        output_kind="baseline",
        score=0,
    )
    candidate = _evaluation(
        evaluation_id="evaluation-candidate-workflow-conflict",
        workflow_id="workflow-shared",
        output_kind="candidate",
        score=2,
    )

    comparison = _compare(baseline=baseline, candidate=candidate)

    assert comparison.status is ReviewValueComparisonStatus.BLOCKED
    assert comparison.blocker_code == "workflow_output_conflict"
    assert comparison.decision is None


def test_compared_contract_rejects_conflicting_outputs_for_one_workflow() -> None:
    payload = _compare().model_dump(mode="json")
    payload["candidate_workflow_id"] = payload["baseline_workflow_id"]

    with pytest.raises(ValidationError, match="one workflow"):
        ReviewValueComparisonEvidence.model_validate(payload)


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
