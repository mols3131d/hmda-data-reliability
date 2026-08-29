"""Provider 독립적인 결정론적 review 검증 모듈."""

from __future__ import annotations

from hmda_reliability.review_ai.contracts import (
    AgenticReviewInput,
    AgenticReviewOutput,
    AgenticReviewValidation,
    ReviewValidationStatus,
    ReviewViolationCode,
)

# 결정론적 진단 순서를 보존하기 위한 표준 위반 평가 순서.
_VIOLATION_ORDER = (
    ReviewViolationCode.FABRICATED_EVIDENCE,
    ReviewViolationCode.INCIDENT_MISMATCH,
    ReviewViolationCode.DETERMINISTIC_CONTRADICTION,
)


def validate_agentic_review(
    review_input: AgenticReviewInput,
    output: AgenticReviewOutput,
) -> AgenticReviewValidation:
    """불변의 결정론적 입력 스냅샷과 provider 출력을 비교 검증한다.

    자연어 regex 휴리스틱 없이 3대 구조적 무결성 불변식을 강제한다:
    1. `fabricated_evidence`: 출력과 findings는 제공된 evidence ID만 참조해야 한다.
    2. `incident_mismatch`: 출력의 incident_id는 입력의 incident_id와 일치해야 한다.
    3. `deterministic_contradiction`: target_column 및 수치 팩트가 완전히 일치해야 한다.

    위반이 없으면 `ACCEPTED`, 감지 시 정규화된 위반 목록과 함께 `REJECTED`를 반환한다.
    """

    detected: set[ReviewViolationCode] = set()
    provided_evidence = {item.evidence_id for item in review_input.evidence}
    referenced_evidence = set(output.evidence_used)
    for finding in output.findings:
        referenced_evidence.update(finding.evidence_refs)
    # Evidence 참조 부분집합 불변식 검증.
    if not referenced_evidence.issubset(provided_evidence):
        detected.add(ReviewViolationCode.FABRICATED_EVIDENCE)

    # Incident 식별자 일치 불변식 검증.
    if output.incident_id != review_input.incident.incident_id:
        detected.add(ReviewViolationCode.INCIDENT_MISMATCH)

    # 대상 컬럼 및 결정론적 수치 사실 일치 불변식 검증.
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
