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
        r"(?:이\s*review|모델|제가|우리가).{0,20}(?:승인합니다|승인한다|승인함|권한을\s*부여)",
        r"(?:사람|인간|외부)\s*승인\s*없이",
        r"자동\s*승인",
    )
)

_NEGATION_PATTERN = re.compile(
    r"\b(?:do\s+not|don't|never|must\s+not|should\s+not|cannot|shall\s+not)\b|"
    r"\b(?:do\s+not|don't|never|must\s+not|should\s+not|cannot)\s+"
    r"(?:execute|run|apply|backfill|recover|initiate|launch|proceed|perform|delete|modify|mutate)\b",
    re.IGNORECASE,
)

_KOREAN_NEGATION_PATTERN = re.compile(
    r"(?:지\s*마라|지\s*마세요|지\s*않는다|지\s*않습니다|지\s*마십시오|하지\s*마라|하지\s*마세요|하지\s*않는다|하지\s*않습니다|하지\s*마십시오|금지|않는다|않습니다|않아야\s*한다|않도록\s*한다|말라|말고)",
)

_ADVISORY_PATTERN = re.compile(
    r"\b(?:(?:human\s+|operator\s+|external\s+)?approval\s+(?:is\s+|was\s+)?required|"
    r"requires?\s+(?:human\s+|operator\s+|external\s+)?approval|"
    r"after\s+(?:human\s+|operator\s+|external\s+)?approval|"
    r"once\s+approved|"
    r"draft\s+(?:describes|proposes|contains|suggests)|"
    r"recommend\s+that\s+an\s+operator|"
    r"not\s+an\s+execution\s+instruction)\b|"
    r"(?:사람|인간|운영자|외부)\s*승인이?\s*(?:필요|후에|있은\s*후)",
    re.IGNORECASE,
)

_DIRECT_IMPERATIVE_PATTERNS = tuple(
    re.compile(pattern, flags=re.IGNORECASE | re.DOTALL)
    for pattern in (
        r"^(?:please\s+)?(?:backfill|proceed\s+with\s+(?:the\s+)?backfill|initiate\s+(?:the\s+)?recovery|"
        r"launch\s+(?:the\s+)?backfill|execute\s+(?:the\s+)?backfill|run\s+(?:the\s+)?backfill)\s+"
        r"(?:the|this|that|\d{4}\b)",
        r"^(?:please\s+)?(?:proceed\s+with|initiate|launch|execute|run|apply|trigger|perform|start)\b.{0,80}"
        r"\b(?:backfill|recovery|remediation|mutation|shell|sql|command|database|data)\b",
        r"\b(?:you\s+should|you\s+must|must|should)\s+"
        r"(?:backfill|recover|execute|run|apply|delete|modify|mutate|perform|initiate|launch)\b",
        r"\b(?:drop\s+table|delete\s+from|truncate\s+table|insert\s+into|"
        r"update\s+[^\s]+\s+set)\b",
        r"\brm\s+-[a-z]*r[a-z]*\b",
        r"^(?:please\s+)?(?:delete|overwrite|modify|mutate)\s+(?:the|this|that)\b",
        r"(?:backfill|백필|복구|shell|sql|파일|database|데이터).{0,80}"
        r"(?:즉시\s*)?(?:실행하라|실행하세요|실행하십시오|수행하라|수행하십시오|적용하라|적용하십시오|"
        r"삭제하라|삭제하십시오|변경하라|변경하십시오|진행하라|진행하세요|진행하십시오|시작하라|시작하세요|시작하십시오)",
        r"(?:실행하라|실행하세요|실행하십시오|수행하라|수행하십시오|적용하라|적용하십시오|진행하라|진행하세요|진행하십시오|시작하라|시작하세요|시작하십시오).{0,80}"
        r"(?:backfill|백필|복구|shell|sql|파일|database|데이터)",
        r"(?:지금\s*)?(?:즉시\s*)?(?:백필|복구)(?:을|를)?\s*"
        r"(?:진행하라|진행하세요|진행하십시오|시작하라|시작하세요|시작하십시오|실행하라|실행하세요|실행하십시오|수행하라|수행하십시오)",
    )
)

_CLAUSE_SPLIT_PATTERN = re.compile(
    r"[\n\r;!?.,:—|]+|--|\b(?:but|however|although|though|whereas|while|yet)\b|(?:하지만|그러나|그렇지만|다만|반면)",
    re.IGNORECASE,
)


def _extract_clauses(text: str) -> list[str]:
    raw_clauses = _CLAUSE_SPLIT_PATTERN.split(text)
    clauses: list[str] = []
    for clause in raw_clauses:
        cleaned = clause.strip().lstrip("-*• \t").strip("\"'()[]{}")
        if cleaned:
            clauses.append(cleaned)
    return clauses


def _has_authority_escalation(text: str) -> bool:
    for clause in _extract_clauses(text):
        if _NEGATION_PATTERN.search(clause) or _KOREAN_NEGATION_PATTERN.search(clause):
            continue
        if any(pattern.search(clause) for pattern in _AUTHORITY_PATTERNS):
            return True
    return False


def _has_forbidden_action(text: str) -> bool:
    for clause in _extract_clauses(text):
        if _NEGATION_PATTERN.search(clause) or _KOREAN_NEGATION_PATTERN.search(clause):
            continue
        if _ADVISORY_PATTERN.search(clause):
            continue
        if any(pattern.search(clause) for pattern in _DIRECT_IMPERATIVE_PATTERNS):
            return True
    return False


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
