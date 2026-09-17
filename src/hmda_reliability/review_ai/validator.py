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
    1. `fabricated_evidence`: 출력의 `evidence_used` 및 `findings`의 `evidence_refs`는
       반드시 입력에서 제공된 `evidence` ID 목록의 부분집합이어야 한다.
    2. `incident_mismatch`: 출력 `incident_id`는 입력 `incident_id`와 일치해야 한다.
    3. `deterministic_contradiction`: 출력의 `target_column` 및 수치 팩트
       (`deterministic_facts`)가 입력의 표준 프로파일 팩트와 완전히 일치해야 한다.

    위반이 없으면 `ACCEPTED`, 감지 시 `_VIOLATION_ORDER`에 따라 정규화된 위반 목록과
    함께 `REJECTED` 상태의 `AgenticReviewValidation`을 반환한다.
    """

    detected: set[ReviewViolationCode] = set()

    # 1. Evidence 참조 무결성 검증 (허위/환각 증적 방지)
    provided_evidence = {item.evidence_id for item in review_input.evidence}
    referenced_evidence = set(output.evidence_used)
    for finding in output.findings:
        referenced_evidence.update(finding.evidence_refs)
    for contribution in output.utility_contributions:
        referenced_evidence.update(contribution.evidence_refs)
    if not referenced_evidence.issubset(provided_evidence):
        detected.add(ReviewViolationCode.FABRICATED_EVIDENCE)

    # 2. Incident 식별자 일치 검증
    if output.incident_id != review_input.incident.incident_id:
        detected.add(ReviewViolationCode.INCIDENT_MISMATCH)

    # 3. 대상 컬럼 및 결정론적 수치 사실 일치 검증
    target_column_mismatch = output.target_column != review_input.target_column
    deterministic_facts_mismatch = (
        output.deterministic_facts != review_input.deterministic_facts
    )
    if target_column_mismatch or deterministic_facts_mismatch:
        detected.add(ReviewViolationCode.DETERMINISTIC_CONTRADICTION)

    # 결정론적 진단 순서에 따라 튜플 정규화
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
