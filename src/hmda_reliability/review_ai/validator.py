"""Provider-independent deterministic review validation."""

from __future__ import annotations

from hmda_reliability.review_ai.contracts import (
    AgenticReviewInput,
    AgenticReviewOutput,
    AgenticReviewValidation,
    ReviewValidationStatus,
    ReviewViolationCode,
)

# Canonical violation evaluation order preserved for deterministic diagnostics.
_VIOLATION_ORDER = (
    ReviewViolationCode.FABRICATED_EVIDENCE,
    ReviewViolationCode.INCIDENT_MISMATCH,
    ReviewViolationCode.DETERMINISTIC_CONTRADICTION,
)


def validate_agentic_review(
    review_input: AgenticReviewInput,
    output: AgenticReviewOutput,
) -> AgenticReviewValidation:
    """Validate provider output against immutable deterministic input snapshot.

    Enforces three structural integrity invariants:
    1. `fabricated_evidence`: output must cite only supplied evidence IDs.
    2. `incident_mismatch`: output incident_id must match input incident_id.
    3. `deterministic_contradiction`: target_column and facts must match exactly.

    Returns `AgenticReviewValidation` with `ACCEPTED` if valid, or `REJECTED`
    with canonically ordered violation codes.
    """

    detected: set[ReviewViolationCode] = set()
    provided_evidence = {item.evidence_id for item in review_input.evidence}
    referenced_evidence = set(output.evidence_used)
    for finding in output.findings:
        referenced_evidence.update(finding.evidence_refs)
    # Check evidence citation subset invariant.
    if not referenced_evidence.issubset(provided_evidence):
        detected.add(ReviewViolationCode.FABRICATED_EVIDENCE)

    # Check incident identity invariant.
    if output.incident_id != review_input.incident.incident_id:
        detected.add(ReviewViolationCode.INCIDENT_MISMATCH)

    # Check numerical and column fact equality invariant.
    if (
        output.target_column != review_input.target_column
        or output.deterministic_facts != review_input.deterministic_facts
    ):
        detected.add(ReviewViolationCode.DETERMINISTIC_CONTRADICTION)

    violations = tuple(code for code in _VIOLATION_ORDER if code in detected)
    status = (
        ReviewValidationStatus.REJECTED
        if violations
        else ReviewValidationStatus.ACCEPTED
    )
    return AgenticReviewValidation(
        status=status,
        violations=violations,
        policy_id="structured-fact-validation-v1",
    )
