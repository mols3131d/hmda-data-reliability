---
type: proposal
title: "Review AI Utility Evaluation Remediation and Simplification Proposal"
description: "PR #245의 merge blocker를 최소 변경으로 해소하고, decision-support와 human utility evaluation의 경계를 바로잡은 뒤 평가 인프라 감량을 별도 단계로 수행하는 후속 행동을 제안합니다."
tags:
  - "domain:review-ai"
  - "capability:reliability-agentic-review"
  - "pull-request"
  - "proposal"
  - "mvp"
  - "evaluation"
---

# Review AI Utility Evaluation Remediation and Simplification Proposal

## Decision

PR #245는 현재 merge 또는 OpenSpec archive 단계로 진행하지 않는다. 기존 [08 proposal](08-proposal-review-ai-next-milestones-and-mvp-completion.md)의 "merge-ready" 전제는 reviewed head `aaf9743d2adf8b654743bc3609fa248cc0a797c7`에서 발견된 F1-F3와 양립하지 않으므로, 이 제안서가 후속 행동의 기준을 대체한다.

다음 작업은 새로운 evaluation platform을 추가하는 일이 아니라, 다음 순서로 현재 PR의 utility proof를 작고 설명 가능한 형태로 바로잡는 일이다.

1. Review AI가 제공하는 domain semantic과 human evaluator가 판정하는 utility를 분리한다.
1. F1-F3을 기존 abstraction 안에서 해소하고 negative test로 고정한다.
1. MVP acceptance에 직접 필요하지 않은 quality-basis, proof-bundle, store, runner 계층을 별도 감량 작업으로 검토한다.
1. 위 변경이 검증된 뒤에만 실제 live human proof와 current-revision MVP 통합을 계획한다.

## Rationale

세 보고서의 판단은 서로 보완적이다.

| Evidence | Decision impact |
| --- | --- |
| [09 current-head review](09-review-review-ai-utility-evaluation-current-head.md) | F1-F3이 남아 있어 `compared / accept` evidence를 merge-ready utility proof로 승격할 수 없다. |
| [10 decision-support boundary assessment](10-report-review-ai-decision-support-boundary.md) | `utility_contributions`의 domain semantic은 유지하되, model-declared utility와 human-evaluated utility의 결합을 해제해야 한다. |
| [11 overengineering assessment](11-report-review-ai-overengineering-assessment.md) | blocker를 해결하는 과정에서 control, proof, persistence, runner 계층을 더 일반화하면 MVP 범위를 벗어난다. |

이 순서는 `docs/mvp.md`의 "useful, not merely valid"와 advisory boundary를 함께 지킨다. 모델은 사람의 다음 판단을 돕는 구조화된 내용을 제시할 수 있지만, 그 내용이 실제로 유용했는지는 versioned human rubric과 rationale이 판단한다. 같은 representative case를 비교한다는 주장도 실제 review input identity와 controlled variable이 닫혀 있을 때만 성립한다.

## Work Package 1: Restore Evaluation Authority

현재 `utility_contributions`는 유용한 domain signal이지만, 이름과 evaluation coupling 때문에 모델이 utility를 선언하고 evaluator가 그 선언의 존재를 다시 검증하는 구조가 된다. 이 작업은 output taxonomy를 전면 재설계하지 않고 ownership만 바로잡는다.

### Proposed changes

1. Runtime output의 `utility_contributions`와 관련 naming을 `decision_support` 또는 `decision_support_items`로 변경한다.
1. `evidence_gap`, `investigation_priority`, `remediation_critique`, `material_uncertainty`의 네 kind는 유지한다.
1. `HumanUtilityEvaluation`에서 contribution kind를 validity invariant로 사용하는 경로를 제거한다.
1. `UtilityControl.expected_contributions`, `UtilityProofCase.expected_contributions`, comparison evidence의 contribution-kind binding, positive control의 non-empty contribution requirement를 human utility pass/fail 조건에서 제거한다.
1. `rubric_v1`에 다섯 criterion의 0/1/2 score anchor를 versioned rubric data로 추가한다.
1. deterministic facts 또는 deterministic context gap을 자연어로 다시 말하지만 decision-support field는 채워진 output을 negative control로 추가한다.

### Acceptance criteria

- decision-support item의 존재나 종류만으로 `added_value` 또는 전체 utility `PASS`가 되지 않는다.
- evaluator는 전체 output, evidence awareness, bounded next action과 rationale을 기준으로 다섯 rubric score를 기록한다.
- deterministic fact 또는 context gap 재진술은 `added_value=0`으로 평가할 수 있고, 이 사례는 positive control을 통과하지 못한다.
- output digest와 invocation identity는 evaluation이 어떤 output을 평가했는지 계속 식별한다.

### Explicit non-goals

- `findings`, `uncertainties`, decision support를 하나의 union schema로 통합하지 않는다.
- LLM-as-a-judge, approval UI, experiment registry 또는 범용 evaluator framework를 도입하지 않는다.
- decision-support output에 mutation 또는 approval authority를 추가하지 않는다.

## Work Package 2: Close Current-Head Blockers

F1-F3은 Work Package 1과 같은 PR에서 해결할 수 있지만, 각각은 좁은 contract와 focused test로 끝낸다. 새로운 controlled-experiment framework나 failure orchestration layer는 만들지 않는다.

| Finding | Minimal change | Focused proof |
| --- | --- | --- |
| F1: same-case attribution | `HumanUtilityEvaluation`에 stable `review_input_digest`를 추가하고, representative source input identity, controlled variable, fixed input binding을 명시한다. | draft 또는 fixed input이 달라지는 baseline/candidate comparison은 `blocked` 또는 `inconclusive`가 되며 accept를 만들지 않는다. |
| F2: context overflow | bounded-context overflow를 전용 preflight exception으로 표현하고 service에서 stable failure code의 `INPUT_REJECTED`로 변환한다. | default context limit을 넘는 유효 input에서 provider와 evidence store가 호출되지 않고 예외가 service 밖으로 전파되지 않는다. |
| F3: provider-visible evidence mismatch | canonical prompt의 draft reference를 bounded selected evidence ID set으로 투영한다. | evidence가 `max_evidence`를 초과하는 input에서 prompt-visible evidence ID와 validator allowed ID가 동일하다. |
| F4: stale PR metadata | PR body가 갱신되는 같은 변경에서 `revision.head`를 body가 설명하는 exact head로 갱신한다. | PR 설명의 revision metadata가 검토·검증 대상으로 기록한 revision과 일치한다. |

`review_input_digest`는 무조건 전체 invocation digest를 뜻하지 않는다. prompt, model, context처럼 의도적으로 비교하는 변수까지 고정하면 change-under-test 자체를 비교할 수 없게 된다. 따라서 구현 전에 representative source input의 canonical 범위와 controlled variable의 identity를 먼저 명시하고, 비교에서 고정해야 할 요소만 digest binding에 포함한다.

## Work Package 3: Separate Simplification Decision

Work Package 1과 2가 끝난 뒤, 현재 MVP proof가 다음의 더 작은 shape로 표현될 수 있는지 별도 change unit에서 판단한다.

```text
AgenticReviewInput
        ↓
BoundedReviewContext
        ↓
AgenticReviewOutput + decision_support
        ↓
HumanUtilityEvaluation
        ↓
UtilityComparisonEvidence
```

우선 검토 대상은 `QualityBasisValidation`, control hierarchy, `UtilityProofCase`/`UtilityProofBundle`, dedicated create-only evidence store, synthetic proof runner다. 각 계층은 다음 질문에 "예"라고 답할 때만 유지한다.

> 이 계층이 없으면 `docs/mvp.md`의 Review Context, Agentic Utility, Quality Evaluation 또는 Change Comparison proof 중 하나를 재현·검토할 수 없게 되는가?

그렇지 않다면 test fixture, serialization projection 또는 기존 local artifact persistence로 낮추거나 제거한다. 이 감량 결정은 F1-F3 remediation에 섞지 않는다. 현재 PR에서 동시에 구조를 크게 바꾸면 attribution과 typed failure 수정의 검증 범위가 불필요하게 넓어진다.

## Sequence and Gates

1. **Reframe PR #245**: 이 제안서를 기준으로 기존 merge/archival 전제를 철회하고 PR description의 stale revision metadata를 정정한다.
1. **Implement boundary and blocker fixes**: Work Package 1과 F1-F3을 최소 변경으로 구현하고 focused regression tests를 추가한다.
1. **Validate current PR**: targeted Review AI tests, relevant type/lint checks, and a fresh independent review를 실행한다. F1-F3 negative path와 decision-support anti-proxy case를 실제로 재현한다.
1. **Merge decision**: 모든 blocker가 해소되고 evidence가 current head에 다시 묶였을 때만 merge와 OpenSpec sync를 판단한다.
1. **Simplification proposal**: merge 후 별도 change unit에서 Work Package 3을 실행하거나, 유지 근거를 짧게 기록한다.
1. **Live human proof**: 감량 결정 이후에만 actual provider invocation, human rubric evaluation, baseline/candidate comparison을 수집한다. synthetic runner 또는 offline fixture는 live human utility의 대체 증거로 취급하지 않는다.

## Merge Gate

PR #245를 merge-ready로 판단하려면 다음이 모두 충족되어야 한다.

- F1-F3의 focused tests가 존재하고 통과한다.
- baseline/candidate attribution이 stable review input identity와 declared controlled variable로 재구성된다.
- service preflight failure가 typed result로 닫히며 provider invocation 전에 fail-closed 한다.
- provider-visible evidence reference와 validator allowed evidence reference가 같은 bounded set을 사용한다.
- decision-support taxonomy는 human utility score의 proxy가 아니며, rubric anchor와 anti-restatement control이 이 경계를 검증한다.
- PR body의 revision metadata와 validation evidence가 동일한 current head를 가리킨다.
- fresh review가 changed head를 대상으로 수행되고, remaining limitation과 live-proof 미수행 사실을 구분해 기록한다.

이 gate는 live provider 품질이나 운영 MTTR 개선을 이미 증명했다는 뜻이 아니다. 그것은 다음 live human proof 단계의 질문이다. 여기서 증명할 것은 MVP가 요구하는 작은 evaluation contract가 잘못된 attribution, preflight crash, evidence-reference mismatch, self-referential proxy 없이 작동한다는 사실이다.
