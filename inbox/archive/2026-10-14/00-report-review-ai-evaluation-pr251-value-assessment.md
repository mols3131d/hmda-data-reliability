---
type: report
title: Review AI Capability Value Assessment
description: Review AI 기능 자체와 human utility evaluation·baseline comparison·Langfuse 관찰 기능의 필요성에 관한 사용자 의문, 확인된 사실과 검증 과제를 보존한다.
tags:
  - review-ai
  - evaluation
  - product-value
  - decision
---

# Review AI Capability Value Assessment

> [!IMPORTANT]
> **사용자 의견 (2026-10-14):** "이거 pr 닫아야하는거 아닐까? 실효성이 없어 보이는데 맞니?"
>
> **후속 정정:** "pr 에 대한 실효성을 넘어서 이 기능에 대한 의문이다."
>
> 핵심 의문은 PR #251의 코드 변경 규모나 리팩터링 타당성이 아니다. **Review AI 기능 자체가 사람의 reliability 판단에 실질적으로 도움이 되는지, 이를 위해 구축한 human utility evaluation·baseline/candidate 비교와 선택적 Langfuse 연동이 실제로 필요한지**에 관한 문제 제기다. 이는 결함 확정이나 제거 결정이 아니라, 기능의 가치가 충분히 입증됐는지에 대한 미해결 질문이다.

## Question and Scope

이 프로젝트는 이미 결정론적인 incident detection, evidence와 `RemediationDraft`를 만든다. 여기에 Review AI가 덧붙이는 결과가 사람이 **더 나은 조사·복구 판단을 내리도록 돕는가?** 그리고 그 효과를 입증하는 데 현재 평가·관찰 기능의 비용이 정당한가?

다음 세 층을 구별한다.

1. **Review AI:** 근거를 활용해 advisory review를 생성하는 기능. 이것 자체가 기존 deterministic evidence보다 나은 판단을 제공하는지가 첫 질문이다.
2. **Human utility evaluation / comparison:** 다섯 항목 `rubric_v1`으로 사람이 채점하고 동일 case의 baseline/candidate를 비교하는 기능. 실제 변경 결정에 활용되는지가 두 번째 질문이다.
3. **Optional Langfuse projection:** 검증된 synthetic invocation을 외부 UI에 사후 투영하고 수동 annotation을 돕는 기능. 로컬 provenance·평가 기록만으로 부족한 실질적 필요가 있는지가 세 번째 질문이다.

이 문서의 질문은 특정 Python class 이름, 패키지 구조 또는 PR #251의 diff 자체를 평가하는 질문과 **다르다**.

## Current Evidence

| 확인된 사실 | 의미와 한계 |
| --- | --- |
| Review AI는 bounded evidence와 deterministic structured-fact validation을 사용한다. | 안전한 계약과 사실 정합성의 근거이지, 추가적인 **판단 효용**의 증거는 아니다. |
| `ReviewValueAssessment`와 `compare_review_value()`가 versioned rubric, 평가 근거, 비교 조건 및 `blocked` 상태를 지원한다. | 같은 기준의 평가를 표현하고 비교할 **수단**이 존재한다. 사람이 이를 이용해 더 나은 결정을 내렸다는 뜻은 아니다. |
| 테스트는 positive/restatement/hedging fixture, serialized contract와 회귀 동작을 검증한다. | 규칙과 fixture 판별력을 확인한다. 실제 인간 평가의 일관성·효과를 대신하지 않는다. |
| Langfuse는 opt-in child process projection이고 원격 전달은 `submitted_unverified`로 구분한다. | 관찰 경계가 분리돼 있다. 원격 ingestion, annotation 완료 또는 운영상의 필요를 증명하지 않는다. |

근거: [MVP 목표](../../../docs/mvp.md), [Review AI domain](../../../docs/domains/review-ai.md), [canonical Spec](../../../openspec/specs/reliability-agentic-review/spec.md), [평가 구현](../../../src/hmda_reliability/review_ai/evaluation/value.py), [평가 실행 가이드](../../../docs/development/review-ai-evaluation.md).

**아직 확인되지 않은 핵심 증거:** representative incident에서 Review AI 유무에 따른 사람의 최종 조사 방향·판단 품질·소요 노력의 차이, 실제 사람이 수행한 rubric 결과와 반복성, baseline/candidate 비교가 실제 변경 채택 결정을 개선한 사례, Langfuse를 사용해야만 얻을 수 있었던 통찰. 이 기록에서 이를 확인하지 못했다는 뜻이며, 존재하지 않는다고 확정하는 것은 아니다.

## Value Hypotheses and Doubts

### Review AI

- **기대 가치:** deterministic evidence가 놓친 조사 우선순위, 근거 공백, remediation 위험 또는 불확실성을 지적할 수 있다.
- **의문:** 결과가 이미 제공된 incident/evidence/`RemediationDraft`의 자연어 재진술에 머문다면 LLM 실행과 검토 비용을 정당화할 수 없다. 구조적 검증 통과와 유용함은 다른 문제다.

### Human Evaluation and Comparison

- **기대 가치:** 인간 평가를 동일한 case·rubric·output identity에 연결하고 prompt/model/context 변경 전후의 결정을 추적할 수 있다.
- **의문:** 실제로 사람이 반복 채점하거나 baseline을 비교해 변경을 채택하는 흐름이 없다면, 다섯 항목 점수와 여러 비교 모델·identity·digest 계약은 실효성보다 운영 부담이 클 수 있다.
- **구분:** 사람의 간단한 사례 리뷰가 필요한 것과 지금 구현된 **비교 계약 전체**가 필요한 것은 같은 주장이 아니다.

### Langfuse Projection

- **기대 가치:** 동일 invocation의 input/output, metadata와 수동 annotation을 UI에서 살펴볼 수 있다.
- **의문:** 현재 범위가 소수 synthetic live proof와 수동 평가라면 기존 로컬 invocation evidence만으로 충분할 수 있다. 별도 SDK, 설정, 전송·검증 경계는 운영 복잡성을 만든다.
- **구분:** Langfuse 유무는 Review AI의 본질적 효용과 별개이며, 특정 observability 제품을 필수 전제로 삼을 이유가 입증된 것은 아니다.

## Smallest Useful Proof

기능을 더 확장하기 전에 다음과 같은 **작은 실험의 증거**가 먼저 필요하다.

1. 동일한 대표 incident에 대해 사람에게 **deterministic evidence + RemediationDraft만 제공한 경우**와 **Review AI 결과를 함께 제공한 경우**를 비교한다.
2. AI가 발견한 추가 evidence gap·우선순위·위험 또는 중요한 불확실성이 **실제 다음 행동이나 판단을 바꿨는지** 기록한다. 단순히 보기 좋게 요약한 것은 추가 가치와 구별한다.
3. 서로 다른 prompt/model/context를 실제로 선택해야 하는 상황에서만 `rubric_v1`과 baseline/candidate 비교가 결정을 더 명확하게 만드는지 시험한다.
4. 로컬 evidence를 읽는 방식과 Langfuse UI 방식을 비교해, 외부 투영 없이는 해결하기 어려운 문제와 실제 절약된 노력이 있는지 확인한다.

이는 검증 제안이지 이미 실행된 실험이나 채택된 새로운 acceptance 기준이 아니다. 적절한 사례 수·평가 방법·중단 기준은 별도 판단이 필요하다.

## Decision Record

- **현재 판단:** Review AI 및 평가·관찰 기능의 **실질적 가치는 아직 이 기록에서 입증되지 않았다**. "기능이 동작한다", "테스트가 통과한다", "코드가 정리됐다"는 사실만으로 유지·확대의 충분한 근거가 되지 않는다.
- **선택지:** 작은 실험에서 도움이 확인되면 필요한 최소 evaluation을 유지하고, 반복적인 비교 수요나 Langfuse의 고유 이익이 없으면 해당 부가 기능은 단순화·보류를 검토한다. 핵심 Review AI 자체도 추가 가치가 없다면 계속할 이유를 재평가한다.
- **기술적 경계:** 효용 의문이 있다고 해서 deterministic reliability truth, evidence binding, human approval, review output 안전 검증을 무단으로 제거하지 않는다. 기능 축소나 MVP acceptance 변경은 별도의 명시적 결정을 필요로 한다.
- **현행 목표와의 관계:** [MVP](../../../docs/mvp.md)는 실질적인 Agentic utility와 human evaluation의 proof를 요구한다. 이 기록은 그 목표를 수정하거나 달성했다고 주장하지 않고, **어떤 실증이 아직 필요한지**를 드러낸다.

## Historical Context

[PR #251](https://github.com/mols3131d/hmda-data-reliability/pull/251)은 2026-10-14에 squash merge됐다(merge commit `0cd51b9035f85e2f3e1d2f6c405e2ecaf668bea4`). 해당 PR은 주로 기존 evaluation 코드를 재배치·rename하고 Langfuse JSON 타입 비교 회귀를 수정했다. **머지는 해당 구현의 채택 이력일 뿐, Review AI 또는 평가·Langfuse 기능의 실효성을 증명하거나 사용자 의문을 철회한 사건이 아니다.**

이 문서는 의문과 기술적 판단을 보존하는 non-canonical archive다. 현재 계약은 [canonical Spec](../../../openspec/specs/reliability-agentic-review/spec.md), 현재 구현은 [source](../../../src/hmda_reliability/review_ai/evaluation/value.py)가 소유한다.
