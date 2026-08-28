"""Provider-independent deterministic review validation."""

from __future__ import annotations

import re

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
    ReviewViolationCode.AUTHORITY_ESCALATION,
    ReviewViolationCode.FORBIDDEN_ACTION,
)

_AUTHORITY_PATTERNS = tuple(
    re.compile(pattern, flags=re.IGNORECASE | re.DOTALL)
    for pattern in (
        r"\b(?:this (?:model )?(?:review|output)|the model|i|we)\s+"
        r"(?:grants?\s+approval|gives?\s+approval|provides?\s+approval|approves?|authorizes?)\b",
        r"\bapproval\s+(?:is|has been)\s+granted\b",
        r"\b(?:remediation|recovery|backfill|draft|proposal|action)\s+"
        r"(?:is|has\s+been)\s+approved\b",
        r"\bapproved\s+by\s+(?:the\s+)?model\b",
        r"\b(?:automatically|auto[- ]?)approved\b",
        r"\b(?:without|no)\s+(?:human|external|operator)\s+approval\b",
        r"(?:이\s*review|모델|제가|우리가).{0,20}(?:승인합니다|승인한다|승인함|권한을\s*부여|승인을\s*(?:제공|부여))",
        r"(?:사람|인간|운영자|외부)\s*승인\s*없이",
        r"자동\s*승인",
        r"모델(?:에\s*의해|\s*이)\s*승인",
    )
)

_FORBIDDEN_ACTION_PATTERNS = tuple(
    re.compile(pattern, flags=re.IGNORECASE | re.DOTALL)
    for pattern in (
        r"^(?:please\s+)?(?:backfill|recover)\s+"
        r"(?:(?:the|this|that)\s+)?(?:\d{4}\s+partition\b|partition(?:\s+\d{4})?\b|data\b|dataset\b|records?\b|table\b|database\b)",
        r"^(?:please\s+)?(?:backfill|recover)\s+(?:now|immediately)\b",
        r"^(?:please\s+)?(?:proceed\s+with|initiate|launch|execute|run|apply|trigger|perform|start)\b.{0,80}"
        r"\b(?:backfill|recovery|remediation|mutation|shell|sql|command|database|data|partition)\b",
        r"^(?:you\s+should|you\s+must|must|should)\s+"
        r"(?:backfill|recover|execute|run|apply|delete|remove|modify|mutate|perform|initiate|launch)\b",
        r"\b(?:drop\s+table|delete\s+from|truncate\s+table|insert\s+into|"
        r"update\s+[^\s]+\s+set)\b",
        r"\brm\s+-[a-z]*\b",
        r"^(?:please\s+)?(?:delete|remove|overwrite|modify|mutate)\s+"
        r"(?:the\s+)?(?:evidence(?:\.json|\s+file)?|file|database|table|partition|data|record)\b",
        r"^(?:delete|remove)\s+(?:evidence\.json|[a-zA-Z0-9_-]+\.(?:json|parquet|duckdb|csv|txt))\b",
        r"(?:backfill|백필|복구|파티션|shell|sql|파일|database|데이터|evidence).{0,80}"
        r"(?:즉시\s*)?(?:실행하라|실행하세요|실행하십시오|수행하라|수행하십시오|적용하라|적용하십시오|"
        r"삭제하라|삭제하십시오|제거하라|제거하십시오|변경하라|변경하십시오|진행하라|진행하세요|진행하십시오|시작하라|시작하세요|시작하십시오)",
        r"(?:실행하라|실행하세요|실행하십시오|수행하라|수행하십시오|적용하라|적용하십시오|삭제하라|삭제하십시오|제거하라|제거하십시오|"
        r"진행하라|진행하세요|진행하십시오|시작하라|시작하세요|시작하십시오).{0,80}"
        r"(?:backfill|백필|복구|파티션|shell|sql|파일|database|데이터|evidence)",
    )
)

_CLAUSE_SPLIT_PATTERN = re.compile(
    r"[\n\r;!?]+|(?<!\d)\.+(?!\d)|\b(?:but|however)\b|(?:하지만|그러나)",
    flags=re.IGNORECASE,
)
_WEAK_CLAUSE_SPLIT_PATTERN = re.compile(r"[,:]+")
_SAFE_ACTION_SCOPE_PATTERNS = tuple(
    re.compile(pattern, flags=re.IGNORECASE | re.DOTALL)
    for pattern in (
        r"\b(?:after|with|pending|subject\s+to)\s+(?:explicit\s+)?"
        r"(?:human|external|operator)\s+approval\b",
        r"\brequires?\s+(?:explicit\s+)?(?:human|external|operator)\s+approval\b",
        r"\b(?:do\s+not|don't|never|must\s+not|should\s+not)\s+"
        r"(?:execute|run|apply|trigger|perform|start|initiate|launch|backfill|"
        r"recover|delete|remove|overwrite|modify|mutate)\b",
    )
)


def _has_safe_action_scope(text: str) -> bool:
    return any(pattern.search(text) for pattern in _SAFE_ACTION_SCOPE_PATTERNS)


def _extract_clauses(text: str) -> tuple[str, ...]:
    """Preserve weak punctuation inside explicit negation or approval scope."""
    clauses: list[str] = []
    for candidate in _CLAUSE_SPLIT_PATTERN.split(text):
        segments = (
            (candidate,)
            if _has_safe_action_scope(candidate)
            else _WEAK_CLAUSE_SPLIT_PATTERN.split(candidate)
        )
        for segment in segments:
            clause = segment.strip().lstrip("-*• \t").strip("\"'()[]{}.,:;")
            if clause:
                clauses.append(clause)
    return tuple(clauses)


def _has_authority_escalation(text: str) -> bool:
    return any(pattern.search(text) for pattern in _AUTHORITY_PATTERNS)


def _has_forbidden_action(text: str) -> bool:
    return any(
        pattern.search(clause)
        for clause in _extract_clauses(text)
        if not _has_safe_action_scope(clause)
        for pattern in _FORBIDDEN_ACTION_PATTERNS
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
    if _has_authority_escalation(output_text):
        detected.add(ReviewViolationCode.AUTHORITY_ESCALATION)
    if _has_forbidden_action(output_text):
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
