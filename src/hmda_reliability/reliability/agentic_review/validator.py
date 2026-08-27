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

_QUOTE_PATTERN = re.compile(
    r"""(?<![a-zA-Z0-9])'[^'\n]+'(?![a-zA-Z0-9])|"[^"\n]+"|`[^`\n]+`"""
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
        r"\b(?:this\s+review\s+gives\s+approval|this\s+review\s+grants\s+approval)\b",
        r"\b(?:automatically|auto[- ]?)approved\b",
        r"\b(?:without|no)\s+(?:human|external|operator)\s+approval\b",
        r"(?:이\s*review|모델|제가|우리가).{0,20}(?:승인합니다|승인한다|승인함|권한을\s*부여|승인을\s*(?:제공|부여))",
        r"(?:사람|인간|운영자|외부)\s*승인\s*없이",
        r"자동\s*승인",
        r"모델(?:에\s*의해|\s*이)\s*승인",
    )
)

_AUTHORITY_NEGATION_PATTERN = re.compile(
    r"\b(?:does\s+not|do\s+not|cannot|shall\s+not|will\s+not|is\s+not|not)\s+"
    r"(?:grant\s+approval|give\s+approval|approve|authorize)\b"
    r"|\bapproval\s+is\s+not\s+granted\b"
    r"|\b(?:not|never|no)\s+(?:automatically|auto[- ]?)approved\b"
    r"|자동\s*승인\s*(?:금지|되지|하지|않)"
    r"|승인(?:하지\s*않|되지\s*않|을\s*부여하지\s*않)",
    re.IGNORECASE,
)

_DIRECT_IMPERATIVE_PATTERNS = tuple(
    re.compile(pattern, flags=re.IGNORECASE | re.DOTALL)
    for pattern in (
        # Direct backfill / recovery
        r"\b(?:please\s+)?(?:backfill|proceed\s+with\s+(?:the\s+)?backfill|initiate\s+(?:the\s+)?(?:recovery|backfill)|"
        r"launch\s+(?:the\s+)?backfill|execute\s+(?:the\s+)?backfill|run\s+(?:the\s+)?backfill)"
        r"(?:\s+(?:(?:the|this|that)\s+)?(?:\d{4}\s+partition\b|partition\s+\d{4}\b|\d{4}\b|partition\b|recovery\b|backfill\b|action\b))?",
        r"\b(?:please\s+)?(?:backfill|recover)\b(?:\s+(?:(?:the|this|that)\s+)?(?:\d{4}\s+partition\b|partition\s+\d{4}\b|\d{4}\b|partition\b))?",
        r"\b(?:please\s+)?(?:proceed\s+with|initiate|launch|execute|run|apply|trigger|perform|start)\b.{0,60}"
        r"\b(?:backfill|recovery|remediation|mutation|shell|sql|command|database|data|partition)\b",
        # Modal imperatives
        r"\b(?:you\s+should|you\s+must|must|should)\s+"
        r"(?:backfill|recover|execute|run|apply|delete|remove|modify|mutate|perform|initiate|launch)\b",
        # Destructive SQL
        r"\b(?:drop\s+table|delete\s+from|truncate\s+table|insert\s+into|"
        r"update\s+[^\s]+\s+set)\b",
        # Destructive shell
        r"\brm\s+-[a-z]*\b",
        # File / Table / Data deletion or mutation
        r"\b(?:please\s+)?(?:delete|remove|overwrite|modify|mutate)\s+"
        r"(?:the\s+)?(?:evidence(?:\.json|\s+file)?|file|database|table|partition|data|record)\b",
        r"\b(?:delete|remove)\s+(?:evidence\.json|[a-zA-Z0-9_-]+\.(?:json|parquet|duckdb|csv|txt))\b",
        # Korean imperatives
        r"(?:backfill|백필|복구|파티션|shell|sql|파일|database|데이터|evidence).{0,60}"
        r"(?:즉시\s*)?(?:실행하라|실행하세요|실행하십시오|수행하라|수행하십시오|적용하라|적용하십시오|"
        r"삭제하라|삭제하십시오|제거하라|제거하십시오|변경하라|변경하십시오|진행하라|진행하세요|진행하십시오|시작하라|시작하세요|시작하십시오)",
        r"(?:실행하라|실행하세요|실행하십시오|수행하라|수행하십시오|적용하라|적용하십시오|삭제하라|삭제하십시오|제거하라|제거하십시오|"
        r"진행하라|진행하세요|진행하십시오|시작하라|시작하세요|시작하십시오).{0,60}"
        r"(?:backfill|백필|복구|파티션|shell|sql|파일|database|데이터|evidence)",
        r"(?:지금\s*)?(?:즉시\s*)?(?:백필|복구|삭제|제거)(?:을|를)?\s*"
        r"(?:진행하라|진행하세요|진행하십시오|시작하라|시작하세요|시작하십시오|실행하라|실행하세요|실행하십시오|수행하라|수행하십시오|삭제하라|삭제하십시오|제거하라|제거하십시오)",
    )
)

_PRE_NEGATION_PATTERN = re.compile(
    r"(?:\b(?:do\s+not|don't|never|must\s+not|should\s+not|cannot|shall\s+not|prohibit(?:ed)?|forbidden|no\s+execution)\b"
    r"(?:\s+(?:to\s+)?(?:execute|run|apply|perform|initiate|launch|proceed\s+with|start|backfill|recover))?"
    r"(?:\s*:\s*|\s+)"
    r"|(?:실행\s*금지|금지)\s*:\s*)\s*$",
    re.IGNORECASE,
)

_POST_NEGATION_PATTERN = re.compile(
    r"^(?:\s*)(?:하지\s*마라|하지\s*마세요|하지\s*마십시오|지\s*마라|지\s*마세요|지\s*마십시오|"
    r"지\s*않는다|지\s*않습니다|않아야\s*한다|않도록\s*한다|금지|말라|말고)\b",
    re.IGNORECASE,
)

_PRE_CONDITIONAL_PATTERN = re.compile(
    r"(?:(?:only\s+)?after|(?:up)?on|with)\s+(?:(?:human|operator|external|engineer)\s+)?approval\s*,\s*$"
    r"|once\s+approved(?:\s+by\s+[a-zA-Z\s]+)?\s*,\s*$"
    r"|(?:사람|인간|운영자|외부|엔지니어)?\s*승인\s*(?:후에?|하에|시|조건으로)\s*,\s*$"
    r"|(?:the\s+)?(?:proposed\s+)?draft\s+(?:describes|proposes|contains|suggests)\s+(?:(?:a|the)\s+)?(?:action\s+that\s+)?$"
    r"|recommend\s+that\s+an\s+operator\s+$"
    r"|(?:analysis|assessment|evaluation)\s+indicates\s+that\s+(?:recovery\s+)?$",
    re.IGNORECASE,
)

_POST_CONDITIONAL_PATTERN = re.compile(
    r"^(?:\s*)(?:(?:for\s+(?:the\s+)?(?:\d{4}\s+partition|\d{4}|partition)\s+)?(?:(?:only\s+)?after|(?:up)?on|with)\s+(?:(?:human|operator|external|engineer)\s+)?approval\b)"
    r"|^(?:\s*)(?:that\s+)?requires?\s+(?:(?:human|operator|external|engineer)\s+)?approval\b"
    r"|^(?:\s*)is\s+(?:subject\s+to|conditional\s+upon)\s+(?:(?:human|operator|external|engineer)\s+)?approval\b"
    r"|^(?:\s*)once\s+approved\b"
    r"|^(?:\s*)without\s+(?:human|external|operator)\s+approval\b"
    r"|^(?:\s*)(?:for\s+(?:the\s+)?(?:\d{4}\s+partition|\d{4}|partition)\s+)?is\s+feasible\b"
    r"|^(?:\s*)after\s+thorough\s+review\b"
    r"|^(?:\s*)(?:은|는)?\s*(?:사람|인간|운영자|외부|엔지니어)?\s*승인이?\s*(?:필요|조건|후에|있은\s*후)",
    re.IGNORECASE,
)


def _mask_quotes(text: str) -> str:
    return _QUOTE_PATTERN.sub(" [quoted_ref] ", text)


def _split_sentences(text: str) -> list[str]:
    return [
        s.strip().lstrip("-*• \t").strip("\"'()[]{}.,:;")
        for s in re.split(r"[\n\r;!?]+|(?<!\d)\.+(?!\d)", text)
        if s.strip()
    ]


def _merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not intervals:
        return []
    sorted_intervals = sorted(intervals, key=lambda x: (x[0], -x[1]))
    merged: list[tuple[int, int]] = [sorted_intervals[0]]
    for start, end in sorted_intervals[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def _has_authority_escalation(text: str) -> bool:
    masked_text = _mask_quotes(text)
    for sentence in _split_sentences(masked_text):
        if _AUTHORITY_NEGATION_PATTERN.search(sentence):
            continue
        for pattern in _AUTHORITY_PATTERNS:
            for match in pattern.finditer(sentence):
                prefix = sentence[: match.start()]
                matched = match.group(0)
                if re.search(
                    r"\b(?:without|no)\s+(?:human|external|operator)\s+approval\b",
                    matched,
                    re.IGNORECASE,
                ) and re.search(
                    r"\b(?:do\s+not|don't|never|must\s+not|should\s+not|cannot|shall\s+not)\b",
                    prefix,
                    re.IGNORECASE,
                ):
                    continue
                if re.search(
                    r"(?:사람|인간|운영자|외부)\s*승인\s*없이", matched
                ) and re.search(
                    r"(?:지\s*마라|하지\s*마라|금지|않는다)",
                    sentence,
                ):
                    continue
                return True
    return False


def _has_forbidden_action(text: str) -> bool:
    masked_text = _mask_quotes(text)
    for sentence in _split_sentences(masked_text):
        if "not an execution instruction" in sentence.lower():
            continue
        raw_intervals: list[tuple[int, int]] = []
        for pattern in _DIRECT_IMPERATIVE_PATTERNS:
            for match in pattern.finditer(sentence):
                raw_intervals.append((match.start(), match.end()))
        if not raw_intervals:
            continue
        merged = _merge_intervals(raw_intervals)
        for start, end in merged:
            prefix = sentence[:start]
            suffix = sentence[end:]
            if _PRE_NEGATION_PATTERN.search(prefix):
                continue
            if _POST_NEGATION_PATTERN.search(suffix):
                continue
            if _PRE_CONDITIONAL_PATTERN.search(prefix):
                continue
            if _POST_CONDITIONAL_PATTERN.search(suffix):
                continue
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
