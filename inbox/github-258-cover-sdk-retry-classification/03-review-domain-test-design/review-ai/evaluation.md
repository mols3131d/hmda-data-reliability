---
type: review
title: Review AI Evaluation Test Design Review
description: Utility 데이터의 serialization·criterion score attribution·Langfuse projection 테스트의 결정론적 oracle을 검토합니다.
---

# Review AI Evaluation Test Design Review

> [!NOTE]
> 독립 static golden과 projection binding이 호환성을 보호한다. Criterion별 점수 귀속은 균일한 fixture로 구별되지 않는다.

- **Target**: Review AI evaluation.
- **Revision**: `3ab899100fc0b35e23d464bd761f3b144a978ae7`.
- **Scope**: [utility 테스트](../../../../tests/review_ai/evaluation/test_utility_evaluation.py), [Langfuse projection 테스트](../../../../tests/review_ai/evaluation/test_langfuse_projection.py), [static golden](../../../../tests/review_ai/evaluation/fixtures/utility_comparison_6e64cc7.json) 전체.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| F1 | Minor | 동일한 rubric score가 criterion permutation을 가린다 | 서로 다른 score vector의 criterion별 비교 추가 |

## Subview Assessment

| Area | Scenario And Independent Oracle | Boundary And Limit |
| --- | --- | --- |
| Serialization/public compatibility | 과거 static JSON 전체·text 비교, nested enum/digest·public rename | writer→reader round trip만 사용하는 것이 아님 |
| Utility mechanics | 모델·annotation binding·score aggregation/comparison | fixture의 점수는 인간의 실제 utility 평가가 아님 |
| Langfuse projection | exact output·bool/int mismatch·annotation binding·환경 allowlist | exporter는 통제된 경계이며 remote ingestion은 증명하지 않음 |
| Export containment | 실제 stalled child와 SDK media 보존 | `submitted_unverified`는 제출 상태; UI·원격 ingestion·사람 검토 완료와 다름 |

주요 근거는 utility 테스트 134·169·193·211·317·335·351·375·400·423·445행, Langfuse 테스트 106·143·220·334·369·403·439·460·501행이다.

### F1 — Minor: Heterogeneous Score Attribution

#### Locations

- [test_utility_evaluation.py](../../../../tests/review_ai/evaluation/test_utility_evaluation.py)
  - `_scores`와 comparison 사례는 baseline 0·candidate 2를 모든 criterion에 동일 적용한다.
- [value.py](../../../../src/hmda_reliability/review_ai/evaluation/value.py)
  - criterion별 candidate score lookup은 현재 정상이다.

#### Evidence

합계를 유지하면서 candidate의 criterion별 점수를 서로 바꾸는 구현도 균일한 vector와 static golden에서는 같은 결과를 만든다. Heterogeneous hedging fixture는 comparison에 전달되지 않는다. 순서·합계 validation은 있지만 이 attribution 오류를 구별하지 않는다. 실제 mutant는 실행하지 않았다.

#### Action

서로 다른 점수 vector 한 쌍으로 criterion별 baseline·candidate·delta를 고정 비교한다. 실제 AI 점수의 적절성이나 subjective rubric을 이 리뷰에서 평가하자는 제안이 아니다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 독립 full-body·golden 검토 | Batch D 두 관점 |
| ✅ Pass | 현재 실행 | [전체 suite](../validation.md#test-execution) |
| ⚪ Not Verified | score permutation mutation | 정적 oracle gap |
| ⚪ Not Verified | Langfuse remote ingestion·human utility | 통제된 exporter·fixture와 구분 |
