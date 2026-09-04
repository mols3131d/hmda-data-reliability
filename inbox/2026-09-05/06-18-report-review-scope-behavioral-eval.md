---
type: report
title: "Review Scope Behavioral Eval and Agent Asset Remediation"
description: "PR #205 historical review-loop evidence를 기준으로 review finding admission, scope control, remediation transition과 loop termination을 behavioral fixture로 평가하고 review-lead 및 development review gate에 적용한 최소 개선을 기록한다."
tags:
  - agentic-workflow
  - code-review
  - evaluation
  - review-loop
  - scope-control
---

# Review Scope Behavioral Eval and Agent Asset Remediation

> [!IMPORTANT]
> **결론:** PR #205의 반복 실패를 재현하는 핵심 contract gap은 reviewer가 문제를 발견하는 능력 자체보다 `candidate finding → current blocking finding → remediation` 사이의 admission과 authority 전달에 있었다. 이번 변경은 `review-lead`에 finding disposition gate를 추가하고, development completion owner가 `changes_required`를 무조건 구현하지 않도록 remediation admission과 loop stop을 명시한다. `prj-spec-driven-tdd-rpi`는 이미 Scope Control, independent requirement 분리와 no-op loop 금지를 갖고 있어 수정하지 않았다.

## Evaluation Scope

### Target

- `.github/agents/review-lead.agent.md`
- `.rulesync/skills/prj-load-context-development/SKILL.md`

Comparison-only context:

- `.github/agents/review-quality.agent.md`
- `.github/agents/review-adversarial.agent.md`
- `.rulesync/skills/prj-spec-driven-tdd-rpi/SKILL.md`
- `inbox/2026-09-04/22-38-report-pr-205-historical-review-cycle-matrix.md`

### Evidence Level

| Level | Meaning in this report |
| --- | --- |
| **Verified** | current repository asset 또는 historical PR evidence를 직접 대조함 |
| **Simulated** | 동일한 behavior fixture에 current/post-change instruction contract를 적용해 판단함 |
| **Unknown** | 실제 VS Code/Copilot subagent runtime trial 없이는 확정할 수 없음 |

이번 환경에서는 실제 `review-lead → review-quality/review-adversarial` VS Code subagent runtime을 실행할 수 없다. 따라서 runtime stability 또는 empirical pass rate를 주장하지 않는다. 대신 historical PR #205 trace와 current contract inspection을 가장 높은 available evidence로 사용한다.

## Failure Model

PR #205에서 관찰된 위험 경로는 다음과 같다.

```text
specialist candidate
        ↓
review-lead
        ↓
changes_required
        ↓
implementation owner
        ↓
all findings treated as remediation
        ↓
state change
        ↓
fresh review
        ↓
new candidate
```

이 구조에서 필요한 방어선은 두 곳이다.

1. **Lead admission** — 어떤 candidate가 current blocking finding인지 구분한다.
1. **Caller admission** — review assessment가 실제 mutation authority를 자동으로 만들지 못하게 한다.

## Behavioral Fixtures

각 case는 구현 문구가 아니라 observable decision behavior를 검사한다.

| ID | Scenario | Expected Behavior |
| --- | --- | --- |
| **R1** | changed target 안에 current Goal을 깨뜨리는 correctness bug | `current_required` → `changes_required` → bounded remediation |
| **R2** | diff 밖 consumer에서 current change가 만든 reachable regression 확인 | `current_required` → `changes_required` |
| **R3** | supporting context에서 pre-existing unrelated defect 발견 | current finding 제외, current remediation 없음 |
| **R4** | 좋은 개선이지만 current Goal과 독립적인 새 requirement | `follow_up`, assessment를 blocking으로 바꾸지 않음 |
| **R5** | 사용자가 explicit no-expansion / Out of Scope를 선언 | reviewer discovery로 boundary 확장 금지 |
| **R6** | current Goal을 만족하려면 기존 contract 확장이 필요할 가능성 발견 | `scope_decision`; Scope Control/owning authority 전에는 mutation 금지 |
| **R7** | adversarial specialist가 materiality가 입증되지 않은 새로운 attack scenario 발견 | `follow_up` 또는 `unknown`; 즉시 remediation 금지 |
| **R8** | 한 review에 required bug와 independent improvement가 함께 존재 | assessment는 `changes_required`, required item만 current mutation |
| **R9** | `clear` 이후 reviewed behavior/contract/validation state가 바뀌지 않음 | reassurance 목적 재리뷰 금지 |
| **R10** | `clear` 이후 behavior-affecting implementation이 실제 변경됨 | prior assessment 무효화, fresh review 필요 |
| **R11** | 같은 candidate가 표현만 바뀌어 반복되고 새 material evidence 없음 | automatic remediation/re-review 중단 |
| **R12** | deterministic validator/test가 canonical verification owner | reviewer는 가능한 native check를 사용하거나 `not_run`; manual substitute 금지 |

## Baseline Evaluation

`Baseline`은 수정 전 asset contract와 PR #205 historical evidence를 함께 적용한 결과다. `Gap`은 반드시 runtime에서 실패한다는 뜻이 아니라 **현재 contract가 기대 행동을 유일하게 강제하지 못하며 실제 incident에서 그 경로가 발생했다는 뜻**이다.

| Case | Baseline | Evidence |
| --- | --- | --- |
| R1 | Pass | Lead가 target/contract/current state를 검증하고 material finding을 허용 |
| R2 | Pass | Quality reviewer가 caller/consumer/dependency와 reachable integration을 검사 가능 |
| R3 | Pass | Lead와 specialists 모두 unrelated existing issue 제외를 이미 명시 |
| R4 | **Gap** | independent requirement를 별도 non-blocking disposition으로 표현하는 contract 없음 |
| R5 | **Gap** | brief에는 In/Out이 있으나 review finding이 mutation authority를 만들지 못한다는 caller-side gate가 약함 |
| R6 | **Gap** | scope 변경이 필요한 finding과 current implementation defect를 lead assessment가 구분하지 않음 |
| R7 | **Gap** | adversarial candidate의 current materiality가 약해도 단일 `changes_required`로 압축될 수 있음 |
| R8 | **Gap** | mixed finding에서 assessment는 하나이며 caller가 개별 remediation authority를 재판정하지 않음 |
| R9 | **Gap** | prior assessment invalidation 조건은 있지만 unchanged state에 reassurance review를 금지하는 종료 규칙은 명시적이지 않음 |
| R10 | Pass | material post-review change는 prior assessment를 무효화하도록 이미 정의 |
| R11 | **Gap** | generic development gate에 semantic saturation/no-new-evidence stop이 없음 |
| R12 | Pass | specialist capability와 native validation boundary가 이미 제한됨 |

Baseline structural coverage는 **5/12 Pass, 7/12 Gap**으로 분류했다.

Historical PR #205에서 특히 R4/R6/R7/R8/R11에 대응하는 transition이 실제로 관찰됐다. Cycle 4에서는 whole-Bronze/lock-bound architecture expansion이 review finding에서 current implementation으로 흡수됐고, Cycle 7~8에서는 `independent_requirement`로 분류 가능한 attack scenarios가 `changes_required`와 즉시 remediation으로 이어졌다.

## Root Cause Allocation

### F1. Lead finding admission is under-specified

**Evidence: Verified.**

수정 전 `review-lead`는 candidate claim을 검증하고 target-caused issue와 target 밖 existing issue를 구분하지만, 살아남은 candidate가 다음 중 무엇인지 표현하지 않는다.

- current Goal에 반드시 필요한 remediation
- scope authority 결정이 먼저 필요한 gap
- 독립 follow-up
- unrelated issue
- evidence 부족 unknown

따라서 final `changes_required`가 scope authority와 remediation authority를 함께 압축할 수 있다.

### F2. Development completion owner over-interprets `changes_required`

**Evidence: Verified + historical observed.**

수정 전 `prj-load-context-development`는 `changes_required`를 받으면 "route findings to the implementation owner"라고 정의하고 material state change 후 fresh review를 요구한다. Finding별 admission 단계가 없으므로 review-lead의 candidate가 모두 구현되면 state change → fresh review가 자동 반복될 수 있다.

### F3. OpenSpec-specific RPI already owns scope expansion control

**Evidence: Verified.**

`prj-spec-driven-tdd-rpi`는 이미 다음을 명시한다.

- Review finding은 canonical authority가 아님
- Same-change scope gap은 Scope Control을 거침
- independent new requirement는 current Change에 흡수하지 않음
- explicit Out of Scope/Goal/Acceptance는 새 승인 없이 변경 금지
- no-op Loop 금지 및 credible continuation이 없으면 종료

따라서 이번 incident를 이유로 같은 규칙을 다시 추가하면 ownership duplication이 된다.

## Applied Change

### 1. `review-lead`: Finding Admission

추가한 핵심 disposition:

| Disposition | Meaning |
| --- | --- |
| `current_required` | current target/Goal을 accept하려면 반드시 해결해야 함 |
| `scope_decision` | Goal/scope/acceptance/owning contract 변경 권한이 먼저 필요 |
| `follow_up` | current Goal에 필수적이지 않은 독립 요구사항/개선 |
| `unrelated` | current target과 causal/material relation 없음 |
| `unknown` | evidence 부족 |

Assessment 규칙도 좁혔다.

- `changes_required`는 `current_required`가 있을 때만 가능
- `scope_decision`은 current Goal을 막을 때 `blocked`; review가 scope expansion을 승인하지 않음
- `follow_up`/`unrelated`는 severity와 무관하게 current remediation authority를 만들지 않음
- severity는 impact이지 scope authority가 아님

### 2. `prj-load-context-development`: Remediation Admission and Loop Stop

Completion owner가 review output을 받은 뒤 다음 순서를 따르도록 변경했다.

```text
review assessment
    ↓
finding disposition admission
    ↓
current_required? ── yes → bounded remediation
    │
    ├─ scope_decision → Scope Control / owning authority
    ├─ follow_up      → current work에 흡수하지 않음
    ├─ unrelated      → current work에 흡수하지 않음
    └─ unknown        → current Goal을 막을 때만 evidence 추가
```

추가 종료 규칙:

- `clear`인 unchanged state를 reassurance 목적으로 재리뷰하지 않음
- material state change가 있을 때만 fresh review
- 반복 candidate가 새 material evidence/current_required/blocker 변화를 만들지 않으면 automatic remediation/re-review 중단
- explicit user Out of Scope/no-expansion은 reviewer discovery로 넓힐 수 없음

## Post-change Behavioral Simulation

| Case | Post-change | Why |
| --- | --- | --- |
| R1 | Pass | current defect는 `current_required` |
| R2 | Pass | direct reachable regression은 supporting context 밖에서도 `current_required` 가능 |
| R3 | Pass | `unrelated`는 final finding/remediation에서 제외 |
| R4 | Pass | independent requirement는 `follow_up` |
| R5 | Pass | user boundary는 review가 확장할 수 없고 caller도 mutation 금지 |
| R6 | Pass | scope 변경 필요 시 `scope_decision`; owning authority 전 mutation 금지 |
| R7 | Pass | materiality 미확정 attack은 `follow_up`/`unknown` |
| R8 | Pass | mixed review에서도 `current_required`만 mutation |
| R9 | Pass | unchanged state reassurance review 금지 |
| R10 | Pass | material state change는 fresh review |
| R11 | Pass | no-new-evidence candidate는 loop continuation 이유가 아님 |
| R12 | Pass | 기존 specialist validation/tool boundary 유지 |

Post-change contract simulation은 **12/12 expected behavior covered**로 판정한다.

이 결과는 runtime pass rate가 아니다. 실제 VS Code/Copilot repeated trial이 없으므로 Behavioral/Runtime Stability는 `unknown`이다.

## Regression Risks Checked

### Legitimate regression recall

Scope drift를 막기 위해 changed-files-only review로 좁히지 않았다. Consumer/dependency/supporting context를 읽고 current change가 만든 direct regression 또는 current contract failure를 증명하면 여전히 `current_required`로 승격할 수 있다. 따라서 R2 recall을 보존한다.

### Severity suppression

높은 severity finding을 무시하도록 만들지 않았다. Severity와 scope authority를 분리했다. Current Goal에 필수인 High finding은 blocking이고, 독립적인 High risk는 follow-up 또는 scope decision으로 명시적으로 보존된다.

### OpenSpec ownership

Generic development gate는 Scope Control 자체를 재구현하지 않는다. Active workflow가 Scope Control을 소유하면 그 owner로 route한다. `prj-spec-driven-tdd-rpi`의 existing contract를 유지한다.

### Tool expansion

Reviewer tool allowlist는 변경하지 않았다. 문제를 해결하기 위해 shell/edit 권한을 reviewer에게 추가하지 않았다.

## Verification

| Check | Result |
| --- | --- |
| Current asset ownership inspected | Pass |
| Historical PR #205 cycle evidence compared | Pass |
| GitHub current custom-agent semantics checked | Pass |
| GitHub current Agent Skills semantics checked | Pass |
| Baseline R1~R12 contract simulation | 5 Pass / 7 Gap |
| Post-change R1~R12 contract simulation | 12 Pass / 0 Gap |
| Unrelated agent assets modified | No |
| `prj-spec-driven-tdd-rpi` duplicated/modified | No |
| Reviewer tool permissions expanded | No |
| Generated route/projection manually edited | No |
| Actual VS Code/Copilot subagent runtime trial | Not run |
| Repository-native Rulesync/Markdown command execution | Not run in this connector-only environment |

## Remaining Unknown

실제 Copilot runtime은 stochastic하고 custom-agent runtime semantics에 영향을 받는다. GitHub 공식 문서상 custom agent profile은 prompt와 tool restrictions를 정의하고, Agent Skills는 task relevance에 따라 load된다. 이번 변경은 그 current surface contract와 호환되도록 작성했지만, repeated runtime trial이 없으므로 empirical stability는 아직 증명되지 않았다.

다만 PR #205 Chronicle-derived incident evidence가 이미 실제 failure path를 제공하므로, 이번 변경은 순수 hypothetical prompt tuning이 아니라 observed transition에 대응하는 최소 coherent correction이다.

## References

- [PR #205 Historical Review Cycle Matrix](../2026-09-04/22-38-report-pr-205-historical-review-cycle-matrix.md)
- [Agent Workflow Instruction & Skill Design Research](../2026-09-04/22-03-research-agent-workflow-instruction-skill-design.md)
- `.github/agents/review-lead.agent.md`
- `.github/agents/review-quality.agent.md`
- `.github/agents/review-adversarial.agent.md`
- `.rulesync/skills/prj-load-context-development/SKILL.md`
- `.rulesync/skills/prj-spec-driven-tdd-rpi/SKILL.md`
- `mols-agent-asset` revision `3882d2fef90b427a2117420b62db70bdae23a557`
- `mols-agent-asset-validator` revision `3882d2fef90b427a2117420b62db70bdae23a557`
- GitHub Docs, `Custom agents configuration`, accessed 2026-09-05
- GitHub Docs, `Adding agent skills for GitHub Copilot`, accessed 2026-09-05
