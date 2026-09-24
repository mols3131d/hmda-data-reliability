---
type: report
title: "PR #245 Overengineering Assessment"
description: "PR #245의 MVP utility proof 구현에서 유지해야 할 핵심과 줄여야 할 평가 인프라 복잡성을 구분합니다."
tags:
  - "domain:review-ai"
  - "capability:reliability-agentic-review"
  - "mvp"
  - "complexity"
---

# PR #245 Overengineering Assessment

> [!IMPORTANT]
> PR #245의 핵심 제품 방향은 유지할 가치가 있지만, utility를 증명하기 위한 평가 인프라는 현재 MVP 요구보다 무거워진 부분이 있습니다. 특히 quality-basis/control 계층, proof bundle 계층, 별도 create-only evidence store와 큰 synthetic runner는 단순한 human utility comparison을 작은 evaluation framework로 확장하고 있습니다. 이후 수정에서는 finding을 해결한다는 이유로 abstraction을 더 추가하기보다 평가 구조를 줄이는 것을 우선해야 합니다.

- **Target** — [PR #245 · `feat(review-ai): prove MVP utility evaluation`](https://github.com/mols3131d/hmda-data-reliability/pull/245)
- **Assessed revision** — `af9d25eae1ae9c3c03ae663407e91b020f829b40`
- **Related review** — [`09-review-review-ai-utility-evaluation-current-head.md`](09-review-review-ai-utility-evaluation-current-head.md)

## MVP Boundary

현재 MVP가 Review AI에서 증명해야 하는 본질은 다음 네 가지다.

1. incident 주변의 필요한 evidence를 bounded context로 제공하고 provenance를 보존한다.
1. AI output이 deterministic facts나 `RemediationDraft`의 단순 재진술을 넘어 사람의 다음 판단에 최소 하나의 추가 가치를 제공한다.
1. 사람이 versioned rubric의 다섯 기준으로 utility를 평가할 수 있다.
1. 같은 representative case에서 baseline과 candidate를 비교하고 채택 판단과 근거를 남길 수 있다.

이 범위에서는 production-grade evaluation platform, 자동 LLM judge, 범용 experiment framework가 필요하지 않다. 따라서 구현 복잡성은 위 네 proof를 직접 강화하는 경우에만 정당화하는 것이 맞다.

## Current Complexity Signal

현재 PR은 39개 파일에서 약 `+4,262/-22` 변경이며, 그중 Inbox artifact가 약 1,347줄이다. Canonical implementation 쪽에서도 utility evaluation 전용 구조가 빠르게 커졌다.

- `src/hmda_reliability/review_ai/evaluation.py` — 약 603줄
- `scripts/run_review_ai_utility_proof.py` — 약 374줄
- `src/hmda_reliability/review_ai/evaluation_store.py` — 약 127줄
- `tests/review_ai/test_utility_evaluation.py` — 약 831줄

줄 수 자체가 defect는 아니다. 다만 "사람이 두 output을 다섯 기준으로 평가하고 같은 case에서 비교한다"는 MVP 문제에 비해 별도 domain model과 persistence semantics가 많이 생겼다는 신호로 봐야 한다.

## Keep

다음 요소는 MVP acceptance와 직접 연결되므로 유지하는 편이 낫다.

### Bounded Review Context

`BoundedReviewContext`는 raw data나 전체 로그를 무제한으로 넘기지 않고 incident 주변 evidence를 결정론적으로 선택하며 provenance와 gap을 유지한다. 이는 evidence-bound AI와 replayability에 직접 필요하다.

### Structured Utility Contributions

`evidence_gap`, `investigation_priority`, `remediation_critique`, `material_uncertainty`는 "유용함"을 자연어 주장으로만 남기지 않고 사람이 검토할 구조로 만든다. 종류도 네 개로 제한되어 있어 현재 수준은 과하지 않다.

### Five-Criterion Human Rubric

`added_value`, `actionability`, `evidence_awareness`, `uncertainty_handling`, `prioritization`은 MVP acceptance에 직접 포함된다. 자동 judge 대신 human score와 rationale을 남기는 것도 프로젝트 방향과 맞는다.

### Small Baseline/Candidate Comparison

같은 representative case에서 baseline과 candidate score를 비교하고 `change_under_test`, human decision과 rationale을 남기는 기능 자체는 필요하다. 다만 이를 지원하는 domain model의 수는 줄일 수 있다.

## Simplify

### Quality-Basis and Control Hierarchy

현재 구현은 `UtilityControl`, `ControlValidationResult`, `QualityBasisValidation`을 별도 domain model로 만들고 positive/negative control의 결과를 durable quality basis로 승격한다. restatement나 hedging 사례가 rubric sanity check로 유용한 것은 맞지만, MVP에서는 이를 production model로 보존하지 않고 test fixture로 유지해도 핵심 위험을 상당 부분 막을 수 있다.

권장 방향은 다음과 같다.

- positive control과 restatement/hedging negative case는 tests에 유지한다.
- control validation 결과를 별도 runtime/domain evidence hierarchy로 만들 필요가 있는지는 다시 판단한다.
- rubric이 최소 판별력을 갖는다는 사실은 focused test로 증명하고, 실제 utility proof는 human evaluation과 comparison에 집중한다.

### Utility Proof Case and Bundle

`UtilityProofCase`와 `UtilityProofBundle`은 이미 `HumanUtilityEvaluation`과 `UtilityComparisonEvidence`가 가진 case, revision, output digest, comparison link를 다시 묶는다. 현재 단계에서는 proof를 설명하기 위해 proof wrapper를 한 층 더 만드는 구조가 될 수 있다.

가능하면 `HumanUtilityEvaluation`과 `UtilityComparisonEvidence`가 필요한 identity와 digest를 직접 소유하고, 별도 bundle은 제거하거나 단순 serialization projection으로 축소하는 편이 낫다.

### Dedicated Create-Only Evidence Store

`UtilityEvidenceStore`는 temp file, `fsync`, hard link, duplicate protection, directory `fsync`, rollback과 custom exception을 구현한다. 이 수준의 write semantics는 중요한 audit log나 production durability에는 의미가 있지만, 현재 MVP의 local human-reviewable comparison evidence에는 비용 대비 이점이 작다.

기존 artifact persistence owner가 있다면 재사용하고, 없다면 MVP에서는 작은 JSON evidence write로 충분한지 먼저 검토한다. create-only 보장이 실제 acceptance에 필요한 경우에만 별도 persistence abstraction을 유지한다.

### Synthetic Proof Runner

`run_review_ai_utility_proof.py`는 synthetic baseline/candidate output과 human score를 코드에서 직접 만들고 `ACCEPT` decision까지 고정한다. 이 runner는 실제 human utility를 증명하지 않으며, 스스로도 contract/fixture validation 용도라고 한정한다.

따라서 runner가 증명하는 대부분의 내용이 deterministic tests와 중복된다면 다음 중 하나로 축소하는 편이 낫다.

- representative fixture를 tests에서만 검증한다.
- 사람이 실제 proof를 수집할 때 필요한 최소 command만 남긴다.
- JSON/Markdown rendering demonstration이 필요하면 작은 fixture script로 제한한다.

runner 자체를 MVP proof처럼 키우지 않는다.

### Hedging as a Normative Contract

과도한 면책형 답변이 유용하지 않다는 문제의식은 타당하다. 다만 특정 hedging pattern을 OpenSpec의 강한 normative requirement와 durable control hierarchy로 승격하면 한 대표 실패 유형이 평가 architecture를 끌고 가게 된다.

MVP에서는 `actionability`와 `prioritization`이 낮은 hedging output이 human rubric을 통과하지 못한다는 test fixture로 충분한지 우선 검토한다. 실제 운영에서 반복적으로 중요한 failure mode로 확인될 때 더 강한 contract로 승격해도 늦지 않다.

## PR Scope

PR body에는 utility proof 외에 Rulesync `eli5` asset 도입, 설명용 ELI5 보고서와 후속 milestone proposal까지 포함되어 있다. Inbox 문서는 canonical runtime complexity를 직접 늘리지는 않지만 review surface와 변경 목적의 경계를 넓힌다.

이 PR의 핵심 질문은 "Review AI가 bounded evidence를 바탕으로 사람에게 추가 utility를 제공하고 이를 작게 평가·비교할 수 있는가"로 유지하는 편이 좋다. 이후 작업에서 직접 필요하지 않은 agent asset 또는 설명용 부수 변경은 별도 change unit으로 분리하는 것을 고려한다.

## Minimal Target Shape

MVP 관점에서 필요한 구조는 다음 정도로 줄일 수 있다.

```text
AgenticReviewInput
        ↓
BoundedReviewContext
        ↓
AgenticReviewOutput
  + utility_contributions
        ↓
HumanUtilityEvaluation
  - case_id/version
  - review_input_digest
  - invocation_id
  - output_digest
  - five rubric scores + rationale
        ↓
UtilityComparisonEvidence
  - baseline/candidate evaluation identity
  - criterion deltas
  - change_under_test
  - decision + rationale
```

이 구조에서 positive/negative/hedging 사례는 test fixture로 남기고, persistence는 기존 local artifact 방식 또는 단순 JSON evidence로 처리할 수 있다.

## Implication for Review Findings

[`09-review-review-ai-utility-evaluation-current-head.md`](09-review-review-ai-utility-evaluation-current-head.md)의 F1–F3도 새 framework를 추가하지 않고 작게 해결하는 것이 중요하다.

- **F1** — 별도의 controlled-experiment framework를 만들기보다 `HumanUtilityEvaluation`에 stable `review_input_digest`를 추가하고 baseline/candidate의 동일성을 검증하는 방향을 우선한다. Prompt/model/context처럼 의도적으로 비교하는 요소가 digest에 포함되어서는 안 되는 경우에는 "representative source input"의 canonical 범위를 작게 정의한다.
- **F2** — bounded-context overflow를 전용 exception으로 표현하고 service에서 typed `INPUT_REJECTED`로 변환한다. 별도 failure framework는 만들지 않는다.
- **F3** — provider-visible `draft.evidence_refs`를 bounded selected evidence set과 정합하게 투영하고 integration test 한두 개로 고정한다.

Finding을 해소한다는 이유로 새로운 abstraction layer, registry 또는 generalized experiment model을 추가하면 이번 감량 목표와 충돌한다.

## Recommended Direction

PR #245는 폐기보다 감량이 적절하다. 제품 가치에 직접 연결되는 bounded context, utility contribution, human rubric과 baseline/candidate comparison은 유지하고, 평가 시스템 자체를 증명하기 위해 생긴 계층은 줄이는 것이 좋다.

우선순위는 다음과 같다.

1. OpenSpec에서 MVP에 반드시 필요한 evaluation contract와 test-only discrimination fixture를 다시 구분한다.
1. `HumanUtilityEvaluation` + `UtilityComparisonEvidence` 중심으로 모델을 축소할 수 있는지 검토한다.
1. control/quality-basis/proof-bundle/store/runner 중 acceptance에 직접 필요하지 않은 계층을 제거하거나 test/support code로 낮춘다.
1. 09 review의 F1–F3를 최소 변경으로 해결한다.
1. 감량 후 같은 MVP proof를 더 작은 conceptual surface로 설명하고 재실행할 수 있는지 재검토한다.

목표는 코드 줄 수 자체를 줄이는 것이 아니라, **MVP utility proof에 필요한 신뢰성은 유지하면서 이해·검증·수정해야 할 개념 수를 줄이는 것**이다.
