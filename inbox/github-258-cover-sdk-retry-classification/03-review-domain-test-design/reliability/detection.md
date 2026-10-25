---
type: review
title: Reliability Detection Test Design Review
description: Incident detector와 quality policy의 경계값·독립 규칙·정확한 evidence 테스트를 검토합니다.
---

# Reliability Detection Test Design Review

> [!NOTE]
> 정확한 incident 목록과 고정 수치가 알려진 오탐·누락을 구별한다. 현재 범위에서 추가 material finding은 확인하지 못했다.

- **Target**: Reliability detection와 quality policy.
- **Revision**: `3ab899100fc0b35e23d464bd761f3b144a978ae7`.
- **Scope**: [test_basic_incident_detection.py](../../../../tests/reliability/test_basic_incident_detection.py), [test_quality_gate.py](../../../../tests/reliability/test_quality_gate.py) 전체와 관련 detector·policy·Spec.

## Findings

채택한 material finding은 없다. PR #252에서 다룬 zero-threshold 무변화 오탐은 현재 regression이 보호한다. 과거 결함을 현재 미해결 항목으로 다시 세지 않는다.

## Design Assessment

| Area | Scenario And Oracle | Strength And Limit |
| --- | --- | --- |
| Incident result | exact incident/payload, asset·partition·evidence 연결 | 단순 발생 여부보다 구체적인 값·집합 비교 |
| Relative change | 무변화·개선·실제 양의 악화, 0 threshold, 양수 equality | inclusive threshold와 실제 악화 조건을 분리 |
| Rule independence | zero-row baseline, schema·freshness 독립 실행 | volume의 조기 종료가 전체 탐지를 막는 회귀를 검출 |
| Freshness | below/equal boundary, unavailable, 고정 시간 | 상대 변화와 절대 age의 의미를 혼동하지 않음 |
| Quality policy | 고정 baseline, 정확한 5 percentage-point 경계, null spike, 빈 partition·누락/미지원 컬럼 | 실제 detector 중심; non-blocking policy 분리 사례의 detector만 fake |

Detector의 주요 근거는 20행 이후와 198·236·264·323·362행, policy는 60·71·85·137·152·178행이다. Production 계산을 그대로 복제하는 oracle 대신 고정 수치와 정확한 incident 목록을 쓴다. Policy 테스트의 일부 fake detector를 전체 domain integration의 증거로 확대하지 않는다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 독립 full-body·계약 검토 | Batch B 두 관점 |
| ✅ Pass | 현재 실행 | [전체 suite](../validation.md#test-execution) |
| ⚪ Not Verified | 모든 새 정책·변경에 대한 일반 보장 | 이 revision의 명시된 계약에 한정 |
