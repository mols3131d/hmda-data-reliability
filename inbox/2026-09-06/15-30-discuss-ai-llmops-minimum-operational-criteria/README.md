---
type: discuss
title: "Minimum Criteria for Working LLMOps"
description: "LLMOps가 정상 작동한다고 판단하기 위한 최소 feedback loop와 완료 기준을 토론한다."
status: "completed"
discussion:
  id: "2026-09-06-llmops-minimum-operational-criteria"
  type: explore
  exchange: iterative
  cadence: manual
  execution: live
  phase: sublation
  decision_authority: human
  topic: blocked-and-inconclusive-evaluation
tags:
  - ai-engineering
  - llmops
---

## Goal

현재 프로젝트에서 “LLMOps가 정상 작동한다”고 인정할 수 있는 가장 작은 feedback loop와 검증 가능한 완료 기준을 도출한다. 특정 플랫폼이나 자동화 수준이 아니라 실제 AI review의 품질을 반복 평가하고 다음 변경 판단에 사용할 수 있는 최소 운영 능력을 기준으로 삼는다.

## Session

- **Initial** - 2026-09-06 15:30–15:55 KST, 25 minutes
- **Continuation** - 2026-09-06 16:11–16:25 KST
- **Continuation 2** - 2026-09-06 16:30 KST–2026-09-07 T7 closure
- **Reopen reason** - 사용자가 첫 수렴 이후에도 같은 session에서 토론을 계속하도록 명시해 T1 결과를 유지한 채 최소 proof와 ongoing operation을 계속 stress-test한다.

## Topic

### T1. Minimum Operating Criteria

- **Status** - completed
- **Result** - `Traceable → Quality-evaluable → Replayable → Feedback-consumed`의 네 gate와 representative failure/edge quality case의 end-to-end proof로 수렴했다.

### T2. Non-vacuous Quality Signal

- **Status** - completed
- **Result** - 실제 traced model `FAIL`은 필수가 아니다. Candidate를 보기 전에 고정한 versioned case/rubric이 bounded negative control을 `FAIL`, compliant control을 `PASS`로 구별하고 actual traced baseline/candidate를 같은 rubric으로 평가·비교하면 non-vacuous proof로 충분하다.

### T3. Durable Feedback Evidence

- **Status** - completed
- **Result** - `Feedback-consumed`는 durable decision record로 증명한다. Record는 quality basis, baseline/candidate invocation identities, 재구성 가능한 change-under-test, `accept/reject/no-change`와 짧은 rationale를 연결한다. Existing provenance diff가 change-under-test를 유일하게 식별하면 별도 delta artifact는 필요 없다.

### T4. Versioned Case Retention

- **Status** - completed
- **Result** - authored case definition은 stable case identity, replayable input definition과 versioned quality-basis reference를 소유한다. Rubric과 bounded control discrimination proof는 별도 quality-basis validation evidence가 소유할 수 있다. Controls가 case-specific semantics에 결합된 경우에만 해당 control recipe를 case dependency로 versioning한다. 파일 수나 registry는 최소 기준이 아니다.

### T5. Operational Re-evaluation Trigger

- **Status** - completed
- **Result** - ongoing operation은 모든 commit에 live eval을 거는 것이 아니라 candidate acceptance 시 `applicable / not-applicable`을 판정하는 gate로 증명한다. Review AI output/quality semantics에 material한 candidate면 retained case comparison이 acceptance 전에 소비되어야 하고, 아니라면 생략 이유가 기존 change evidence에서 재구성 가능해야 한다. 알려진 provider/model behavior change도 새 candidate acceptance로 취급하되 자동 drift 탐지는 최소 기준에서 제외한다.

### T6. Failure Intake And Regression Promotion

- **Status** - completed
- **Result** - known material failure는 coverage-preserving intake를 거친다. 원 evidence를 연결하고 materiality와 existing coverage를 판단한 뒤, 기존 case가 동일 risk를 재현하면 그 case에 evidence를 연결하고, coverage gap만 새 retained regression knowledge로 승격한다. 재현 불가한 material failure는 original evidence, blocker/rationale, revisit condition을 durable하게 남긴다. Material은 task usefulness 또는 candidate quality decision을 바꿀 수 있는 expectation 위반/누락으로 제한한다.

### T7. Blocked And Inconclusive Evaluation

- **Status** - completed
- **Question** - applicable candidate인데 provider invocation, case replay 또는 quality judgment가 비교 가능한 evidence를 만들지 못했을 때 최소 운영 gate는 어떻게 동작해야 하는가?
- **Result** - Applicable candidate는 admissible quality decision evidence 없이 accept할 수 없다. Candidate-caused material regression이라는 admissible attribution evidence가 있으면 human `reject`의 근거가 될 수 있고, comparison validity 또는 attribution이 성립하지 않으면 `blocked/inconclusive`로 acceptance와 baseline promotion을 멈춘다. Blocker evidence는 candidate/applicability, case/basis, failure/attribution, baseline continuity와 revisit condition을 직접 또는 durable evidence chain으로 유일하게 재구성할 수 있어야 한다. Blocker 해소 후 같은 candidate를 다시 평가할 수 있지만 current comparability는 새로 성립시켜야 한다.

## Current State

최소 기준은 **readiness proof**와 **ongoing operational discipline**으로 구분된다.

Readiness는 retained case/validated quality basis를 이용한 traced baseline/candidate compare와 durable human decision 한 사이클로 증명한다. Ongoing operation은 candidate acceptance applicability gate, blocked/inconclusive fail-closed 처리와 known-failure intake를 통해 quality evidence가 다음 변경에서 재사용되도록 한다.

Failure intake는 failure occurrence와 case를 1:1로 만들지 않는다. Existing coverage가 있으면 원 failure evidence를 그 case와 연결한다. Coverage gap만 새 case/dependency로 승격한다. Deferral은 영구 면제가 아니며 동일 failure 재발 또는 관련 quality-basis/input-boundary 변경 때 다시 검토한다.

`accept`된 candidate만 다음 comparison의 baseline이 된다. `reject/no-change`와 `blocked/inconclusive`에서는 기존 accepted baseline lineage가 유지된다. 별도 mutable baseline registry는 필수가 아니며 durable decision chain과 invocation identities로 current accepted baseline을 유일하게 재구성할 수 있으면 충분하다. Blocked 동안 다른 candidate가 accept됐다면 재평가 시 current accepted baseline을 다시 resolve한다.

`blocked/inconclusive`는 waiver가 아니다. Applicable candidate는 blocker 해소와 current valid comparable evidence 확보 전 accept할 수 없다. Baseline retention은 기존 baseline의 현재 quality 또는 operational availability를 보증하지 않는다.

## References

- [`docs/VISION.md`](../../../docs/VISION.md)
- [`docs/mvp.md`](../../../docs/mvp.md)
- [`docs/domains/review-ai.md`](../../../docs/domains/review-ai.md)
- [`docs/domains/runtime-ai.md`](../../../docs/domains/runtime-ai.md)
- [`docs/domains/reliability.md`](../../../docs/domains/reliability.md)
- [`docs/development/test-design.md`](../../../docs/development/test-design.md)
- [`openspec/specs/reliability-agentic-review/spec.md`](../../../openspec/specs/reliability-agentic-review/spec.md)
- [`openspec/specs/reliability-evaluation-report/spec.md`](../../../openspec/specs/reliability-evaluation-report/spec.md)
- [`scripts/run_agentic_review_live.py`](../../../scripts/run_agentic_review_live.py)
- [`tests/review_ai/conftest.py`](../../../tests/review_ai/conftest.py)
- [`tests/review_ai/test_validator.py`](../../../tests/review_ai/test_validator.py)
- [`turns/001-a.md`](turns/001-a.md)
- [`turns/002-b.md`](turns/002-b.md)
- [`turns/003-a.md`](turns/003-a.md)
- [`turns/004-b.md`](turns/004-b.md)
- [`turns/005-a.md`](turns/005-a.md)
- [`turns/006-b.md`](turns/006-b.md)
- [`turns/007-a.md`](turns/007-a.md)
- [`turns/008-b.md`](turns/008-b.md)
- [`turns/009-a.md`](turns/009-a.md)
- [`turns/010-b.md`](turns/010-b.md)
- [`turns/011-a.md`](turns/011-a.md)
- [`turns/012-b.md`](turns/012-b.md)
- [`turns/013-a.md`](turns/013-a.md)
- [`turns/014-b.md`](turns/014-b.md)
- [`turns/015-a.md`](turns/015-a.md)
- [`turns/016-b.md`](turns/016-b.md)
- [`turns/017-a.md`](turns/017-a.md)
- [`turns/018-b.md`](turns/018-b.md)
- [`turns/019-a.md`](turns/019-a.md)
- [`turns/020-b.md`](turns/020-b.md)

## Synthesis

### Readiness Minimum

1. **Traceable** - baseline/candidate run을 evidence, prompt identity, model/config, project revision, output/status와 다시 연결한다. latency와 가능한 usage도 invocation evidence에 보존한다.
2. **Quality-evaluable** - task-quality case/rubric을 candidate output 전에 고정하고 bounded negative/positive control로 discrimination을 증명한다. Actual traced model `FAIL`이나 자동 judge는 필수가 아니다.
3. **Replayable** - failure 또는 중요한 edge case를 candidate에서 다시 실행하고 같은 rubric으로 비교한다. Candidate replay가 별도 replay run을 대체할 수 있다.
4. **Feedback-consumed** - durable decision record가 quality basis, baseline/candidate comparison, 재구성 가능한 change-under-test, human decision과 짧은 rationale를 묶는다. Stable retained case identity가 다음 cycle 연결점이다.

### Ongoing Minimum

```text
candidate acceptance event
→ material-output applicability determination
→ applicable:
     retained case + current quality basis
     → admissible candidate-caused material regression evidence?
          → yes: human reject is permitted
          → no:
               valid comparable quality evidence available?
               → yes: compare → accept / reject / no-change
               → no: blocked/inconclusive
                    → acceptance stop
                    → no baseline promotion
                    → durable blocker evidence + revisit condition
→ not applicable:
     reconstructable non-applicability basis

known material failure / edge
→ original evidence link
→ materiality + existing coverage triage
→ covered: link to retained knowledge
→ coverage gap: promote to retained regression knowledge
→ not reproducible: durable deferral + revisit condition
```

Failure status 이름 자체는 `reject` 또는 `blocked`를 결정하지 않는다. Candidate attribution은 causal mechanism 또는 materially equivalent conditions의 bounded evidence와 material quality/operational expectation violation으로 뒷받침해야 한다. Shared/stochastic cause가 plausible한 one-shot asymmetric failure는 attribution이 충분하지 않다면 `blocked/inconclusive`로 둔다.

Quality basis가 materially 바뀌면 새 basis의 bounded control discrimination을 다시 검증한다. 동일한 basis라면 controls를 매 candidate마다 다시 실행하지 않는다. `independent oracle`은 최소 요구가 아니며 human rubric/judgment도 admissible quality judgment basis가 될 수 있다.

Blocker가 해소되어 같은 candidate를 재평가하더라도 이전 blocked attempt의 partial evidence를 이어붙이지 않는다. Current retained case/basis, current accepted baseline과 candidate 조건, provider/model/config/environment를 기준으로 valid comparable evidence를 새로 성립시킨다.

### Artifact Ownership

- **Case definition** - stable case identity + replayable input + quality-basis reference
- **Quality basis validation** - rubric/material expectation + 재구성 가능한 positive/negative control discrimination proof
- **Invocation evidence** - actual run/provenance/output/operations
- **Decision evidence** - comparison + change-under-test + human decision/rationale
- **Failure intake evidence** - original failure reference + coverage disposition 또는 deferral rationale/revisit condition
- **Blocker evidence** - candidate/applicability + case/basis + available evaluation attempt reference + failure/attribution evidence and uncertainty + revisit condition + baseline continuity/no-promotion. Baseline/disposition은 기존 durable decision chain에서 유일하게 복원되면 별도 중복 field가 필요 없다.

### Excluded From Minimum

- 별도 LLMOps SaaS 또는 evaluation platform
- Airflow가 evaluation/LLMOps semantics를 소유하는 구조
- online continuous evaluation과 production SLO dashboard
- 자동 provider drift monitoring
- 별도 cost accounting platform
- multi-model routing 또는 fallback graph
- 자동 prompt optimization
- LLM-as-judge 또는 복잡한 scoring framework
- replay 전용 별도 추가 run
- 실제 traced model failure를 의도적으로 만드는 절차
- recovery `Approval` 또는 delegation authority와 quality decision record를 합치는 구조
- approver identity, RBAC, 서명, issue/PR workflow, deployment state
- 별도 case/rubric/failure taxonomy registry를 필수화하는 구조
- blocked evaluation을 위한 별도 scheduler, retry queue 또는 incident workflow
- 별도 mutable baseline registry
- mandatory independent oracle 또는 fixed statistical attribution threshold

### Current Project State

| 필수 조건 | 상태 | 근거 |
| --- | --- | --- |
| **Traceable** | 충족 | durable invocation evidence와 live provenance proof가 있다. |
| **Quality-evaluable** | 미충족 | Review AI usefulness를 판단하는 authored task-quality case/rubric과 bounded control validation evidence가 없다. |
| **Replayable** | 부분 충족 | provenance replay는 있으나 retained quality case를 candidate에서 같은 rubric으로 재평가한 proof는 없다. |
| **Feedback-consumed** | 미충족 | comparison을 human decision에 소비하고 retained case와 연결한 durable record가 없다. |
| **Ongoing applicability gate** | 미충족 | output-affecting candidate acceptance를 applicability, quality replay/compare, blocked/inconclusive fail-closed 처리와 durable decision 또는 blocker evidence에 연결한 operational proof가 없다. |
| **Failure intake** | 미충족 | known material AI failure를 retained regression coverage 또는 durable deferral로 연결하는 운영 proof가 없다. |

### T7 Final Result

Outcome은 `sublation`이다. `reject vs blocked`를 runtime failure taxonomy가 아니라 **admissible candidate attribution × comparison validity**로 재구성함으로써 A의 fail-closed constraint와 B의 false-reject 방지 constraint를 함께 보존했다.

- `not-applicable` - quality evaluation obligation이 발생하지 않으며 non-applicability basis가 재구성 가능해야 한다.
- `blocked/inconclusive` - applicable하지만 admissible decision evidence가 아직 없으며 acceptance와 baseline promotion을 멈춘다. 실행 불가, evidence invalid, quality judgment insufficiency 같은 차이는 reason에서 보존한다.
- candidate-attributable material failure - causal 또는 bounded attribution evidence가 있으면 human `reject`의 근거가 될 수 있다. Failure status 이름이나 one-shot asymmetric observation 자체는 충분하지 않다.
- blocked baseline - 마지막 accepted baseline lineage가 유지되지만 해당 baseline의 current quality 또는 operational availability를 보증하지 않는다.
- resume - 같은 candidate identity를 유지할 수 있어도 current comparability를 새로 성립시켜야 하며, blocked 동안 baseline이 바뀌었으면 current accepted baseline을 다시 resolve한다.

### Residual Conditions

- **Limits** - stochastic provider behavior의 attribution sufficiency에 fixed repetition/statistical rule을 두지 않는다. Human judgment variability가 남는다. Emergency override semantics와 operational availability policy는 T7 범위 밖이다.
- **Trade-offs** - false reject를 줄이는 대신 ambiguous candidate regression이 blocked로 오래 남아 acceptance latency가 증가할 수 있다.
- **Cautions** - `blocked`는 waiver가 아니다. Human이 candidate 작업을 포기할 수는 있지만 invalid comparison을 LLMOps quality `reject` evidence로 위장하면 안 된다. Baseline retention을 current quality/availability 보증으로 해석하지 않으며, resume 시 과거 partial evidence를 재사용해 false comparability를 만들지 않는다.
- **Reopen Conditions** - emergency override가 실제 requirement가 되거나, provider/model nondeterminism 때문에 attribution이 반복적으로 불가능해 gate가 operational deadlock을 만들거나, decision baseline과 operational-use baseline을 별도 정책으로 관리해야 하거나, current comparability 재성립 규칙이 실제 운영에서 불충분하다는 failure evidence가 생기면 T7을 다시 연다.

### Review Status

B의 `020-b` final review에서 T7 semantic material finding은 없었다. Closure-integrity finding으로 legacy README에 빠져 있던 `discussion.execution`과 `discussion.phase`, T7 completed state, blocked path, blocker evidence ownership과 continuation turn references를 final shared state에 반영했다.

### Human Decision

이 synthesis와 T7 결과는 non-canonical discussion result다. Human decision authority가 채택하기 전에는 canonical project decision이 아니며, 채택 시에도 owning spec/document/workflow에 필요한 내용만 별도 정상 change로 반영한다.
