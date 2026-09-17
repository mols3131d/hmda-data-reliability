"""Human-rubric utility evaluation and comparison contract tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from hmda_reliability.review_ai import evaluation_store as store_module
from hmda_reliability.review_ai.contracts import AgenticReviewUtilityContribution
from hmda_reliability.review_ai.evaluation import (
    RUBRIC_V1,
    AgenticReviewOutput,
    HumanDecision,
    HumanUtilityEvaluation,
    RubricCriterion,
    RubricScore,
    UtilityComparisonStatus,
    UtilityControl,
    UtilityProofBundle,
    UtilityProofCase,
    compare_utility_evaluations,
    utility_contribution_kinds,
    utility_output_digest,
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
    project_revision: str = "test-revision",
    output_fixture_id: str | None = None,
    output: AgenticReviewOutput | None = None,
) -> HumanUtilityEvaluation:
    output = output or _output(output_kind)
    fixture_id = output_fixture_id or f"utility-{output_kind}-fixture"
    return HumanUtilityEvaluation(
        evaluation_id=evaluation_id,
        case_id=case_id,
        case_version=case_version,
        invocation_id=invocation_id,
        project_revision=project_revision,
        rubric_id=RUBRIC_V1.rubric_id,
        output_kind=output_kind,
        output_fixture_id=fixture_id,
        output_digest=utility_output_digest(output),
        contribution_kinds=utility_contribution_kinds(output),
        output=output,
        scores=_scores(score),
    )


def _output(output_kind: str) -> AgenticReviewOutput:
    contributions = ()
    if output_kind in {"positive_control", "candidate"}:
        contributions = (
            AgenticReviewUtilityContribution(
                kind="evidence_gap",
                description="Lineage evidence remains unconfirmed.",
                evidence_refs=("ev-1",),
            ),
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
            "The output adds a bounded utility contribution."
            if contributions
            else "The output restates the deterministic facts."
        ),
        evidence_used=("ev-1",),
        findings=(),
        uncertainties=("Root cause remains unconfirmed.",),
        advisory_recommendation="needs_human_review",
        utility_contributions=contributions,
    )


def _control(*, output_kind: str, score: int, control_id: str) -> UtilityControl:
    output = _output(output_kind)
    fixture_id = f"utility-{output_kind}-fixture"
    evaluation = _evaluation(
        evaluation_id=f"eval-{control_id}",
        invocation_id=f"inv-{control_id}",
        case_id="controls",
        score=score,
        output_kind=output_kind,
        output_fixture_id=fixture_id,
        output=output,
    )
    return UtilityControl(
        control_id=control_id,
        case_id="controls",
        case_version="v1",
        expected_outcome="pass" if output_kind == "positive_control" else "fail",
        output_fixture_id=fixture_id,
        output=output,
        expected_incident_id=output.incident_id,
        expected_target_column=output.target_column,
        expected_deterministic_facts=output.deterministic_facts,
        expected_contributions=utility_contribution_kinds(output),
        evaluation=evaluation,
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
    basis = validate_quality_basis(
        [
            _control(
                control_id="control-positive",
                output_kind="positive_control",
                score=2,
            ),
            _control(
                control_id="control-negative",
                output_kind="negative_control",
                score=0,
            ),
        ]
    )

    assert basis.valid is True
    assert [result.observed_outcome for result in basis.controls] == ["pass", "fail"]


def test_comparison_records_deltas_and_human_decision() -> None:
    controls = [
        _control(
            control_id="control-positive",
            output_kind="positive_control",
            score=2,
        ),
        _control(
            control_id="control-negative",
            output_kind="negative_control",
            score=0,
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
    assert comparison.project_revision == "test-revision"


def test_incomplete_negative_control_cannot_make_quality_basis_valid() -> None:
    positive = _control(
        control_id="control-positive",
        output_kind="positive_control",
        score=2,
    )
    negative = _control(
        control_id="control-negative",
        output_kind="negative_control",
        score=0,
    )
    incomplete_evaluation = negative.evaluation.model_copy(
        update={"scores": tuple(_scores(0)[:-1])}
    )
    negative = negative.model_copy(update={"evaluation": incomplete_evaluation})

    basis = validate_quality_basis([positive, negative])

    assert basis.valid is False
    assert basis.failure_code == "control_incomplete"


def test_control_rejects_evaluation_that_is_not_bound_to_actual_output() -> None:
    output = _output("positive_control")
    evaluation = _evaluation(
        evaluation_id="eval-positive",
        invocation_id="inv-positive",
        output_kind="positive_control",
        score=2,
        output=output,
    ).model_copy(update={"output_digest": "sha256:" + "0" * 64})

    with pytest.raises(ValidationError):
        UtilityControl(
            control_id="control-positive",
            case_id="controls",
            case_version="v1",
            expected_outcome="pass",
            output_fixture_id="utility-positive_control-fixture",
            output=output,
            expected_incident_id=output.incident_id,
            expected_target_column=output.target_column,
            expected_deterministic_facts=output.deterministic_facts,
            expected_contributions=utility_contribution_kinds(output),
            evaluation=evaluation,
        )


def test_negative_control_rejects_output_that_changes_deterministic_facts() -> None:
    control = _control(
        control_id="control-negative",
        output_kind="negative_control",
        score=0,
    )
    wrong_facts = control.output.deterministic_facts.model_copy(
        update={"current_null_rate": 0.99}
    )
    wrong_output = control.output.model_copy(
        update={"deterministic_facts": wrong_facts}
    )
    tampered_control = control.model_copy(update={"output": wrong_output})

    basis = validate_quality_basis(
        [
            tampered_control,
            _control(
                control_id="control-positive",
                output_kind="positive_control",
                score=2,
            ),
        ]
    )

    assert basis.valid is False
    assert basis.failure_code == "control_mismatch"


def test_comparison_rejects_a_digest_tampered_after_evaluation_creation() -> None:
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
        output_kind="candidate",
    )
    tampered_candidate = candidate.model_copy(
        update={"output_digest": "sha256:" + "0" * 64}
    )

    with pytest.raises(ValidationError):
        compare_utility_evaluations(
            comparison_id="comparison-tampered",
            baseline=baseline,
            candidate=tampered_candidate,
            quality_basis=validate_quality_basis([]),
            change_under_test="tampered output",
            decision=HumanDecision.ACCEPT,
            rationale="Must not become a valid comparison.",
        )


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
            baseline_output_digest=comparison.baseline_output_digest,
            candidate_output_digest=comparison.candidate_output_digest,
            expected_contributions=comparison.candidate_contribution_kinds,
        ),
        quality_basis=quality_basis,
        comparison=comparison,
    )
    store = UtilityEvidenceStore(tmp_path)

    path = store.write_proof(bundle)

    assert path == tmp_path / "agentic-review" / "utility" / "proofs" / "proof-1.json"
    assert store.load_proof("proof-1") == bundle


def test_proof_store_rejects_unsafe_proof_identity(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        UtilityEvidenceStore(tmp_path).load_proof("../escape")


def test_proof_store_rolls_back_final_link_when_directory_fsync_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    quality_basis = validate_quality_basis([])
    comparison = compare_utility_evaluations(
        comparison_id="comparison-fsync",
        baseline=_evaluation(
            evaluation_id="eval-baseline",
            invocation_id="inv-baseline",
            score=0,
            output_kind="baseline",
        ),
        candidate=_evaluation(
            evaluation_id="eval-candidate",
            invocation_id="inv-candidate",
            score=2,
            output_kind="candidate",
        ),
        quality_basis=quality_basis,
        change_under_test="fsync failure",
        decision=HumanDecision.NO_CHANGE,
        rationale="Invalid quality basis remains blocked.",
    )
    bundle = UtilityProofBundle(
        proof_id="proof-fsync",
        case=UtilityProofCase(
            case_id=comparison.case_id,
            case_version=comparison.case_version,
            fixture_id="fixture-fsync",
            project_revision=comparison.project_revision,
            input_digest="sha256:" + "0" * 64,
            baseline_output_digest=comparison.baseline_output_digest,
            candidate_output_digest=comparison.candidate_output_digest,
            expected_contributions=comparison.candidate_contribution_kinds,
        ),
        quality_basis=quality_basis,
        comparison=comparison,
    )
    store = UtilityEvidenceStore(tmp_path)

    def fail_fsync(_: Path) -> None:
        raise OSError("simulated")

    monkeypatch.setattr(store_module, "_fsync_directory", fail_fsync)

    with pytest.raises(store_module.UtilityEvidenceStoreError):
        store.write_proof(bundle)

    assert not store.path_for_proof(bundle.proof_id).exists()
