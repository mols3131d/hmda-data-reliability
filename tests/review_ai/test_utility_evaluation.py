"""Human-rubric utility evaluation and comparison contract tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from hmda_reliability.review_ai.evaluation import (
    RUBRIC_V1,
    HumanDecision,
    HumanUtilityEvaluation,
    RubricCriterion,
    RubricScore,
    UtilityComparisonStatus,
    UtilityControl,
    UtilityProofBundle,
    UtilityProofCase,
    compare_utility_evaluations,
    validate_quality_basis,
)
from hmda_reliability.review_ai.evaluation_store import UtilityEvidenceStore

pytestmark = pytest.mark.component


def _scores(value: int) -> list[RubricScore]:
    return [
        RubricScore(
            criterion=criterion,
            score=value,
            rationale=f"human rationale for {criterion.value}",
        )
        for criterion in RubricCriterion
    ]


def _evaluation(
    *,
    evaluation_id: str,
    invocation_id: str,
    case_id: str = "null-spike-representative",
    case_version: str = "v1",
    score: int,
    output_kind: str = "candidate",
) -> HumanUtilityEvaluation:
    return HumanUtilityEvaluation(
        evaluation_id=evaluation_id,
        case_id=case_id,
        case_version=case_version,
        invocation_id=invocation_id,
        rubric_id=RUBRIC_V1.rubric_id,
        output_kind=output_kind,
        scores=_scores(score),
    )


def test_rubric_requires_all_five_human_criteria() -> None:
    assert RUBRIC_V1.criteria == tuple(RubricCriterion)

    incomplete = _evaluation(
        evaluation_id="eval-incomplete",
        invocation_id="inv-incomplete",
        score=2,
    ).model_copy(update={"scores": _scores(2)[:-1]})
    assert not incomplete.is_complete


def test_controls_prove_positive_pass_and_negative_fail() -> None:
    positive = _evaluation(
        evaluation_id="eval-positive",
        invocation_id="inv-control-positive",
        score=2,
        output_kind="positive_control",
    )
    negative = _evaluation(
        evaluation_id="eval-negative",
        invocation_id="inv-control-negative",
        score=0,
        output_kind="negative_control",
    )
    basis = validate_quality_basis(
        [
            UtilityControl(
                control_id="control-positive",
                case_id=positive.case_id,
                case_version=positive.case_version,
                expected_outcome="pass",
                evaluation=positive,
            ),
            UtilityControl(
                control_id="control-negative",
                case_id=negative.case_id,
                case_version=negative.case_version,
                expected_outcome="fail",
                evaluation=negative,
            ),
        ]
    )

    assert basis.valid is True
    assert [result.observed_outcome for result in basis.controls] == ["pass", "fail"]


def test_comparison_records_deltas_and_human_decision() -> None:
    controls = [
        UtilityControl(
            control_id="control-positive",
            case_id="controls",
            case_version="v1",
            expected_outcome="pass",
            evaluation=_evaluation(
                evaluation_id="eval-positive",
                invocation_id="inv-control-positive",
                case_id="controls",
                score=2,
                output_kind="positive_control",
            ),
        ),
        UtilityControl(
            control_id="control-negative",
            case_id="controls",
            case_version="v1",
            expected_outcome="fail",
            evaluation=_evaluation(
                evaluation_id="eval-negative",
                invocation_id="inv-control-negative",
                case_id="controls",
                score=0,
                output_kind="negative_control",
            ),
        ),
    ]
    basis = validate_quality_basis(controls)
    baseline = _evaluation(
        evaluation_id="eval-baseline",
        invocation_id="inv-baseline",
        score=0,
        output_kind="baseline",
    )
    candidate = _evaluation(
        evaluation_id="eval-candidate",
        invocation_id="inv-candidate",
        score=2,
    )

    comparison = compare_utility_evaluations(
        comparison_id="comparison-1",
        baseline=baseline,
        candidate=candidate,
        quality_basis=basis,
        change_under_test="add bounded review context",
        decision=HumanDecision.ACCEPT,
        rationale="Candidate adds an actionable evidence gap and priority.",
    )

    assert comparison.status is UtilityComparisonStatus.COMPARED
    assert comparison.total_delta == 10
    assert comparison.criterion_deltas[0].delta == 2
    assert comparison.decision is HumanDecision.ACCEPT


def test_mismatched_case_blocks_comparison() -> None:
    basis = validate_quality_basis([])
    comparison = compare_utility_evaluations(
        comparison_id="comparison-blocked",
        baseline=_evaluation(
            evaluation_id="eval-baseline",
            invocation_id="inv-baseline",
            score=0,
        ),
        candidate=_evaluation(
            evaluation_id="eval-candidate",
            invocation_id="inv-candidate",
            case_id="other-case",
            score=2,
        ),
        quality_basis=basis,
        change_under_test="mismatched case",
        decision=HumanDecision.ACCEPT,
        rationale="Should not be accepted.",
    )

    assert comparison.status in {
        UtilityComparisonStatus.BLOCKED,
        UtilityComparisonStatus.INCONCLUSIVE,
    }
    assert comparison.decision is None
    assert comparison.blocker_code is not None


def test_comparison_store_is_create_only_and_replayable(
    tmp_path: Path,
) -> None:
    store = UtilityEvidenceStore(tmp_path)
    controls = validate_quality_basis([])
    comparison = compare_utility_evaluations(
        comparison_id="comparison-store",
        baseline=_evaluation(
            evaluation_id="eval-baseline",
            invocation_id="inv-baseline",
            score=0,
        ),
        candidate=_evaluation(
            evaluation_id="eval-candidate",
            invocation_id="inv-candidate",
            score=2,
        ),
        quality_basis=controls,
        change_under_test="store test",
        decision=HumanDecision.NO_CHANGE,
        rationale="Control basis is intentionally invalid.",
    )
    path = store.write(comparison)

    assert path == tmp_path / "agentic-review" / "utility" / "comparison-store.json"
    assert store.load(comparison.comparison_id) == comparison


def test_proof_bundle_store_preserves_case_basis_and_comparison(
    tmp_path: Path,
) -> None:
    quality_basis = validate_quality_basis([])
    comparison = compare_utility_evaluations(
        comparison_id="comparison-proof",
        baseline=_evaluation(
            evaluation_id="eval-baseline",
            invocation_id="inv-baseline",
            score=0,
        ),
        candidate=_evaluation(
            evaluation_id="eval-candidate",
            invocation_id="inv-candidate",
            score=2,
        ),
        quality_basis=quality_basis,
        change_under_test="proof bundle test",
        decision=HumanDecision.NO_CHANGE,
        rationale="Invalid quality basis remains blocked.",
    )
    bundle = UtilityProofBundle(
        proof_id="proof-1",
        case=UtilityProofCase(
            case_id=comparison.case_id,
            case_version=comparison.case_version,
            fixture_id="fixture-1",
            project_revision="test-revision",
            input_digest="sha256:" + "0" * 64,
            baseline_output_digest="sha256:" + "1" * 64,
            candidate_output_digest="sha256:" + "2" * 64,
            expected_contributions=("evidence_gap",),
        ),
        quality_basis=quality_basis,
        comparison=comparison,
    )
    store = UtilityEvidenceStore(tmp_path)

    path = store.write_proof(bundle)

    assert path == tmp_path / "agentic-review" / "utility" / "proofs" / "proof-1.json"
    assert store.load_proof("proof-1") == bundle
