---
type: report
title: "Review AI Decision-Support Boundary Assessment"
description: "PR #245의 utility_contributions가 실제 Review AI 출력 계약과 human utility evaluation 사이에서 적절한 경계를 갖는지 검토하고 최소 수정 방향을 제안합니다."
tags:
  - "domain:review-ai"
  - "capability:reliability-agentic-review"
  - "pull-request"
  - "report"
  - "llmops"
  - "evaluation"
---

# Review AI Decision-Support Boundary Assessment

## Executive Summary

`utility_contributions`가 표현하려는 네 가지 정보(`evidence_gap`, `investigation_priority`, `remediation_critique`, `material_uncertainty`)는 Review AI가 단순 사실 재진술을 넘어 사람의 다음 판단을 돕기 위해 필요한 의미를 상당 부분 잘 포착한다. 따라서 이 taxonomy 자체를 제거하는 것은 권장하지 않는다.

문제는 현재 이름과 평가 결합 방식이다. `utility_contributions`는 모델이 자신의 출력 중 무엇이 "utility"인지 직접 선언하는 형태이고, evaluation layer가 `contribution_kinds`, `expected_contributions`, positive control의 non-empty contribution 조건까지 검증한다. 이 구조는 실제 사람의 유용성 판단과 모델이 출력한 utility label 사이의 경계를 흐린다.

또한 현재 representative candidate의 일부 contribution은 새 추론이라기보다 `BoundedReviewContext`가 이미 결정론적으로 생성한 gap을 다시 표현한다. `evidence_gap`은 `missing_evidence`, `material_uncertainty`는 `unconfirmed_context`와 겹칠 수 있다. 따라서 contribution field의 존재 자체를 added value의 증거로 취급하면 "deterministic context를 다시 말하는 것"이 utility처럼 보이는 proxy failure가 생길 수 있다.

권고는 삭제가 아니라 **경계 수정**이다.

- Runtime output에서는 네 가지 종류를 `decision_support` 같은 domain semantic으로 유지한다.
- Human utility evaluation은 decision-support 종류의 존재를 pass 조건이나 expected oracle로 사용하지 않는다.
- `rubric_v1`은 각 criterion의 0/1/2 score anchor를 명시해 실제 human judgment가 무엇을 의미하는지 고정한다.
- 단순 deterministic fact뿐 아니라 deterministic context gap의 재진술도 `added_value=0`이 될 수 있어야 한다.
- PR #245에서는 output 전체 재설계까지 확장하지 않고 이 경계만 최소한으로 정리하는 것이 적절하다.

이 문서는 [09 current-head review](09-review-review-ai-utility-evaluation-current-head.md)의 finding 번호를 재사용하지 않는 보조 설계 검토다. 해당 리뷰의 F1-F4와 별개로, utility proof의 의미적 타당성을 강화하기 위한 추가 판단 근거를 기록한다.

## Scope

검토 대상은 PR #245 head `af9d25eae1ae9c3c03ae663407e91b020f829b40`의 다음 경계다.

- [`AgenticReviewOutput`](../../src/hmda_reliability/review_ai/contracts.py)의 `utility_contributions`
- [`BoundedReviewContext`](../../src/hmda_reliability/review_ai/context.py)의 context gap
- [`HumanUtilityEvaluation`, `UtilityControl`, `UtilityComparisonEvidence`, `UtilityProofCase`](../../src/hmda_reliability/review_ai/evaluation.py)의 utility binding
- [`run_review_ai_utility_proof.py`](../../scripts/run_review_ai_utility_proof.py)의 representative fixture
- [`reliability-agentic-review` OpenSpec delta](../../openspec/changes/review-ai-utility-evaluation/specs/reliability-agentic-review/spec.md)

검토 질문은 하나다.

> `utility_contributions`가 Review AI가 사람에게 제공할 domain output을 표현하는 필드인지, 아니면 사람 평가자가 판정해야 할 utility를 모델이 스스로 선언하는 필드인지 명확히 분리되어 있는가?

## Current Design

현재 output contract는 기존 `review_summary`, `findings`, `uncertainties`, `advisory_recommendation`에 다음 네 종류의 `utility_contributions`를 추가한다.

| Kind | Intended role | Existing overlap |
| --- | --- | --- |
| `evidence_gap` | 추가 확인이 필요한 증적 공백 | `findings(kind=omission)`, `BoundedReviewContext.missing_evidence` |
| `investigation_priority` | 다음 조사 우선순위 | 기존 구조에서 가장 독립적인 역할 |
| `remediation_critique` | RemediationDraft의 위험·누락 비판 | `findings(kind=concern/omission)` |
| `material_uncertainty` | 현재 증적으로 확정할 수 없는 핵심 불확실성 | `findings(kind=uncertainty)`, `uncertainties`, `unconfirmed_context` |

이 taxonomy는 "무엇을 발견했는가"보다 "사람의 다음 판단에 어떤 형태로 도움을 주는가"를 더 직접 표현한다는 장점이 있다. 특히 `investigation_priority`와 `remediation_critique`는 generic finding보다 Review AI의 역할을 분명하게 만든다.

반면 현재 evaluation contract는 이 domain output을 utility proof의 oracle 일부로 끌어들인다.

- `HumanUtilityEvaluation.contribution_kinds`
- `UtilityControl.expected_contributions`
- `ControlValidationResult.contribution_kinds`
- `UtilityComparisonEvidence.baseline_contribution_kinds`
- `UtilityComparisonEvidence.candidate_contribution_kinds`
- `UtilityProofCase.expected_contributions`
- positive control은 실제 contribution이 하나도 없으면 invalid

결과적으로 "어떤 decision-support category가 출력되었는가"와 "그 출력이 실제로 사람에게 유용했는가"가 같은 proof graph 안에서 강하게 결합된다.

## Findings

### Domain Semantics Are Useful

네 종류의 semantic은 모두 제거할 대상이 아니다. MVP는 deterministic facts를 다시 말하는 것 이상의 값을 요구하고, 현재 taxonomy는 그 기대를 provider output에 구체적으로 드러낸다. 특히 조사 우선순위와 remediation critique는 기존 `findings`만으로 표현할 때보다 소비자가 의도를 쉽게 구분할 수 있다.

따라서 `utility_contributions`를 단순 삭제하고 모든 내용을 `findings`와 `uncertainties`에 흡수하면 output contract는 더 단순해지지만 Review AI가 제공해야 하는 decision aid의 구조도 약해진다.

### Utility Is Not a Model-Owned Property

문제는 `utility`라는 이름이다. Provider가 신뢰성 있게 선언할 수 있는 것은 "이 항목은 evidence gap이다", "이 항목은 investigation priority다"와 같은 task-level semantic이다. "이 항목은 사람에게 유용한 contribution이다"는 평가는 별도의 human rubric이 소유해야 한다.

현재 이름은 다음 두 문장을 하나의 필드에 겹친다.

```text
Model-owned claim: 이 항목은 investigation priority다.
Evaluator-owned claim: 이 항목은 실제로 유용한 기여다.
```

이 둘을 분리하지 않으면 모델이 evaluation vocabulary를 직접 출력하고 evaluation record가 그 vocabulary의 존재를 다시 검증하는 자기참조적 구조가 된다.

### Deterministic Gap Restatement Can Look Like Added Value

`BoundedReviewContext`는 provider 호출 전에 `missing_evidence`와 `unconfirmed_context`를 결정론적으로 생성한다. 현재 구현은 required source가 없으면 missing gap을 만들고, 제공된 Evidence가 root cause를 확정하지 못한다는 `root_cause` unconfirmed gap도 추가한다.

대표 candidate는 다음과 같은 contribution을 포함한다.

```text
evidence_gap:
  Lineage evidence is missing before root-cause attribution.

material_uncertainty:
  The supplied profile does not establish root cause.
```

이 둘은 새로운 model synthesis가 될 수도 있지만 현재 fixture에서는 이미 input context에 존재하는 gap을 다시 자연어로 표현한 것으로 해석할 여지가 크다. 따라서 `utility_contributions`가 채워졌다는 사실만으로는 `added_value`의 근거가 될 수 없다.

이 문제는 MVP의 원래 문제 정의와 직접 연결된다. "deterministic facts를 다시 말하는 것"이 부족하다면 "deterministically generated context gaps를 다시 말하는 것" 역시 자동으로 utility가 되어서는 안 된다.

### Semantic Ownership Is Duplicated

현재 uncertainty는 최소 세 output surface에서 표현할 수 있다.

```text
findings(kind="uncertainty")
uncertainties
utility_contributions(kind="material_uncertainty")
```

여기에 input의 `unconfirmed_context`까지 포함하면 producer와 evaluator가 같은 의미를 여러 위치에서 해석해야 한다. `evidence_gap`과 `remediation_critique`도 각각 omission/concern finding과 상당히 겹친다.

이 중복은 당장 correctness defect라고 단정할 수는 없지만 provider output의 일관성과 향후 evaluation 비교의 noise를 높일 수 있다. PR #245에서 전체 output schema를 재설계하는 것은 범위가 크므로, 이번 change에서는 evaluation coupling을 먼저 줄이고 장기적으로 output taxonomy를 통합할지 별도로 판단하는 편이 안전하다.

### Current Rubric Needs Stronger Anchors

현재 `rubric_v1`은 다섯 criterion과 0-2 범위, pass threshold를 고정하지만 score 의미를 충분히 고정하지 않는다. 실제 live human proof에서는 evaluator마다 `2`의 의미가 달라질 수 있다.

최소한 다음 수준의 score anchor가 versioned rubric에 필요하다.

| Criterion | 0 | 1 | 2 |
| --- | --- | --- | --- |
| `added_value` | deterministic facts/context gap의 실질적 재진술 | 일부 새로운 synthesis가 있으나 다음 판단을 거의 좁히지 못함 | evidence-backed synthesis/critique가 다음 판단이나 조사를 실질적으로 좁힘 |
| `actionability` | 구체적 다음 행동이 없거나 전수 조사 같은 포괄적 지시 | 실행 가능한 행동이 있으나 범위·근거가 약함 | bounded next action이 구체적이고 근거와 연결됨 |
| `evidence_awareness` | 근거를 무시·과장하거나 fact/gap을 구분하지 못함 | 근거를 사용하지만 provenance 또는 gap 구분이 약함 | 확정 사실, 제공 근거, 미확인 영역을 명확히 구분함 |
| `uncertainty_handling` | 과신하거나 모든 것이 불확실하다는 blanket hedging | 불확실성을 언급하지만 판단 영향이 불명확함 | 중요한 불확실성, 영향, 해소에 필요한 evidence가 구체적임 |
| `prioritization` | 우선순위가 없거나 모든 것을 우선시함 | 순서는 있으나 근거가 약함 | 영향·근거에 연결된 명확한 조사 순서를 제시함 |

이 anchor는 모델 output schema보다 evaluation authority에 속한다.

## Recommended Boundary

권장 구조는 다음과 같다.

```text
AgenticReviewOutput
├─ review_summary
├─ findings
├─ uncertainties
├─ decision_support
│  ├─ evidence_gap
│  ├─ investigation_priority
│  ├─ remediation_critique
│  └─ material_uncertainty
└─ advisory_recommendation

                ↓ full output

HumanUtilityEvaluation
├─ added_value
├─ actionability
├─ evidence_awareness
├─ uncertainty_handling
└─ prioritization
```

핵심 원칙은 다음과 같다.

1. 모델은 domain semantic을 출력한다.
2. 모델은 자신의 output이 "유용하다"고 판정하지 않는다.
3. evaluator는 전체 output을 보고 utility를 판정한다.
4. decision-support field의 존재나 종류는 human score의 대체 지표가 아니다.
5. output digest가 전체 output identity를 보존하므로 evaluation evidence를 특정 output에 묶는 데 별도 contribution-kind oracle은 필요하지 않다.

## Minimal Change For PR 245

PR #245에서 가장 작은 coherent change는 다음 정도다.

1. `utility_contributions`와 관련 type을 `decision_support` 또는 `decision_support_items` 중심의 domain naming으로 변경한다.
2. 네 kind는 유지한다. taxonomy 재설계는 별도 후속 작업으로 둔다.
3. `HumanUtilityEvaluation`의 `contribution_kinds`를 utility validity invariant에서 제거한다.
4. `UtilityControl.expected_contributions`, comparison의 baseline/candidate contribution kinds, `UtilityProofCase.expected_contributions`를 필수 proof binding에서 제거한다.
5. positive control의 "non-empty contribution required" 조건을 제거한다. Positive/negative 판정은 human rubric score와 rationale이 소유한다.
6. `rubric_v1`에 각 criterion의 0/1/2 anchor를 추가한다.
7. "decision-support field는 채워져 있지만 deterministic fact/context gap을 다시 말할 뿐인 output"을 negative control에 추가해 superficial schema compliance가 PASS가 되지 않음을 검증한다.
8. 전체 output identity는 기존 output digest와 fixture/invocation identity로 계속 보존한다.

이 변경은 bounded context, deterministic reference guard, create-only evidence store, same-case comparison 같은 #245의 핵심 구조를 버리지 않는다. 평가 authority만 더 명확하게 분리한다.

## Alternatives

| Option | Benefit | Cost / risk | Assessment |
| --- | --- | --- | --- |
| 현재 `utility_contributions` 유지 | 구현 변경 없음 | model-declared utility와 human-evaluated utility가 결합됨 | 비추천 |
| 필드 완전 삭제 후 `findings` 재사용 | 단순한 schema | investigation priority와 remediation critique의 domain 의미가 약해짐 | 과도한 축소 |
| `decision_support`로 rename하고 evaluation decouple | domain semantic 유지, 평가 독립성 강화 | 제한된 migration 비용 | **권장** |
| `findings`/`uncertainties`/decision support를 하나의 typed item union으로 재설계 | 중복 최소화 | PR #245 범위를 크게 확장 | 후속 후보 |

## External Evaluation Evidence

외부 자료는 repository contract의 authority가 아니라 설계 판단을 보강하는 참고 근거로 사용한다.

- OpenAI, [A shared playbook for trustworthy third party evaluations](https://openai.com/index/trustworthy-third-party-evaluations-foundations/): evaluation이 어떤 claim을 검증하는지 명시하고, reward hacking처럼 scorer나 harness의 shortcut으로 점수를 얻는 위험을 별도로 검토해야 한다고 설명한다. 현재 contribution-presence와 utility score의 결합은 의도한 utility보다 schema compliance를 proxy로 만들 수 있으므로 이 위험과 관련된다.
- OpenAI, [How evals drive the next chapter in AI for businesses](https://openai.com/index/evals-drive-next-chapter-of-ai/): rubric이 구체성을 주지만 표면적인 항목을 과도하게 강조하면 본래 목표를 놓칠 수 있으며 domain expert 판단이 계속 필요하다고 설명한다.
- OpenAI, [Measuring the performance of our models on real-world tasks](https://openai.com/index/gdpval/): 전문가가 결과물을 blind comparison하고 상세 rubric으로 평가하며, 자동 grader를 expert judgment의 완전한 대체로 사용하지 않는다. Live Human Proof에서도 baseline/candidate identity를 가능하면 숨기고 전체 output을 비교하는 방식이 적합하다는 참고가 된다.
- Anthropic, [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents): evaluator와 grader가 unintended shortcut에 견고해야 하고, structured rubric과 human calibration이 중요하다고 설명한다.

## Decision

현재 판단은 다음과 같다.

- **Keep:** 네 가지 decision-support semantic.
- **Change:** `utility_contributions`라는 model-owned naming.
- **Decouple:** contribution 종류의 존재와 human utility pass/fail.
- **Strengthen:** `rubric_v1` score anchor와 anti-proxy negative control.
- **Defer:** 전체 review item taxonomy 통합.

따라서 이 설계 문제는 "필드가 쓸모없다"가 아니라 **쓸모있는 domain signal이 잘못된 evaluation boundary에 놓여 있다**고 보는 것이 정확하다. PR #245의 utility proof를 더 강하게 만들려면 모델이 utility를 선언하게 하는 것이 아니라, 모델은 decision-support output을 만들고 human evaluation이 그 결과의 실제 utility를 독립적으로 판정해야 한다.
