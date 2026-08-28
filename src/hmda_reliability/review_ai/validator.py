"""Provider-independent deterministic review validation."""

from __future__ import annotations

from hmda_reliability.review_ai.contracts import (
    AgenticReviewInput,
    AgenticReviewOutput,
    AgenticReviewValidation,
    ReviewValidationStatus,
    ReviewViolationCode,
)

_VIOLATION_ORDER = (
    ReviewViolationCode.FABRICATED_EVIDENCE,
    ReviewViolationCode.INCIDENT_MISMATCH,
    ReviewViolationCode.DETERMINISTIC_CONTRADICTION,
)


def validate_agentic_review(
    review_input: AgenticReviewInput,
    output: AgenticReviewOutput,
) -> AgenticReviewValidation:
    """Compare provider output with the immutable deterministic input snapshot."""

    detected: set[ReviewViolationCode] = set()
    provided_evidence = {item.evidence_id for item in review_input.evidence}
    referenced_evidence = set(output.evidence_used)
    for finding in output.findings:
        referenced_evidence.update(finding.evidence_refs)
    if not referenced_evidence.issubset(provided_evidence):
        detected.add(ReviewViolationCode.FABRICATED_EVIDENCE)

    if output.incident_id != review_input.incident.incident_id:
        detected.add(ReviewViolationCode.INCIDENT_MISMATCH)

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
