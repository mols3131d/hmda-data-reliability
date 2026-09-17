"""Run the offline Review AI MVP utility proof fixture."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from hmda_reliability.reliability import (
    DetectionRequest,
    Evidence,
    EvidenceSource,
    FreshnessMeasurementStatus,
    ProfileSnapshot,
    RemediationDraftRequest,
    create_remediation_draft,
    detect_basic_incidents,
)
from hmda_reliability.review_ai import (
    RUBRIC_V1,
    AgenticReviewInput,
    AgenticReviewOutput,
    AgenticReviewUtilityContribution,
    HumanDecision,
    HumanUtilityEvaluation,
    UtilityControl,
    UtilityProofBundle,
    UtilityProofCase,
    build_bounded_review_context,
    compare_utility_evaluations,
    validate_quality_basis,
)
from hmda_reliability.review_ai.evaluation import RubricCriterion, RubricScore
from hmda_reliability.review_ai.evaluation_store import UtilityEvidenceStore
from hmda_reliability.review_ai.prompt import canonical_json_bytes

CASE_ID = "review-ai-null-spike-utility"
CASE_VERSION = "v1"
FIXTURE_ID = "review-ai-null-spike-utility-v1"


def build_representative_utility_proof(
    *,
    project_revision: str = "utility-proof-fixture-revision",
) -> UtilityProofBundle:
    """Build the deterministic case, controls and human comparison evidence."""

    review_input = _build_review_input()
    context = build_bounded_review_context(review_input)
    baseline_output = _build_output(review_input, utility_contributions=())
    candidate_output = _build_output(
        review_input,
        utility_contributions=(
            AgenticReviewUtilityContribution(
                kind="evidence_gap",
                description=(
                    "Lineage evidence is missing before root-cause attribution."
                ),
                evidence_refs=(review_input.evidence[0].evidence_id,),
            ),
            AgenticReviewUtilityContribution(
                kind="investigation_priority",
                description="First verify the source extraction for income.",
                evidence_refs=("ev-table-metadata",),
                priority="high",
            ),
            AgenticReviewUtilityContribution(
                kind="remediation_critique",
                description="The draft needs validation evidence before recovery.",
                evidence_refs=("ev-dbt-validation",),
            ),
            AgenticReviewUtilityContribution(
                kind="material_uncertainty",
                description="The supplied profile does not establish root cause.",
                evidence_refs=(review_input.evidence[0].evidence_id,),
            ),
        ),
    )
    controls = validate_quality_basis(
        [
            UtilityControl(
                control_id="control-positive",
                case_id="review-ai-utility-controls",
                case_version=CASE_VERSION,
                expected_outcome="pass",
                evaluation=_evaluation(
                    evaluation_id="eval-control-positive",
                    invocation_id="utility-control-positive",
                    case_id="review-ai-utility-controls",
                    output_kind="positive_control",
                    score=2,
                ),
            ),
            UtilityControl(
                control_id="control-negative",
                case_id="review-ai-utility-controls",
                case_version=CASE_VERSION,
                expected_outcome="fail",
                evaluation=_evaluation(
                    evaluation_id="eval-control-negative",
                    invocation_id="utility-control-negative",
                    case_id="review-ai-utility-controls",
                    output_kind="negative_control",
                    score=0,
                ),
            ),
        ]
    )
    baseline = _evaluation(
        evaluation_id="eval-baseline",
        invocation_id="utility-baseline",
        output_kind="baseline",
        score=0,
    )
    candidate = _evaluation(
        evaluation_id="eval-candidate",
        invocation_id="utility-candidate",
        output_kind="candidate",
        score=2,
    )
    comparison = compare_utility_evaluations(
        comparison_id="comparison-review-ai-utility-v1",
        baseline=baseline,
        candidate=candidate,
        quality_basis=controls,
        change_under_test="add bounded context and structured utility contributions",
        decision=HumanDecision.ACCEPT,
        rationale=(
            "Candidate adds evidence-gap, priority, critique and uncertainty signals "
            "that improve the next human review step."
        ),
    )
    case = UtilityProofCase(
        case_id=CASE_ID,
        case_version=CASE_VERSION,
        fixture_id=FIXTURE_ID,
        project_revision=project_revision,
        input_digest=context.digest,
        baseline_output_digest=_output_digest(baseline_output),
        candidate_output_digest=_output_digest(candidate_output),
        expected_contributions=(
            "evidence_gap",
            "investigation_priority",
            "remediation_critique",
            "material_uncertainty",
        ),
    )
    return UtilityProofBundle(
        proof_id="review-ai-utility-proof-v1",
        case=case,
        quality_basis=controls,
        comparison=comparison,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact-root",
        type=Path,
        default=Path(".local/artifacts"),
        help="root for create-only utility proof evidence",
    )
    args = parser.parse_args(argv)
    bundle = build_representative_utility_proof(project_revision=_current_revision())
    store = UtilityEvidenceStore(args.artifact_root)
    path = store.write_proof(bundle)
    print(f"Utility proof evidence: {path}")
    print()
    from hmda_reliability.review_ai.evaluation import render_utility_comparison_markdown

    print(render_utility_comparison_markdown(bundle.comparison))
    return 0


def _build_review_input() -> AgenticReviewInput:
    observed_at = datetime(2026, 8, 27, 0, 0, tzinfo=UTC)
    baseline = ProfileSnapshot(
        snapshot_id="utility-baseline-2025",
        asset_name="raw.hmda_loans",
        partition="2025",
        observed_at=observed_at,
        row_count=100,
        null_rates={"income": 0.01},
        schema_hash="sha256:utility-fixture",
        freshness_at=None,
        freshness_status=FreshnessMeasurementStatus.UNAVAILABLE,
    )
    current = baseline.model_copy(
        update={
            "snapshot_id": "utility-current-2025",
            "null_rates": {"income": 0.21},
        }
    )
    detection = detect_basic_incidents(
        DetectionRequest(baseline=baseline, current=current)
    )[0]
    surrounding = [
        detection.evidence,
        Evidence(
            evidence_id="ev-table-metadata",
            source=EvidenceSource.TABLE_METADATA,
            asset_name="raw.hmda_loans",
            partition="2025",
            observed_at=observed_at,
            summary="Table metadata for the affected partition",
            payload={
                "table_name": "raw.hmda_loans",
                "columns": ["income", "loan_amount"],
                "schema_hash": "sha256:utility-fixture",
            },
        ),
        Evidence(
            evidence_id="ev-dbt-validation",
            source=EvidenceSource.DBT_ARTIFACT,
            asset_name="raw.hmda_loans",
            partition="2025",
            observed_at=observed_at,
            summary="The income not-null validation failed",
            payload={"test_name": "not_null_income", "status": "fail"},
        ),
    ]
    evidence_refs = [item.evidence_id for item in surrounding]
    incident = detection.incident.model_copy(update={"evidence_refs": evidence_refs})
    draft = create_remediation_draft(
        RemediationDraftRequest(incident=incident, evidence=detection.evidence)
    ).model_copy(update={"evidence_refs": evidence_refs})
    return AgenticReviewInput(
        incident=incident,
        evidence=surrounding,
        draft=draft,
        prompt_identity={
            "template_id": "reliability-agentic-review.null-spike",
            "version": "v1",
        },
        project_revision="utility-proof-fixture-revision",
    )


def _build_output(
    review_input: AgenticReviewInput,
    *,
    utility_contributions: tuple[AgenticReviewUtilityContribution, ...],
) -> AgenticReviewOutput:
    return AgenticReviewOutput(
        incident_id=review_input.incident.incident_id,
        incident_type="null_spike",
        target_column=review_input.target_column,
        deterministic_facts=review_input.deterministic_facts,
        review_summary="Profile evidence confirms an income null-rate increase.",
        evidence_used=(review_input.evidence[0].evidence_id,),
        findings=(),
        uncertainties=("Root cause remains unconfirmed.",),
        advisory_recommendation="needs_human_review",
        utility_contributions=utility_contributions,
    )


def _evaluation(
    *,
    evaluation_id: str,
    invocation_id: str,
    output_kind: str,
    score: int,
    case_id: str = CASE_ID,
) -> HumanUtilityEvaluation:
    return HumanUtilityEvaluation(
        evaluation_id=evaluation_id,
        case_id=case_id,
        case_version=CASE_VERSION,
        invocation_id=invocation_id,
        rubric_id=RUBRIC_V1.rubric_id,
        output_kind=output_kind,
        scores=tuple(
            RubricScore(
                criterion=criterion,
                score=score,
                rationale=f"Human score for {criterion.value}",
            )
            for criterion in RubricCriterion
        ),
    )


def _output_digest(output: AgenticReviewOutput) -> str:
    return (
        "sha256:"
        f"{hashlib.sha256(canonical_json_bytes(output.model_dump(mode='json'))).hexdigest()}"
    )


def _current_revision() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    revision = result.stdout.strip()
    if not revision:
        raise RuntimeError("Git HEAD is empty")
    return revision


if __name__ == "__main__":
    raise SystemExit(main())
