"""Human-rubric utility evaluation and comparison contract tests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from hmda_reliability.review_ai import evaluation_store as store_module
from hmda_reliability.review_ai.contracts import (
    AgenticReviewFinding,
    AgenticReviewUtilityContribution,
    FindingKind,
)
from hmda_reliability.review_ai.evaluation import (
    RUBRIC_V1,
    AgenticReviewOutput,
    HumanDecision,
    HumanUtilityEvaluation,
    QualityBasisValidation,
    RubricCriterion,
    RubricScore,
    UtilityComparisonStatus,
    UtilityControl,
    UtilityControlRole,
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
    case_id: str = "controls",
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


def _hedging_output() -> AgenticReviewOutput:
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
        review_summary="A full audit of all tables may be needed.",
        evidence_used=("ev-1",),
        findings=(),
        uncertainties=("Everything is uncertain.",),
        advisory_recommendation="needs_human_review",
        utility_contributions=(),
    )


def _control(
    *,
    output_kind: str,
    score: int,
    control_id: str,
    role: UtilityControlRole | None = None,
    output: AgenticReviewOutput | None = None,
) -> UtilityControl:
    output = output or _output(output_kind)
    role = role or (
        UtilityControlRole.POSITIVE
        if output_kind == "positive_control"
        else UtilityControlRole.RESTATEMENT_NEGATIVE
    )
    fixture_id = f"utility-{control_id}-fixture"
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
        role=role,
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


def _quality_controls() -> list[UtilityControl]:
    return [
        _control(
            control_id="control-positive",
            output_kind="positive_control",
            score=2,
        ),
        _control(
            control_id="control-restatement",
            output_kind="negative_control",
            score=0,
        ),
        _control(
            control_id="control-hedging",
            output_kind="negative_control",
            score=0,
            role=UtilityControlRole.HEDGING_NEGATIVE,
            output=_hedging_output(),
        ),
    ]


def test_rubric_requires_all_five_human_criteria() -> None:
    assert RUBRIC_V1.criteria == tuple(RubricCriterion)

    incomplete = _evaluation(
        evaluation_id="eval-incomplete",
        invocation_id="inv-incomplete",
        score=2,
    ).model_copy(update={"scores": _scores(2)[:-1]})
    assert not incomplete.is_complete


def test_controls_prove_positive_pass_and_negative_fail() -> None:
    basis = validate_quality_basis(_quality_controls())

    assert basis.valid is True
    assert [result.role for result in basis.controls] == list(UtilityControlRole)
    assert [result.observed_outcome for result in basis.controls] == [
        "pass",
        "fail",
        "fail",
    ]


@pytest.mark.parametrize(
    "roles",
    [
        (
            UtilityControlRole.POSITIVE,
            UtilityControlRole.RESTATEMENT_NEGATIVE,
        ),
        (
            UtilityControlRole.POSITIVE,
            UtilityControlRole.HEDGING_NEGATIVE,
        ),
        (
            UtilityControlRole.POSITIVE,
            UtilityControlRole.RESTATEMENT_NEGATIVE,
            UtilityControlRole.RESTATEMENT_NEGATIVE,
        ),
    ],
)
def test_quality_basis_requires_each_control_role_exactly_once(
    roles: tuple[UtilityControlRole, ...],
) -> None:
    controls = []
    for index, role in enumerate(roles):
        controls.append(
            _control(
                control_id=f"control-{index}",
                role=role,
                output_kind=(
                    "positive_control"
                    if role is UtilityControlRole.POSITIVE
                    else "negative_control"
                ),
                score=2 if role is UtilityControlRole.POSITIVE else 0,
                output=(
                    _output("positive_control")
                    if role is UtilityControlRole.POSITIVE
                    else _output("negative_control")
                ),
            )
        )

    basis = validate_quality_basis(controls)

    assert basis.valid is False
    assert basis.failure_code == "controls_incomplete"


def test_control_role_requires_its_expected_outcome() -> None:
    hedging = next(
        control
        for control in _quality_controls()
        if control.role is UtilityControlRole.HEDGING_NEGATIVE
    ).model_dump()
    hedging["role"] = UtilityControlRole.POSITIVE

    with pytest.raises(ValidationError, match="semantic role"):
        UtilityControl.model_validate(hedging)


def test_comparison_records_deltas_and_human_decision() -> None:
    controls = _quality_controls()
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


@pytest.mark.parametrize(
    "tampering",
    ["duplicate_criterion", "wrong_totals"],
)
def test_compared_evidence_rejects_inconsistent_criterion_totals(
    tampering: str,
) -> None:
    comparison = compare_utility_evaluations(
        comparison_id=f"comparison-inconsistent-{tampering}",
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
        quality_basis=validate_quality_basis(_quality_controls()),
        change_under_test="inconsistent comparison totals",
        decision=HumanDecision.ACCEPT,
        rationale="Rows and totals must describe the same human scores.",
    )
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
        type(comparison).model_validate(payload)


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

    basis = validate_quality_basis([positive, negative, _quality_controls()[2]])

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
            role=UtilityControlRole.POSITIVE,
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
    controls = _quality_controls()
    basis = validate_quality_basis(controls)
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

    assert comparison.status is UtilityComparisonStatus.BLOCKED
    assert comparison.decision is None
    assert comparison.blocker_code == "case_mismatch"


def test_quality_basis_case_must_match_comparison_case() -> None:
    basis = validate_quality_basis(_quality_controls())
    baseline = _evaluation(
        evaluation_id="eval-baseline",
        invocation_id="inv-baseline",
        case_id="other-case",
        score=0,
        output_kind="baseline",
    )
    candidate = _evaluation(
        evaluation_id="eval-candidate",
        invocation_id="inv-candidate",
        case_id="other-case",
        score=2,
    )

    comparison = compare_utility_evaluations(
        comparison_id="comparison-basis-case-mismatch",
        baseline=baseline,
        candidate=candidate,
        quality_basis=basis,
        change_under_test="unrelated case",
        decision=HumanDecision.ACCEPT,
        rationale="Must not reuse controls from another case.",
    )

    assert comparison.status is UtilityComparisonStatus.BLOCKED
    assert comparison.decision is None
    assert comparison.blocker_code == "quality_basis_case_mismatch"


def test_quality_basis_digest_binds_case_identity() -> None:
    basis = validate_quality_basis(_quality_controls())

    with pytest.raises(ValidationError, match="quality basis digest"):
        QualityBasisValidation.model_validate(
            basis.model_dump() | {"case_id": "other-case"}
        )

    with pytest.raises(ValidationError, match="quality basis digest"):
        QualityBasisValidation.model_validate(
            basis.model_dump() | {"project_revision": "other-revision"}
        )


def _recompute_quality_basis_digest(payload: dict[str, object]) -> str:
    digest_payload = {
        key: payload[key]
        for key in (
            "basis_id",
            "rubric_id",
            "case_id",
            "case_version",
            "project_revision",
            "controls",
            "valid",
            "failure_code",
        )
    }
    canonical = json.dumps(
        digest_payload,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def test_quality_basis_reload_rejects_incomplete_roles_with_recomputed_digest() -> None:
    basis = validate_quality_basis(_quality_controls())
    payload = basis.model_dump(mode="json")
    payload["controls"] = payload["controls"][:-1]
    payload["basis_digest"] = _recompute_quality_basis_digest(payload)

    with pytest.raises(ValidationError, match="matching valid control results"):
        QualityBasisValidation.model_validate(payload)


def test_quality_basis_reload_rejects_tampered_control_outcome() -> None:
    basis = validate_quality_basis(_quality_controls())
    payload = basis.model_dump(mode="json")
    payload["controls"][0]["observed_outcome"] = "fail"
    payload["basis_digest"] = _recompute_quality_basis_digest(payload)

    with pytest.raises(ValidationError, match="valid control result must match"):
        QualityBasisValidation.model_validate(payload)


@pytest.mark.parametrize(
    ("control_index", "output_kind", "expected_error"),
    [
        (0, "negative_control", "valid control result must match"),
        (1, "positive_control", "valid control result must match"),
    ],
)
def test_quality_basis_reload_rejects_role_output_mismatch(
    control_index: int,
    output_kind: str,
    expected_error: str,
) -> None:
    basis = validate_quality_basis(_quality_controls())
    payload = basis.model_dump(mode="json")
    control = payload["controls"][control_index]
    replacement_output = _output(output_kind).model_dump(mode="json")
    control["output"] = replacement_output
    control["output_digest"] = utility_output_digest(
        AgenticReviewOutput.model_validate(replacement_output)
    )
    control["contribution_kinds"] = [
        kind.value
        for kind in utility_contribution_kinds(
            AgenticReviewOutput.model_validate(replacement_output)
        )
    ]
    payload["basis_digest"] = _recompute_quality_basis_digest(payload)

    with pytest.raises(ValidationError, match=expected_error):
        QualityBasisValidation.model_validate(payload)


def test_quality_basis_reload_rejects_structured_restating_control_mismatch() -> None:
    basis = validate_quality_basis(_quality_controls())
    payload = basis.model_dump(mode="json")
    control = payload["controls"][1]
    output = _output("negative_control").model_copy(
        update={
            "findings": (
                AgenticReviewFinding(
                    kind=FindingKind.OBSERVATION,
                    description="Adds a structured observation.",
                ),
            )
        }
    )
    control["output"] = output.model_dump(mode="json")
    control["output_digest"] = utility_output_digest(output)
    payload["basis_digest"] = _recompute_quality_basis_digest(payload)

    with pytest.raises(ValidationError, match="valid control result must match"):
        QualityBasisValidation.model_validate(payload)


def test_comparison_blocks_when_quality_basis_rubric_differs() -> None:
    basis = validate_quality_basis(_quality_controls()).model_copy(
        update={"rubric_id": "rubric_v2"}
    )
    comparison = compare_utility_evaluations(
        comparison_id="comparison-rubric-basis-mismatch",
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
        quality_basis=basis,
        change_under_test="rubric mismatch",
        decision=HumanDecision.ACCEPT,
        rationale="Basis and evaluations must use the same rubric.",
    )

    assert comparison.status is UtilityComparisonStatus.BLOCKED
    assert comparison.decision is None
    assert comparison.blocker_code == "quality_basis_rubric_mismatch"


def test_quality_basis_rejects_unknown_rubric_identity() -> None:
    basis = validate_quality_basis(_quality_controls())

    with pytest.raises(ValidationError):
        QualityBasisValidation.model_validate(
            basis.model_dump() | {"rubric_id": "rubric_v2"}
        )


def test_mismatched_project_revision_blocks_comparison() -> None:
    controls = _quality_controls()
    basis = validate_quality_basis(controls)
    baseline = _evaluation(
        evaluation_id="eval-baseline",
        invocation_id="inv-baseline",
        score=0,
        project_revision="revision-a",
    )
    candidate = _evaluation(
        evaluation_id="eval-candidate",
        invocation_id="inv-candidate",
        score=2,
        project_revision="revision-b",
    )

    comparison = compare_utility_evaluations(
        comparison_id="comparison-rev-mismatch",
        baseline=baseline,
        candidate=candidate,
        quality_basis=basis,
        change_under_test="mismatched project revision",
        decision=HumanDecision.ACCEPT,
        rationale="Should block on revision mismatch.",
    )

    assert comparison.status is UtilityComparisonStatus.BLOCKED
    assert comparison.decision is None
    assert comparison.blocker_code == "project_revision_mismatch"


def test_mismatched_incident_id_or_target_column_blocks_comparison() -> None:
    controls = _quality_controls()
    basis = validate_quality_basis(controls)
    baseline_output = _output("baseline")
    candidate_output = _output("candidate")

    tampered_incident_output = candidate_output.model_copy(
        update={"incident_id": "other-incident"}
    )
    comparison_incident = compare_utility_evaluations(
        comparison_id="comp-incident-mismatch",
        baseline=_evaluation(
            evaluation_id="eval-base",
            invocation_id="inv-base",
            score=0,
            output=baseline_output,
        ),
        candidate=_evaluation(
            evaluation_id="eval-cand",
            invocation_id="inv-cand",
            score=2,
            output=tampered_incident_output,
        ),
        quality_basis=basis,
        change_under_test="mismatched incident id",
        decision=HumanDecision.ACCEPT,
        rationale="Should block on incident mismatch.",
    )
    assert comparison_incident.status is UtilityComparisonStatus.BLOCKED
    assert comparison_incident.blocker_code == "same_case_fact_mismatch"

    tampered_column_output = candidate_output.model_copy(
        update={"target_column": "other_column"}
    )
    comparison_column = compare_utility_evaluations(
        comparison_id="comp-column-mismatch",
        baseline=_evaluation(
            evaluation_id="eval-base-2",
            invocation_id="inv-base-2",
            score=0,
            output=baseline_output,
        ),
        candidate=_evaluation(
            evaluation_id="eval-cand-2",
            invocation_id="inv-cand-2",
            score=2,
            output=tampered_column_output,
        ),
        quality_basis=basis,
        change_under_test="mismatched target column",
        decision=HumanDecision.ACCEPT,
        rationale="Should block on target column mismatch.",
    )
    assert comparison_column.status is UtilityComparisonStatus.BLOCKED
    assert comparison_column.blocker_code == "same_case_fact_mismatch"


def test_control_revision_and_case_mismatch_fails_quality_basis() -> None:
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

    diff_rev_neg = negative.model_copy(
        update={
            "evaluation": negative.evaluation.model_copy(
                update={"project_revision": "diff-rev"}
            )
        }
    )
    basis_rev = validate_quality_basis([positive, diff_rev_neg])
    assert basis_rev.valid is False
    assert basis_rev.failure_code == "control_revision_mismatch"

    diff_case_neg = negative.model_copy(
        update={
            "case_id": "other-case",
            "evaluation": negative.evaluation.model_copy(
                update={"case_id": "other-case"}
            ),
        }
    )
    basis_case = validate_quality_basis([positive, diff_case_neg])
    assert basis_case.valid is False
    assert basis_case.failure_code == "control_case_mismatch"


def test_mismatched_deterministic_facts_blocks_comparison() -> None:
    controls = _quality_controls()
    basis = validate_quality_basis(controls)
    baseline_output = _output("baseline")
    candidate_output = _output("candidate")
    tampered_facts = candidate_output.deterministic_facts.model_copy(
        update={"current_null_rate": 0.88}
    )
    tampered_candidate_output = candidate_output.model_copy(
        update={"deterministic_facts": tampered_facts}
    )

    baseline = _evaluation(
        evaluation_id="eval-baseline",
        invocation_id="inv-baseline",
        score=0,
        output=baseline_output,
    )
    candidate = _evaluation(
        evaluation_id="eval-candidate",
        invocation_id="inv-candidate",
        score=2,
        output=tampered_candidate_output,
    )

    comparison = compare_utility_evaluations(
        comparison_id="comparison-fact-mismatch",
        baseline=baseline,
        candidate=candidate,
        quality_basis=basis,
        change_under_test="mismatched deterministic facts",
        decision=HumanDecision.ACCEPT,
        rationale="Should block when deterministic facts differ.",
    )

    assert comparison.status is UtilityComparisonStatus.BLOCKED
    assert comparison.decision is None
    assert comparison.blocker_code == "same_case_fact_mismatch"


def test_mismatched_quality_basis_revision_blocks_comparison() -> None:
    controls = _quality_controls()
    basis = validate_quality_basis(controls)
    stale_basis = basis.model_copy(update={"project_revision": "other-revision"})

    baseline = _evaluation(
        evaluation_id="eval-baseline",
        invocation_id="inv-baseline",
        score=0,
        project_revision="test-revision",
    )
    candidate = _evaluation(
        evaluation_id="eval-candidate",
        invocation_id="inv-candidate",
        score=2,
        project_revision="test-revision",
    )

    comparison = compare_utility_evaluations(
        comparison_id="comparison-revision-mismatch",
        baseline=baseline,
        candidate=candidate,
        quality_basis=stale_basis,
        change_under_test="mismatched quality basis revision",
        decision=HumanDecision.ACCEPT,
        rationale="Should block when quality basis revision differs.",
    )

    assert comparison.status is UtilityComparisonStatus.BLOCKED
    assert comparison.decision is None
    assert comparison.blocker_code == "quality_basis_revision_mismatch"


def test_hedging_negative_control_discrimination() -> None:
    hedging_output = AgenticReviewOutput(
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
            "Multiple factors could be involved; full audit of all tables required."
        ),
        evidence_used=("ev-1",),
        findings=(),
        uncertainties=("Everything is uncertain and unconfirmed.",),
        advisory_recommendation="needs_human_review",
        utility_contributions=(),
    )

    # 1. Actionability/prioritization = 0점으로 탈락(FAIL) 판정을 내린
    # 정상적인 negative control 평가 구성
    hedging_scores = [
        RubricScore(
            criterion=RubricCriterion.ADDED_VALUE,
            score=1,
            rationale="Adds minimal context.",
        ),
        RubricScore(
            criterion=RubricCriterion.ACTIONABILITY,
            score=0,
            rationale="Over-defensive hedging with no specific action.",
        ),
        RubricScore(
            criterion=RubricCriterion.EVIDENCE_AWARENESS,
            score=1,
            rationale="Aware of evidence.",
        ),
        RubricScore(
            criterion=RubricCriterion.UNCERTAINTY_HANDLING,
            score=1,
            rationale="Mentions uncertainty.",
        ),
        RubricScore(
            criterion=RubricCriterion.PRIORITIZATION,
            score=0,
            rationale="Fails to prioritize any single investigation step.",
        ),
    ]
    valid_hedging_eval = HumanUtilityEvaluation(
        evaluation_id="eval-hedging-fail",
        case_id="controls",
        case_version="v1",
        invocation_id="inv-hedging",
        project_revision="test-revision",
        rubric_id=RUBRIC_V1.rubric_id,
        output_kind="negative_control",
        output_fixture_id="utility-hedging-fixture",
        output_digest=utility_output_digest(hedging_output),
        contribution_kinds=(),
        output=hedging_output,
        scores=tuple(hedging_scores),
    )

    assert valid_hedging_eval.passed() is False

    hedging_control = UtilityControl(
        control_id="control-hedging",
        role=UtilityControlRole.HEDGING_NEGATIVE,
        case_id="controls",
        case_version="v1",
        expected_outcome="fail",
        output_fixture_id="utility-hedging-fixture",
        output=hedging_output,
        expected_incident_id=hedging_output.incident_id,
        expected_target_column=hedging_output.target_column,
        expected_deterministic_facts=hedging_output.deterministic_facts,
        expected_contributions=(),
        evaluation=valid_hedging_eval,
    )

    positive_control = _control(
        control_id="control-positive",
        output_kind="positive_control",
        score=2,
    )

    restatement_control = _control(
        control_id="control-restatement",
        output_kind="negative_control",
        score=0,
    )
    basis = validate_quality_basis(
        [positive_control, restatement_control, hedging_control]
    )
    assert basis.valid is True
    assert [result.observed_outcome for result in basis.controls] == [
        "pass",
        "fail",
        "fail",
    ]

    # 2. 반대로 면책형 답변에 잘못 통과 점수(2점)를 주어
    # negative control로 등록하려 하면 유효성 검사에서 차단
    passing_eval = valid_hedging_eval.model_copy(update={"scores": tuple(_scores(2))})
    with pytest.raises(ValidationError, match="negative control must not pass"):
        UtilityControl(
            control_id="control-hedging-pass",
            role=UtilityControlRole.HEDGING_NEGATIVE,
            case_id="controls",
            case_version="v1",
            expected_outcome="fail",
            output_fixture_id="utility-hedging-fixture",
            output=hedging_output,
            expected_incident_id=hedging_output.incident_id,
            expected_target_column=hedging_output.target_column,
            expected_deterministic_facts=hedging_output.deterministic_facts,
            expected_contributions=(),
            evaluation=passing_eval,
        )


def test_hedging_negative_requires_zero_actionability_or_prioritization() -> None:
    control = _control(
        control_id="control-hedging-nonzero-key-criteria",
        output_kind="negative_control",
        score=0,
        role=UtilityControlRole.HEDGING_NEGATIVE,
        output=_hedging_output(),
    )
    scores = tuple(
        score.model_copy(
            update={
                "score": (
                    1
                    if score.criterion
                    in {
                        RubricCriterion.ACTIONABILITY,
                        RubricCriterion.PRIORITIZATION,
                    }
                    else 0
                )
            }
        )
        for score in control.evaluation.scores
    )
    evaluation = control.evaluation.model_copy(update={"scores": scores})

    with pytest.raises(ValidationError, match="actionability or prioritization"):
        UtilityControl.model_validate(
            control.model_dump() | {"evaluation": evaluation.model_dump()}
        )


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


def test_comparison_store_rejects_inconsistent_instance_before_writing(
    tmp_path: Path,
) -> None:
    comparison = compare_utility_evaluations(
        comparison_id="comparison-invalid-instance",
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
        quality_basis=validate_quality_basis(_quality_controls()),
        change_under_test="invalid comparison instance",
        decision=HumanDecision.ACCEPT,
        rationale="The store must validate evidence before persistence.",
    )
    invalid_comparison = comparison.model_copy(
        update={
            "candidate_total": comparison.candidate_total - 1,
            "total_delta": comparison.total_delta - 1,
        }
    )
    store = UtilityEvidenceStore(tmp_path)

    with pytest.raises(ValidationError, match="comparison totals must match"):
        store.write(invalid_comparison)

    assert not store.path_for(comparison.comparison_id).exists()


def test_proof_bundle_store_preserves_case_basis_and_comparison(
    tmp_path: Path,
) -> None:
    quality_basis = validate_quality_basis(_quality_controls())
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
        rationale="The complete three-role basis supports this comparison.",
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
    reloaded = store.load_proof("proof-1")
    assert reloaded == bundle
    assert reloaded.quality_basis.valid is True
    assert reloaded.quality_basis.case_id == comparison.case_id
    assert reloaded.quality_basis.case_version == comparison.case_version
    assert reloaded.quality_basis.project_revision == comparison.project_revision
    assert reloaded.quality_basis.basis_digest == quality_basis.basis_digest
    assert reloaded.comparison.quality_basis_digest == quality_basis.basis_digest
    assert [item.role for item in reloaded.quality_basis.controls] == list(
        UtilityControlRole
    )
    assert [item.observed_outcome for item in reloaded.quality_basis.controls] == [
        "pass",
        "fail",
        "fail",
    ]


def test_proof_bundle_rejects_quality_basis_from_another_case() -> None:
    quality_basis = validate_quality_basis(_quality_controls())
    comparison = compare_utility_evaluations(
        comparison_id="comparison-proof-case-mismatch",
        baseline=_evaluation(
            evaluation_id="eval-baseline",
            invocation_id="inv-baseline",
            case_id="other-case",
            score=0,
            output_kind="baseline",
        ),
        candidate=_evaluation(
            evaluation_id="eval-candidate",
            invocation_id="inv-candidate",
            case_id="other-case",
            score=2,
        ),
        quality_basis=quality_basis,
        change_under_test="proof case mismatch",
        decision=HumanDecision.ACCEPT,
        rationale="The basis belongs to another case.",
    )

    assert comparison.status is UtilityComparisonStatus.BLOCKED
    with pytest.raises(ValidationError, match="case identity must match"):
        UtilityProofBundle(
            proof_id="proof-case-mismatch",
            case=UtilityProofCase(
                case_id=comparison.case_id,
                case_version=comparison.case_version,
                fixture_id="fixture-1",
                project_revision=comparison.project_revision,
                input_digest="sha256:" + "0" * 64,
                baseline_output_digest=comparison.baseline_output_digest,
                candidate_output_digest=comparison.candidate_output_digest,
                expected_contributions=comparison.candidate_contribution_kinds,
            ),
            quality_basis=quality_basis,
            comparison=comparison,
        )


def test_proof_bundle_rejects_invalid_quality_basis_for_compared_result() -> None:
    quality_basis = validate_quality_basis(_quality_controls())
    invalid_basis = validate_quality_basis(_quality_controls()[:-1])
    comparison = compare_utility_evaluations(
        comparison_id="comparison-invalid-basis",
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
        change_under_test="invalid proof basis",
        decision=HumanDecision.ACCEPT,
        rationale="A compared result cannot be detached from valid controls.",
    )

    with pytest.raises(ValidationError, match="requires a valid quality basis"):
        UtilityProofBundle.model_validate(
            {
                "proof_id": "proof-invalid-basis",
                "case": UtilityProofCase(
                    case_id=comparison.case_id,
                    case_version=comparison.case_version,
                    fixture_id="fixture-invalid-basis",
                    project_revision=comparison.project_revision,
                    input_digest="sha256:" + "0" * 64,
                    baseline_output_digest=comparison.baseline_output_digest,
                    candidate_output_digest=comparison.candidate_output_digest,
                    expected_contributions=(comparison.candidate_contribution_kinds),
                ).model_dump(mode="json"),
                "quality_basis": invalid_basis.model_dump(mode="json"),
                "comparison": comparison.model_dump(mode="json")
                | {"quality_basis_digest": invalid_basis.basis_digest},
            }
        )


def test_proof_store_rejects_unsafe_proof_identity(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        UtilityEvidenceStore(tmp_path).load_proof("../escape")


def test_proof_store_rejects_invalid_basis_instance_before_writing(
    tmp_path: Path,
) -> None:
    quality_basis = validate_quality_basis(_quality_controls())
    comparison = compare_utility_evaluations(
        comparison_id="comparison-invalid-basis-instance",
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
        change_under_test="invalid basis instance",
        decision=HumanDecision.ACCEPT,
        rationale="The store must validate the proof before persistence.",
    )
    bundle = UtilityProofBundle(
        proof_id="proof-invalid-basis-instance",
        case=UtilityProofCase(
            case_id=comparison.case_id,
            case_version=comparison.case_version,
            fixture_id="fixture-invalid-basis-instance",
            project_revision=comparison.project_revision,
            input_digest="sha256:" + "0" * 64,
            baseline_output_digest=comparison.baseline_output_digest,
            candidate_output_digest=comparison.candidate_output_digest,
            expected_contributions=comparison.candidate_contribution_kinds,
        ),
        quality_basis=quality_basis,
        comparison=comparison,
    )
    invalid_basis = validate_quality_basis(_quality_controls()[:-1]).model_copy(
        update={"valid": True}
    )
    invalid_bundle = bundle.model_copy(
        update={
            "quality_basis": invalid_basis,
            "comparison": comparison.model_copy(
                update={"quality_basis_digest": invalid_basis.basis_digest}
            ),
        }
    )
    store = UtilityEvidenceStore(tmp_path)

    with pytest.raises(ValidationError, match="quality basis digest"):
        store.write_proof(invalid_bundle)

    assert not store.path_for_proof(invalid_bundle.proof_id).exists()


def test_proof_store_rolls_back_final_link_when_directory_fsync_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    quality_basis = validate_quality_basis(_quality_controls())
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


def test_proof_bundle_rejects_invalid_quality_basis_for_blocked_result() -> None:
    quality_basis = validate_quality_basis([])
    comparison = compare_utility_evaluations(
        comparison_id="comparison-proof-invalid-basis",
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
        change_under_test="invalid blocked proof basis",
        decision=HumanDecision.NO_CHANGE,
        rationale="Blocked evidence does not make an incomplete basis durable proof.",
    )

    with pytest.raises(ValidationError, match="proof bundle requires a valid"):
        UtilityProofBundle(
            proof_id="proof-blocked-invalid-basis",
            case=UtilityProofCase(
                case_id=comparison.case_id,
                case_version=comparison.case_version,
                fixture_id="fixture-invalid-basis",
                project_revision=comparison.project_revision,
                input_digest="sha256:" + "0" * 64,
                baseline_output_digest=comparison.baseline_output_digest,
                candidate_output_digest=comparison.candidate_output_digest,
                expected_contributions=comparison.candidate_contribution_kinds,
            ),
            quality_basis=quality_basis,
            comparison=comparison,
        )
