---
type: report
title: "Review Loop Saturation and Workflow Boundary Investigation Plan"
description: "PR #205의 Chronicle 기반 review-loop saturation incident를 바탕으로 reviewer scope drift, finding admission, workflow transition과 automation ownership의 실제 원인을 revision-aware evidence로 분리 검증하기 위한 조사 계획을 정리한다."
tags:
  - agentic-workflow
  - code-review
  - review-loop
  - scope-control
  - workflow
---

# Review Loop Saturation and Workflow Boundary Investigation Plan

> [!IMPORTANT]
> **핵심 질문은 하나다.** PR #205에서 왜 `review → 수정 → 재리뷰 → 새 finding → 수정`이 반복되었는가? 이 문서는 원인을 미리 정하지 않는다. Reviewer가 scope를 넓힌 문제인지, workflow가 finding을 current remediation으로 과도하게 받아들인 문제인지, 또는 둘 사이의 경계가 약했던 문제인지 **finding 발생 당시 revision**을 기준으로 분리 검증한다.

## Executive Summary

PR #205에서는 `review → remediation → state change → independent review → new finding → remediation`이 반복되는 Review Loop Saturation이 관찰됐다. 기존 saturation report는 Chronicle 기반으로 이 chronology와 사용자 개입 전까지 autonomous loop가 스스로 종료되지 못한 현상을 기록한다.

다만 chronology만으로 root cause가 확정되지는 않는다. 특히 `review-adversarial이 본래 scope 밖 edge case를 계속 만들었다`는 설명과 `main workflow가 candidate finding을 required remediation으로 계속 승격했다`는 설명은 별도로 검증해야 한다. 후속 remediation으로 PR body와 OpenSpec scope 자체가 넓어질 수 있으므로, **최종 head의 scope를 과거 finding에 소급 적용해서도 안 된다.**

### What We Know

- PR #205에서 review와 remediation이 여러 차례 반복됐다.
- 한 시점에 `review-lead ... clear`가 기록된 뒤에도 추가 review와 remediation이 이어졌다.
- 기존 saturation report는 여러 `changes_required`와 사용자 중단 개입까지의 흐름을 기록한다.
- 각 remediation은 repository state를 바꾸므로 독립 review를 다시 요구할 수 있고, 이것이 loop를 재점화하는 구조를 만든다.

### What We Do Not Know Yet

- 각 후속 finding이 **발생 당시** 실제로 current PR/OpenSpec scope 밖이었는가.
- Reviewer의 scope expansion이 primary cause였는가.
- Workflow가 uncertain 또는 optional finding을 required remediation으로 자동 흡수한 것이 primary cause였는가.
- Review 횟수 제한, finding admission gate, workflow transition 수정, reviewer capability 제한 중 무엇이 실제 최소 해결책인가.

> [!NOTE]
> 이 조사에서 PR #205의 기존 saturation report는 **incident chronology evidence**로 사용한다. `Observed chronology`, `causal attribution`, `preventive policy`는 서로 다른 층으로 취급한다.

## Decision Frame

| Decision | Question |
| --- | --- |
| **Primary owner** | 최초 failure는 workflow, review-lead, specialist, review methodology 중 어디에서 발생했는가? |
| **Scope rule** | Reviewer는 explicit target 밖을 어디까지 읽을 수 있고, 어떤 causal evidence가 있어야 current finding으로 승격할 수 있는가? |
| **Remediation rule** | Finding을 `required remediation`, `blocker`, `follow-up`, `unknown`으로 누가 어떤 기준으로 분류할 것인가? |
| **Loop stop** | 단순 반복 횟수가 아니라 어떤 상태를 saturation으로 판단할 것인가? |
| **Automation boundary** | Reviewer가 deterministic automation을 검증하는 것과 직접 대신 수행하는 것을 어떻게 구분할 것인가? |

최종 목표는 광범위한 instruction rewrite가 아니다. **Confirmed root cause → primary owner → 최소 coherent change → regression scenario**의 연결을 만드는 것이다.

## Primary Incident: PR #205

PR #205를 이번 조사의 대표 실증 사례로 사용한다. 분석 단위는 finding 자체보다 **finding이 current remediation으로 transition된 이유**다.

```text
implementation / fix
        ↓
independent review
        ↓
candidate finding
        ↓
scope + causal admission decision
        ├─ required remediation → state change → re-review
        ├─ blocker              → current goal 판단
        ├─ follow-up            → current work 밖으로 분리
        └─ unrelated / unknown  → current remediation 금지
```

현재 확인할 chronology는 다음과 같다.

1. Synthetic 2026 평가 구현과 초기 remediation이 진행됐다.
1. Orchestration quality gate가 추가되면서 실제 PR scope가 확장됐다.
1. 한 commit에는 `review-lead` 독립 리뷰 `clear`가 기록됐다.
1. 이후 review report가 다시 갱신되고 추가 remediation이 발생했다.
1. 기존 saturation report는 여러 `changes_required` 이후 사용자가 반복 루프를 직접 중단했다고 기록한다.
1. 최종 remediation은 policy ownership, filename contract, 3-stage architecture, lock-bound revalidation, sandbox 문서까지 넓은 변경을 포함한다.

> [!WARNING]
> **최종 head를 기준으로 과거 finding을 평가하지 않는다.** 후속 수정으로 Proposal, Design, Tasks 또는 PR body가 넓어졌을 수 있다. 각 finding은 반드시 그 finding이 발생한 시점의 revision과 당시 contract를 대조한다.

## Evidence Model

각 review cycle의 자료는 다음 세 종류로 분리한다.

| Class | Meaning | Examples |
| --- | --- | --- |
| **Observed** | 도구·기록에서 직접 확인되는 사실 | Chronicle/session history, commit, review output, validation result |
| **Inferred** | 관찰된 현상을 설명하는 원인 가설 | reviewer scope drift, completion bias, missing admission gate |
| **Proposed** | 재발 방지를 위한 정책 또는 설계 | loop cap, admission gate, escalation, capability restriction |

이 구분을 유지해야 chronology의 강한 증거를 보존하면서도 root cause와 처방을 과잉 확정하지 않는다.

## Competing Hypotheses

| Hypothesis | Failure Description | Evidence Needed |
| --- | --- | --- |
| **H1 — Scope handoff failure** | Workflow가 PR/Change identity, Goal, In Scope, Out of Scope, Acceptance를 review brief에 충분히 고정하지 못했다. | 각 review invocation의 실제 brief와 당시 Active Scope 비교 |
| **H2 — Reviewer enforcement failure** | 올바른 scope를 받았지만 review-lead 또는 specialist가 supporting context를 새로운 review target으로 확장했다. | 명시적 scope를 받은 controlled review에서 unrelated finding이 current finding으로 승격되는지 확인 |
| **H3 — Finding admission failure** | Candidate finding이 causal relation과 current authority를 재판정받지 않고 required remediation으로 승격됐다. | Finding 발생 후 main workflow의 분류·전환 근거 추적 |
| **H4 — Loop control failure** | State change 후 재리뷰 규칙은 작동했지만 semantic saturation 판단이 없어 반복을 스스로 멈추지 못했다. | 반복 cycle에서 새로운 material information의 유무와 종료 판단 근거 비교 |
| **H5 — Automation ownership failure** | Reviewer가 repository-native script, generator, validator가 소유할 deterministic 작업을 직접 대체했다. | Runtime별 tool surface와 실제 validation path 비교 |

가설은 상호 배타적이지 않다. 다만 수정은 **최초 failure를 소유한 primary owner**부터 시작한다.

## Finding Admission Model

Reviewer가 explicit target 밖의 파일이나 dependency를 읽는 것 자체는 scope drift가 아니다. Current change의 reachability, contract 또는 regression을 확인하려면 외부 context가 필요할 수 있다.

Current finding으로 승격하려면 다음 중 하나가 material하게 성립해야 한다.

1. 문제가 explicit review target 또는 Active Scope 안에 있다.
1. Current change가 changed surface 밖에 직접 도달 가능한 regression을 만든다.
1. 외부 caller, consumer, dependency 또는 contract가 current Goal이나 Acceptance 실패를 증명한다.
1. Finding이 current implementation 또는 validation의 material incompleteness를 증명한다.

그 외의 발견은 current remediation으로 자동 승격하지 않는다.

| Relation | Current Treatment |
| --- | --- |
| `explicit_target` | Current finding 후보 |
| `direct_regression` | Current finding 후보 |
| `contract_dependency` | Current finding 또는 blocker 후보 |
| `acceptance_gap` | Current finding 후보 |
| `independent_requirement` | Follow-up 후보 |
| `unrelated` | Current finding 제외 |
| `unknown` | Limitation 또는 escalation |

## Investigation Method

### Phase 1 — Reconstruct Historical Review Cycles

기존 saturation report가 기록한 1차·2차·3차 review cycle을 당시 revision별로 재구성한다.

각 cycle에서 다음을 수집한다.

- Reviewed revision과 직전 remediation revision
- 당시 PR title, body와 Boundaries
- 당시 active OpenSpec Proposal, Design, Tasks
- Reviewer에게 전달된 target, Goal, scope와 validation evidence
- Candidate finding의 source와 specialist
- Finding 이후 실제 remediation과 scope 변화

### Phase 2 — Classify Each Finding at Its Own Revision

각 finding에 `explicit_target`, `direct_regression`, `contract_dependency`, `acceptance_gap`, `independent_requirement`, `unrelated`, `unknown` 중 하나의 relation을 부여한다.

판정 기준은 **당시 contract**다. 최종 head에서 후속 수정된 contract는 사용하지 않는다.

### Phase 3 — Trace Finding-to-Remediation Transitions

각 finding이 왜 `required remediation`이 됐는지 추적한다.

- Reviewer가 처음부터 `changes_required`로 과도하게 승격했는가.
- Review-lead가 specialist candidate를 filtering하지 못했는가.
- Main workflow가 reviewer finding을 authority처럼 받아들였는가.
- OpenSpec Scope Control, blocker, follow-up Change 분기 대신 current Apply에 흡수했는가.

이 단계가 PR #205 loop의 primary owner를 결정하는 핵심이다.

### Phase 4 — Separate Reviewer Behavior from Caller Behavior

같은 target에 대해 scope brief 품질만 다르게 한 paired case를 비교한다.

- Ambiguous brief에서 drift가 발생하는가.
- Explicit PR/OpenSpec scope를 줬는데도 drift가 발생하는가.
- External context를 읽되 causal relation이 없는 defect를 제외하는가.
- Diff 밖에 있는 실제 regression은 계속 탐지하는가.

### Phase 5 — Validate Loop Stop and Automation Ownership

Review 횟수보다 **새로운 material in-scope information이 계속 존재하는가**를 기준으로 종료 조건을 검증한다.

또한 repository-native deterministic owner가 존재할 때 reviewer가 그것을 검증만 하는지, 직접 재현·갱신·우회하는지 확인한다.

## Loop Stop Candidate

기존 saturation report의 `최대 2회` 제안은 유용한 경고선이 될 수 있지만, hard completion rule로 바로 채택하지 않는다. 두 번째 review에서 material regression이 발견될 수 있기 때문이다.

보다 안전한 후보는 다음과 같다.

> [!TIP]
> **반복 review 자체를 막지 말고 automatic remediation을 멈춘다.** 일정 횟수 이상 반복되거나 새 finding의 scope가 불명확해지면, 그 finding을 곧바로 구현하지 않고 current scope와 causal relation을 다시 판정한다.

```text
new finding after repeated review
        ↓
material + causally in scope?
        ├─ yes → bounded remediation 가능
        ├─ no  → follow-up / unrelated
        └─ unclear → blocker / unknown / user decision
```

이 모델은 legitimate regression recall을 유지하면서 autonomous scope expansion을 차단하는 것을 목표로 한다.

## Success Criteria

조사는 다음을 모두 설명할 수 있을 때 종료한다.

- PR #205의 각 주요 review cycle을 revision-aware chronology로 재구성했다.
- 각 finding이 당시 scope와 어떤 relation이었는지 근거로 분류했다.
- Reviewer와 caller/workflow의 책임을 분리했다.
- Out-of-scope 또는 independent requirement가 current remediation으로 흘러간 authority path를 설명했다.
- Legitimate causal regression을 놓치지 않는 finding admission 기준을 제시했다.
- Review saturation을 단순 횟수가 아닌 의미론적 상태로 정의했다.
- Automation ownership 문제가 instruction, capability, workflow 중 어디에 있는지 분류했다.
- 필요한 변경 owner와 건드리지 않아야 할 owner를 함께 설명했다.

## Current Boundary

이 문서는 **조사 계획과 evidence framing을 기록하는 non-canonical inbox artifact**다. Reviewer agent, Skill, OpenSpec workflow, code 또는 tests를 이 보고서만으로 변경하지 않는다. 실제 수정은 조사 evidence가 primary owner를 확정하고 별도 변경 요청 또는 승인 범위가 생긴 뒤 최소 coherent change로 진행한다.

## References

- [Review Loop Saturation Analysis](19-56-report-review-loop-saturation-analysis.md)
- [PR #205 Review](12-25-review-reliability-orchestration-pr-205.md)
- [`prj-spec-driven-tdd-rpi`](../../.rulesync/skills/prj-spec-driven-tdd-rpi/SKILL.md)
- [`prj-load-context-development`](../../.rulesync/skills/prj-load-context-development/SKILL.md)
- [`prj-load-context-review`](../../.rulesync/skills/prj-load-context-review/SKILL.md)
- [`prj-review-code`](../../.rulesync/skills/prj-review-code/SKILL.md)
- [Pull Request Review](../../docs/development/vcs-git/pull-request-review.md)
