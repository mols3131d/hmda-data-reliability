"""Provider-independent deterministic review validation."""

from __future__ import annotations

import re

from hmda_reliability.reliability.agentic_review.contracts import (
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
    ReviewViolationCode.AUTHORITY_ESCALATION,
    ReviewViolationCode.FORBIDDEN_ACTION,
)

_AUTHORITY_PATTERNS = tuple(
    re.compile(pattern, flags=re.IGNORECASE | re.DOTALL)
    for pattern in (
        r"\b(?:this (?:model )?review|the model|i|we)\s+"
        r"(?:grants?\s+approval|approves?|authorizes?)\b",
        r"\bapproval\s+(?:is|has been)\s+granted\b",
        r"\b(?:remediation|recovery|backfill|draft|proposal|action)\s+"
        r"(?:is|has\s+been)\s+approved\b",
        r"\b(?:automatically|auto[- ]?)approved\b",
        r"\b(?:without|no)\s+(?:human|external)\s+approval\b",
        r"(?:이\s*review|모델|제가|우리가).{0,20}(?:승인합니다|권한을\s*부여)",
        r"(?:사람|인간|외부)\s*승인\s*없이",
        r"자동\s*승인",
    )
)

_FORBIDDEN_ACTION_PATTERNS = tuple(
    re.compile(pattern, flags=re.IGNORECASE | re.DOTALL)
    for pattern in (
        r"\b(?:you\s+should|you\s+must|must|should)\s+"
        r"(?:backfill|recover|execute|run|apply|delete|modify|mutate|perform|initiate|launch)\b.{0,80}"
        r"\b(?:now|immediately)\b",
        r"\b(?:drop\s+table|delete\s+from|truncate\s+table|insert\s+into|"
        r"update\s+[^\s]+\s+set)\b",
        r"\b(?:execute|run|apply|trigger|perform|start|proceed\s+with|initiate|launch)\b.{0,80}"
        r"\b(?:backfill|recovery|remediation|mutation|shell|sql|command|database|file|data)\b.{0,80}"
        r"\b(?:now|immediately)\b",
        r"\b(?:backfill|recovery|remediation|mutation|shell|sql|command)\b.{0,80}"
        r"\b(?:execute|run|apply|trigger|perform|start|proceed\s+with|initiate|launch)\b.{0,80}"
        r"\b(?:now|immediately)\b",
        r"(?:^|[.!?]\s*)(?:please\s+)?"
        r"(?:backfill|proceed\s+with\s+(?:the\s+)?backfill|initiate\s+(?:the\s+)?recovery|"
        r"launch\s+(?:the\s+)?backfill|execute\s+(?:the\s+)?backfill|run\s+(?:the\s+)?backfill)\s+"
        r"(?:the|this|that|\d{4}\b).{0,80}\b(?:now|immediately)\b",
        r"(?:^|[.!?]\s*)(?:please\s+)?"
        r"(?:proceed\s+with|initiate|launch)\s+"
        r"(?:the\s+|this\s+)?(?:backfill|recovery|remediation|mutation)\s+"
        r"(?:now|immediately)\b",
        r"(?:^|[.!?]\s*)(?:please\s+)?"
        r"(?:delete|overwrite|modify|mutate)\s+(?:the|this|that)\b",
        r"\brm\s+-[a-z]*r[a-z]*\b",
        r"(?:backfill|백필|복구|shell|sql|파일|database|데이터).{0,80}"
        r"(?:즉시\s*)?(?:실행하라|실행하세요|수행하라|적용하라|삭제하라|변경하라|진행하라|진행하세요|시작하라|시작하세요)",
        r"(?:실행하라|실행하세요|수행하라|적용하라|진행하라|진행하세요|시작하라|시작하세요).{0,80}"
        r"(?:backfill|백필|복구|shell|sql|파일|database|데이터)",
        r"(?:지금\s*)?(?:즉시\s*)?(?:백필|복구)(?:을|를)?\s*"
        r"(?:진행하라|진행하세요|시작하라|시작하세요|실행하라|실행하세요)",
    )
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

    if (
        output.incident_id != review_input.incident.incident_id
        or output.incident_type != review_input.incident.incident_type
    ):
        detected.add(ReviewViolationCode.INCIDENT_MISMATCH)

    if (
        output.target_column != review_input.target_column
        or output.deterministic_facts != review_input.deterministic_facts
    ):
        detected.add(ReviewViolationCode.DETERMINISTIC_CONTRADICTION)

    output_text = _review_text(output)
    if any(pattern.search(output_text) for pattern in _AUTHORITY_PATTERNS):
        detected.add(ReviewViolationCode.AUTHORITY_ESCALATION)
    if any(pattern.search(output_text) for pattern in _FORBIDDEN_ACTION_PATTERNS):
        detected.add(ReviewViolationCode.FORBIDDEN_ACTION)

    violations = tuple(code for code in _VIOLATION_ORDER if code in detected)
    status = (
        ReviewValidationStatus.REJECTED
        if violations
        else ReviewValidationStatus.ACCEPTED
    )
    return AgenticReviewValidation(status=status, violations=violations)


def _review_text(output: AgenticReviewOutput) -> str:
    parts = [output.review_summary, *output.uncertainties]
    parts.extend(finding.description for finding in output.findings)
    return "\n".join(parts)
