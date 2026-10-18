---
type: plan
title: Report Failed Recovery Actions Accurately
description: Schema recovery 실패가 Action PASS 및 100퍼센트 성공률로 집계되는 문제를 수정할 목표와 검증 조건입니다.
---

# Report Failed Recovery Actions Accurately

## Goal

Schema recovery의 실제 target-side 검증이 실패해도 `action_passed=True`, Action `PASS`, 집계 성공률 100%로 표기되는 결함을 해결한다. 실패 단계와 별도로 **요구되는 복구 조치의 미충족 상태**가 집계에 반영돼야 한다.

## Evidence

PR #258 [G6/E1 재현](https://github.com/mols3131d/hmda-data-reliability/blob/b6b47606bdabf69221eff94c8f9c69dc03b6cc57/inbox/github-258-cover-sdk-retry-classification/03-review-domain-test-design/validation.md#c1-failed-recovery-action-metric)에서 `recovery_dbt_failure`의 `required_actions=[]`, `remediation_actions=[]`로 인해 실패한 사례가 Action PASS였다. 현재 `action_passed`의 subset 계산 자체는 정상이며, 원인은 schema 실패 결과의 action 매핑으로 분석됐다.

## Scope

- **In Scope:** schema drift evaluator의 실패 case action 표현과 `EvaluationCaseResult` → 집계 → Markdown으로 이어지는 회귀 테스트.
- **Out of Scope:** 일반 action subset 판정의 의미 변경, 다른 recovery executor의 동작 변경, 실제 AI 리뷰 품질 평가 및 광범위한 새 지표.
- **Boundary:** 정상/clean 사례에서 required action이 비어 있는 기존 의미를 파괴하지 않는다.

## Acceptance

- Target dbt validation 실패를 주입한 schema recovery 사례에서 `action_passed=False`다.
- 동일 결과를 집계하고 렌더링했을 때 실패 사례의 Action은 `FAIL`이며 집계 success count/rate가 이를 반영한다.
- 기존 성공/실패 단계·mutation/reconciliation evidence를 보존하고 정상 schema recovery 결과에는 회귀가 없다.
- Test-first 회귀와 관련 evaluation 테스트·CI의 실제 결과를 기록한다.

## Next

최신 `main`에서 failure case 재현 → action mapping을 최소 수정 → property/aggregate/Markdown oracle 검증 → 리뷰.

## References

- [Evaluation report contract](../../openspec/specs/reliability-evaluation-report/spec.md)
- [G6 review](https://github.com/mols3131d/hmda-data-reliability/blob/b6b47606bdabf69221eff94c8f9c69dc03b6cc57/inbox/github-258-cover-sdk-retry-classification/03-review-domain-test-design/reliability/evaluation.md)
