---
type: research
title: "Designing Agent Instructions and Skills from Runtime Evidence"
description: "PR #205의 review-loop saturation incident와 GitHub Copilot Chronicle, Agent Skills, custom agent 자료를 바탕으로 agent instruction·Skill·subagent workflow를 어떻게 조사·설계·검증해야 하는지 evidence-first 방법론을 정리한다."
status: "completed"
tags:
  - "agentic-workflow"
  - "agent-assets"
  - "copilot"
  - "review-loop"
  - "evaluation"
---

# Designing Agent Instructions and Skills from Runtime Evidence

> [!IMPORTANT]
> **핵심 결론:** Agent instruction이나 Skill을 개선할 때는 실패 사례를 보고 곧바로 문구를 추가하면 안 된다. 먼저 **실제 runtime/session evidence → 책임과 scope 복원 → 최초 failure point 식별 → 올바른 asset surface 선택 → 최소 행동 계약 변경 → positive/negative/near-miss/adversarial eval → runtime 재검증** 순서로 진행해야 한다. PR #205에서는 reviewer 자체에 이미 상당한 scope boundary가 있었지만, `candidate finding → changes_required → implementation remediation → state change → fresh review` 사이의 **finding admission과 transition contract**가 충분히 세분화되지 않은 것이 중요한 조사 후보로 확인된다.

## Question

PR #205에서 발생한 review-loop saturation을 재발 방지하려면 agent instruction, Skill, custom agent와 workflow를 어떤 방식으로 조사·설계·검증해야 하는가?

특히 다음을 답한다.

1. 반복되는 agent failure를 어떤 evidence로 복원해야 하는가.
2. 문제를 `instruction`, `Skill`, `custom agent`, `workflow`, `tool/automation` 중 어디에 고쳐야 하는가.
3. Scope drift와 review saturation을 막으면서 실제 causal regression detection은 유지하려면 어떤 contract가 필요한가.
4. GitHub Copilot Chronicle은 이 개선 lifecycle에서 어떤 역할을 해야 하는가.
5. 새 instruction/Skill을 만들거나 기존 자산을 수정한 뒤 어떤 eval과 runtime 검증이 필요한가.

### Scope

포함한다.

- PR #205의 review-loop incident와 historical scope 변화
- 현재 repository의 review agent와 implementation/OpenSpec workflow contract
- project agent-asset surface selection과 canonical ownership 원칙
- GitHub Copilot custom instructions, custom agents, Agent Skills와 Chronicle
- Agent Skills open specification의 routing/progressive-disclosure 원칙
- agent behavior evaluation, loop termination, tool ownership과 least-privilege 설계

포함하지 않는다.

- PR #205 product code correctness 재리뷰
- reviewer agent 또는 Skill의 실제 수정
- OpenSpec schema 자체 변경
- 특정 모델의 품질 순위 비교
- GitHub Copilot session store에 직접 접근해 Chronicle raw history를 재수집하는 작업

### Stop Condition

다음 판단을 근거로 설명할 수 있으면 조사를 종료한다.

- PR #205의 concrete failure pattern과 current contract 사이의 gap
- 각 agent asset surface의 책임과 선택 기준
- instruction/Skill 개선을 위한 repeatable investigation workflow
- eval fixture와 acceptance 기준
- 실제 수정 전에 확인해야 할 primary owner와 remaining unknown

## Evidence Model

이 보고서는 근거를 다음처럼 구분한다.

| Evidence | Meaning |
| --- | --- |
| **Verified** | repository file, historical revision, Git history 또는 공식 문서에서 직접 확인 |
| **Supporting** | incident report 또는 external engineering guidance가 제공하는 맥락 |
| **Inference** | Verified evidence를 연결해 도출한 원인 후보 |
| **Unknown** | runtime/session raw evidence 없이는 확정할 수 없는 부분 |

이 구분은 repository의 `prj-research-workspace` evidence contract와 동일한 방향이다. 낮은 수준의 근거가 더 높은 authority를 조용히 덮어쓰지 않으며, 실행하지 않은 runtime behavior를 verified로 취급하지 않는다.[^research-evidence]

## Findings

### F1. PR #205는 "reviewer에게 scope 규칙이 없어서"만 발생한 사건으로 설명할 수 없다

현재 `review-lead`는 bounded technical review를 명시하고, specialist에게 동일한 `target / revision / intended behavior / contract / in-scope / out-of-scope / validation` brief를 전달하도록 요구한다. 또한 specialist output을 final evidence가 아닌 candidate claim으로 취급하고, target 때문에 생긴 issue와 target 밖 existing issue를 구분하도록 요구한다.[^review-lead]

`review-quality` 역시 caller·consumer·dependency를 읽을 수 있지만 unrelated existing defect, style preference, general cleanup와 optional redesign을 제외한다. `review-adversarial`도 reachable하고 material한 attack surface에만 집중하며 unrelated system risk와 generic architecture critique로 넓히지 않도록 되어 있다.[^review-quality][^review-adversarial]

즉 현재 text contract에는 이미 다음 방어선이 존재한다.

```text
bounded target
→ minimal review brief
→ specialist candidate finding
→ lead evidence verification
→ unrelated issue exclusion
```

따라서 같은 문제가 반복되었다는 이유만으로 reviewer prompt에 `stay in scope` 문장을 더 추가하는 것은 low-confidence fix다.

**Inference:** 실제 문제는 boundary 문구의 부재보다 boundary가 runtime handoff와 finding disposition에서 충분히 구조화되지 않았거나, reviewer 결과를 받는 caller가 finding을 current remediation으로 자동 승격한 지점일 가능성이 높다.

### F2. Generic development review handoff에는 semantic compression point가 있다

현재 `prj-load-context-development`는 independent review gate를 다음과 같이 처리한다.[^development-review-gate]

```text
review-lead
    ↓
Assessment
    ├─ clear
    ├─ changes_required
    └─ blocked
```

`changes_required`이면 findings를 implementation owner로 route하고, affected state가 바뀌면 fresh `review-lead` assessment를 다시 받는다.

이 contract는 independent review correctness에는 유용하지만 **finding 종류가 caller로 넘어가는 순간 하나의 remediation bucket으로 압축될 위험**이 있다.

예를 들어 material concern은 실제로 다음처럼 다를 수 있다.

| Finding Type | Correct Transition |
| --- | --- |
| current implementation defect | current remediation |
| current acceptance gap | current remediation 또는 owning planning correction |
| same-change scope gap | Scope Control 후 결정 |
| external blocker | blocker / escalation |
| independent new requirement | follow-up Change |
| pre-existing unrelated defect | current work에서 제외 |
| insufficient evidence | unknown / validation gap |

하지만 generic gate의 top-level output은 `changes_required` 하나다. `review-lead`의 final finding contract도 현재 `required action 또는 필요한 판단`을 반환하지만, `scope_relation`과 `disposition`을 mandatory field로 요구하지는 않는다.[^review-lead]

**Inference:** PR #205 같은 loop에서 `changes_required`가 "이 finding을 현재 scope에서 바로 구현하라"로 해석되면, 하나의 candidate가 state change를 만들고 그 state change가 fresh review를 강제하면서 loop가 재점화될 수 있다.

### F3. OpenSpec workflow에는 이미 더 풍부한 transition model이 있다

`prj-spec-driven-tdd-rpi`는 review finding을 canonical authority로 취급하지 않는다. 근거와 영향을 확인하고 current terminal과 Active Scope 안에서 owner에게 route하며, boundary 밖 remediation은 `Next`로만 반환하도록 명시한다.[^openspec-rpi]

특히 Review transition은 다음을 이미 구분한다.

- Evidence / material assumption gap → Research
- Planning defect → earliest owning planning artifact
- Implementation / test defect → Apply
- Same-change scope gap → Scope Control 후 Research
- Narrower material blocker → child scope 조건 검토
- Independent new requirement / current Change 밖 범위 → current Change에 흡수하지 않음
- Material gap 없음 → COMPLETE
- Credible continuation 없음 → saturation 또는 capability/authority boundary로 BLOCKED

이 모델은 이번 문제를 푸는 데 중요한 reference다. Review finding을 단순 `fix / no-fix`가 아니라 **workflow transition event**로 취급하기 때문이다.

다만 이것만으로 실제 runtime이 안전하다고 증명되지는 않는다. Active Scope가 review brief에서 손실되는지, lead가 specialist candidate를 current finding으로 승격할 때 relation을 충분히 증명하는지, implementation owner가 transition을 정확히 적용하는지는 별도 behavior eval이 필요하다.

### F4. PR #205는 `clear` 이후 실제 contract가 넓어졌다는 historical evidence를 제공한다

`a32062b` commit은 review remediation 후 `review-lead ... clear`를 commit message에 기록한다.[^pr205-commits]

그 시점의 `orchestration-quality-gate` Proposal은 다음 정도를 In Scope로 두고 있었다.[^a320-orchestration]

- DAG thin-adapter task
- `detect_basic_incidents` 기반 anomaly detection
- anomaly 시 `AirflowException`

반면 최종 PR head의 Proposal은 다음을 추가로 포함한다.[^final-orchestration]

- Reliability-owned baseline / threshold / detector / blocking policy
- Data Operations application composition
- 전체 Bronze partition 평가
- dbt mutation lock 안의 build 직전 revalidation
- durable architecture와 domain guide 동기화

Synthetic Change도 `a32062b` 시점에는 generic 2026 deterministic `null_spike`와 sandbox lifecycle이 핵심이었지만, 최종 Proposal에는 `case_name`과 ingestion filename parser가 동일한 target year를 읽도록 하는 explicit filename contract가 추가됐다.[^a320-synthetic][^final-synthetic]

이 차이는 두 가지를 동시에 보여준다.

1. 후속 review가 실제로 contract를 materially 발전시켰다.
2. 그러므로 그 후속 work가 모두 "원래 scope 안의 단순 bug fix"였다고 소급해서 말할 수 없다.

> [!NOTE]
> 이 evidence는 후속 확장이 잘못됐다는 뜻이 아니다. 일부는 current Goal을 실제로 닫기 위해 필요한 **same-change scope gap**이었을 수 있다. 중요한 문제는 그러한 확장이 reviewer finding만으로 바로 implementation authority를 얻지 않고, **Scope Control / Research / owner decision**을 거쳐야 한다는 점이다.

### F5. Chronicle은 instruction 생성기가 아니라 runtime failure evidence source로 사용해야 한다

GitHub Copilot의 session data에는 prompt, response, tool usage와 modified file details가 기록되고, `/chronicle`은 이 session history를 검색·요약·분석한다. `/chronicle improve`는 agent가 반복적으로 어려움을 겪었거나 사용자가 후속 prompt로 방향을 수정한 지점을 분석해 custom instruction 개선안을 제안한다.[^chronicle-concept][^chronicle-howto]

이 기능은 agent asset 개선에 매우 유용하다. 특히 다음 evidence를 찾는 데 적합하다.

- 같은 종류의 user correction이 반복되는가.
- 어떤 task에서 tool을 잘못 선택하는가.
- scope를 넓히는 패턴이 어떤 handoff 뒤에 나타나는가.
- review loop가 몇 번, 어떤 finding transition으로 재점화되는가.
- "사용자가 다시 설명해야 했던 순간"이 어디인가.

하지만 `/chronicle improve` 결과를 곧바로 canonical instruction으로 넣으면 과적합 위험이 있다.

Chronicle은 다음 역할에 두는 것이 안전하다.

```text
session history
    ↓
recurring failure hypothesis
    ↓
source / contract / runtime verification
    ↓
asset owner selection
    ↓
minimal change
    ↓
eval + runtime re-test
```

즉 Chronicle은 **Observed/Supporting evidence를 제공하는 diagnostics layer**이고, instruction authority는 아니다.

### F6. Agent asset은 내용보다 applicability와 ownership으로 먼저 선택해야 한다

이 repository는 agent-facing surface를 다음처럼 구분한다.[^agent-surface]

| Applicability | Preferred Surface |
| --- | --- |
| repository 전체 | root `AGENTS.md` |
| directory subtree | nearest `AGENTS.md` |
| path / glob / file type | Rule |
| task intent / semantic relevance | Skill |

GitHub Copilot 공식 문서의 customization model도 유사한 분리를 제공한다.[^copilot-customization]

| Surface | Appropriate Use |
| --- | --- |
| Custom instructions | 거의 모든 관련 interaction에 필요한 persistent project context |
| Path-specific instructions | 특정 file/path에서만 적용되는 규칙 |
| Agent Skill | 특정 task에서 필요할 때만 로드할 상세 workflow, script, resource |
| Custom agent | 특정 역할, prompt, tool surface를 가진 specialized agent |
| Prompt file | 사용자가 명시적으로 호출하는 reusable interaction template |

Agent failure를 고칠 때 **"어디에 문장을 넣을까"보다 먼저 "누가 이 behavior를 소유해야 하는가"를 결정**해야 한다.

예시:

| Problem | Better Owner |
| --- | --- |
| 모든 작업에서 main branch를 건드리지 말아야 함 | repository/project instruction |
| Markdown 파일에만 적용되는 규칙 | path-specific Rule |
| PR review workflow에서만 필요한 finding admission 절차 | review Skill / review workflow owner |
| reviewer 자체의 역할·도구·return contract | custom reviewer agent |
| mechanical generated-file sync | deterministic script/tool, not reviewer prose |
| 특정 반복 작업의 상세 procedure | Skill |

### F7. Skill의 `description`은 설명이 아니라 routing contract다

Agent Skills specification에서 `name`과 `description`은 startup 시 metadata로 로드되고, agent는 이를 이용해 relevant Skill을 선택한다. Skill이 선택된 뒤에야 전체 `SKILL.md` body가 context에 들어간다.[^agent-skills-spec]

따라서 Skill 설계에서 `description`은 단순한 소개문이 아니다.

좋은 description은 최소한 다음을 포함해야 한다.

- **What:** 어떤 책임을 수행하는가.
- **When:** 어떤 task intent에서 사용해야 하는가.
- **Negative boundary:** 비슷하지만 사용하면 안 되는 task는 무엇인가.
- **Disambiguating keywords:** 다른 Skill과 routing을 구분하는 domain/task vocabulary.

Repository의 `mols-agent-asset`도 responsibility와 intended activation을 file/format보다 먼저 결정하도록 요구하고, 기존 owner를 확장하는 것을 competing owner 생성보다 우선한다.[^mols-agent-asset]

### F8. Skill 본문은 모든 세부사항을 담는 곳이 아니다

Agent Skills specification은 progressive disclosure를 권장한다.[^agent-skills-spec]

```text
startup
  → name + description
activation
  → SKILL.md instructions
as needed
  → references / scripts / assets
```

전체 `SKILL.md`는 activation 후 context에 통째로 들어오므로, 항상 필요한 decision contract만 entrypoint에 두고 특정 상황의 세부사항은 reference로 분리하는 것이 좋다.

Repository의 agent-asset guidance 역시 다음을 권장한다.[^mols-skill-authoring]

- smallest deployable Skill package
- conditional detail은 explicit load condition 뒤에 배치
- repository-only verification material을 runtime Skill에 억지로 넣지 않음
- source/target-specific behavior를 portable guidance로 일반화하지 않음
- generated target projection을 canonical source로 착각하지 않음

이 원칙은 context-noise를 줄일 뿐 아니라 중요한 scope/authority rule이 긴 procedural prose에 묻히는 것을 방지한다.

### F9. Tool permission과 capability는 prompt boundary보다 강한 방어선이 될 수 있다

GitHub custom agent는 `tools` field를 생략하면 available tools 전체에 접근할 수 있다. 반대로 explicit tool list를 주면 agent가 사용할 capability를 제한할 수 있다.[^copilot-agent-tools]

현재 project reviewer agent가 좋은 예다.

- `review-adversarial`: `[read, search]`
- `review-quality`: read/search + test-specific capability
- `review-lead`: `[read, search, agent]`

Reviewer에게 edit/general shell capability를 주지 않음으로써 "reviewer가 implementation 또는 deterministic maintenance를 직접 수행"하는 failure class의 blast radius를 줄인다.

이것은 중요한 설계 원칙이다.

> **Prose says what the agent should do. Capability design limits what it can do.**

금지 문장만 추가하는 것보다 tool surface를 최소화하는 것이 더 강한 control일 수 있다.

### F10. Deterministic mechanics는 LLM instruction이 아니라 deterministic owner가 가져야 한다

`mols-agent-asset`은 semantic decisions는 readable instructions에 두되 deterministic mechanics나 runtime resource는 concrete benefit이 있을 때 사용하도록 한다.[^mols-agent-asset]

Agent Skills도 `scripts/`를 지원하지만, script는 self-contained dependency와 명확한 error handling을 가져야 한다.[^agent-skills-spec]

PR #205에서 사용자가 지적한 "스크립트로 자동화할 일을 agent가 직접 수행" 문제에 적용하면 원칙은 다음과 같다.

```text
semantic decision
→ instruction / Skill

mechanical repeatable transformation
→ script / formatter / generator / validator

reviewer
→ deterministic owner를 실행·검증하거나 not-run으로 보고
→ owner를 수동으로 흉내 내지 않음
```

이 경계를 instruction으로만 표현하지 말고 가능하면 tool permission과 repository-native command surface로도 강화해야 한다.

### F11. Agent instruction을 고칠 때는 "더 많은 규칙"보다 failure-preventing contract를 우선해야 한다

`mols-agent-asset-validator`의 performance review는 좋은 instruction이 다음 중 하나를 해야 한다고 본다.[^asset-performance]

- material failure 방지
- stable authority/safety/quality boundary 정의
- project-specific fact/practice 제공
- required output/handoff contract 보존

반대로 다음은 instruction bottleneck 후보다.

- 상식적 절차를 지나치게 세세하게 강제
- 목적/경계보다 중간 단계와 표현을 과도하게 통제
- 같은 rule을 여러 asset에 복제
- exception의 exception 누적
- 중요한 authority rule을 낮은 가치 prose가 가림

즉 PR #205를 보고 여러 Skill과 agent에 동시에 `범위를 벗어나지 마라`를 추가하는 것은 오히려 signal dilution을 만들 수 있다.

더 나은 방향은 **한 곳에서 scope ownership을 결정하고, 다음 owner에게 machine-readable 수준으로 handoff하며, 각 layer는 자기 책임만 enforce**하는 것이다.

### F12. Review loop에는 finding admission contract와 semantic stop condition이 필요하다

Anthropic의 agent engineering guidance도 evaluator-optimizer loop는 **명확한 evaluation criteria가 있고 iterative refinement가 실제로 measurable improvement를 만들 때** 적합하다고 설명한다. Autonomous agent에는 stopping condition을 두는 것이 일반적이며, 복잡성은 outcome을 실제로 개선할 때만 추가해야 한다.[^anthropic-agents]

`mols-agent-asset-validator`는 loop 자체를 다음처럼 정의한다.[^asset-validator][^asset-reconciliation]

- 각 loop는 materially different review lens 또는 new evidence를 가져야 함
- 단순 재독, 요약, 동일 검사 재실행은 새 loop로 세지 않음
- completion criteria를 충족하면 auto loop는 조기 종료 가능
- reviewer 다수결이나 loop 횟수로 truth를 결정하지 않음
- 추가 loop가 새로운 evidence/challenge를 만들 가능성이 낮으면 종료

따라서 PR #205 같은 review loop에는 두 종류의 stop control이 필요하다.

1. **Hard ceiling:** runaway를 막는 안전 상한
2. **Semantic completion:** 새로운 material in-scope evidence 또는 credible continuation이 없으면 종료

`2회면 무조건 종료` 같은 횟수 규칙만 사용하면 두 번째 review에서 발견되는 실제 regression을 놓칠 수 있다.

## PR #205: Working Failure Model

현재 evidence를 바탕으로 한 가장 유력한 working model은 다음과 같다.

```text
Implementation Owner
    │
    │ target + scope + contract
    ▼
Review Lead
    │
    ├── Quality candidate
    └── Adversarial candidate
            │
            ▼
     Reconciliation
            │
            ▼
   clear / changes_required / blocked
            │
            ▼
Implementation Workflow
            │
            ├─ finding classification 충분? ── yes ──► correct transition
            │
            └─ no
                 │
                 ▼
          all material finding
          → current remediation
                 │
                 ▼
             state change
                 │
                 ▼
             fresh review
```

현재 repository source에서 verified할 수 있는 것은 다음이다.

- Reviewer scope/exclusion contract는 이미 존재한다.
- Development gate는 `changes_required`를 implementation owner로 route한다.
- OpenSpec controller는 finding 종류에 따른 더 세밀한 transition model을 이미 갖고 있다.
- PR #205에서는 `clear` 이후 OpenSpec contract가 실제로 확대됐다.

현재 아직 unknown인 것은 다음이다.

- 각 historical review invocation에서 실제 brief가 어떻게 전달됐는가.
- 각 specialist가 어떤 candidate를 어떤 evidence로 반환했는가.
- Lead가 candidate를 어떻게 `changes_required`로 승격했는가.
- Main agent가 각 finding을 current remediation으로 분류한 explicit reasoning/transition record가 있었는가.

이 unknown을 확인하는 데 Chronicle/session history가 가장 가치 있는 evidence source다.

## Recommended Agent-Asset Engineering Lifecycle

Agent instruction이나 Skill을 새로 만들거나 개선할 때 다음 lifecycle을 권장한다.

### Phase 1 — Observe the Failure

먼저 실제 failure를 수집한다.

Evidence 후보:

- `/chronicle search <keyword>`
- `/chronicle improve`
- session transcript / tool trace
- Git commit history
- PR review output
- user correction
- failed validation
- unexpected file mutation

기록할 최소 단위:

```yaml
case_id: <stable id>
task: <original intent>
runtime: <copilot cli | vscode | cloud agent | ...>
revision: <sha or state>
expected_behavior: <observable behavior>
observed_behavior: <observable behavior>
user_correction: <if any>
tools_used: <relevant tool calls>
state_changes: <files / git / external state>
```

중요한 것은 "agent가 이상했다"가 아니라 **어떤 input/context에서 어떤 observable wrong transition이 발생했는지** 남기는 것이다.

### Phase 2 — Reconstruct Authority and Scope

Failure 시점의 authority를 복원한다.

```text
User request
Project instruction
Repository instruction
Active Change / PR scope
Selected Skill
Custom agent
Tool permission
Runtime limitation
```

질문:

- Current Goal은 무엇이었는가.
- Explicit In Scope / Out of Scope는 무엇이었는가.
- Agent가 읽은 external context는 target인가 supporting evidence인가.
- Scope를 바꿀 authority는 누구에게 있었는가.
- Finding이 implementation authority를 얻은 순간은 어디인가.

최종 state를 과거에 소급하지 않는다.

### Phase 3 — Identify the First Failure Point

다음 chain에서 **최초로 contract가 깨진 지점**을 찾는다.

```text
Trigger
→ Routing
→ Context loading
→ Scope handoff
→ Agent decision
→ Tool selection
→ Candidate output
→ Reconciliation
→ Workflow transition
→ Mutation
→ Validation
→ Termination
```

후속 layer가 잘못을 막지 못했더라도 primary owner와 defense-in-depth owner를 구분한다.

예:

| Scenario | Primary Owner | Secondary Defense |
| --- | --- | --- |
| caller가 scope를 전달하지 않음 | caller/workflow | reviewer ambiguity handling |
| scope 전달됐는데 specialist가 unrelated issue 승격 | specialist/lead | workflow admission |
| reviewer가 follow-up이라고 했는데 caller가 수정 | caller/workflow | none needed in reviewer |
| deterministic script 있는데 reviewer가 수동 변환 | tool/capability/workflow | reviewer instruction |

### Phase 4 — Choose the Correct Asset Surface

다음 decision tree를 사용한다.

```text
Is it true for nearly every task in this scope?
├─ yes → AGENTS / custom instruction / Rule
└─ no
    │
    Is applicability based on task intent?
    ├─ yes → Skill
    └─ no
        │
        Does it define a specialized role + tool surface?
        ├─ yes → custom agent
        └─ no
            │
            Is it deterministic/mechanical?
            ├─ yes → script / validator / tool / hook
            └─ no → existing nearest owner를 먼저 재검토
```

새 asset은 마지막 선택지다. 기존 owner를 확장할 수 있으면 competing source를 만들지 않는다.

### Phase 5 — Write a Behavior Contract before Prose

문장을 쓰기 전에 contract를 먼저 작성한다.

```yaml
responsibility: <what this asset owns>
trigger: <when it activates>
negative_trigger: <when it must not activate>
inputs: <authoritative inputs>
context: <supporting context it may inspect>
authority: <what decisions it may make>
write_boundary: <what state it may mutate>
tools: <minimum capabilities>
output: <required semantic result>
transitions: <who acts on each output type>
stop_condition: <when it must stop>
failure_mode: <blocked / unknown / handoff behavior>
```

이 contract가 먼저 있어야 prose가 모호해지지 않는다.

### Phase 6 — Encode the Smallest Coherent Change

작성 원칙:

- 중요한 rule은 한 owner에 둔다.
- 기존 owner의 책임을 유지하면서 필요한 behavior만 추가한다.
- target-runtime-specific field는 runtime owner 문서를 확인한다.
- Skill entrypoint에는 항상 필요한 decision만 둔다.
- detailed edge case는 reference로 progressive disclosure한다.
- mechanical reconciliation은 script/tool로 이동한다.
- tool permission은 최소화한다.
- generated projection을 직접 고치지 않는다.

### Phase 7 — Build Evals before Declaring Success

Agent asset change는 prose review만으로 완료하면 안 된다.

최소 fixture set:

| Case | Purpose |
| --- | --- |
| Positive | 정상 activation과 expected behavior |
| Negative | activation하면 안 되는 request |
| Near-miss | 비슷하지만 다른 owner가 맞는 request |
| Scope boundary | supporting context에서 unrelated issue 발견 |
| Causal external | diff 밖 consumer가 current change 때문에 깨짐 |
| Missing context | 필요한 target/scope가 없음 |
| Tool denied | 필요한 capability가 없음 |
| Adversarial | prompt injection / hostile input / misleading artifact |
| Re-review | prior finding resolved 후 fresh snapshot |
| Saturation | 새 evidence 없이 review 요청 반복 |

PR #205 문제에 특화된 fixture는 다음이 적절하다.

| Case | Expected Result |
| --- | --- |
| PR target 안의 real regression | current finding |
| diff 밖 consumer의 causal regression | current finding |
| adjacent pre-existing defect | exclude / follow-up |
| same-change scope gap | `scope_gap`, auto implementation 금지 |
| independent new requirement | follow-up Change |
| external blocker | blocker |
| reviewer가 script-owned task 발견 | mismatch report, manual substitution 금지 |
| repeated review + no new material evidence | semantic completion / saturation |

### Phase 8 — Use Paired and Baseline Tests

Instruction change가 실제 원인에 영향을 줬는지 보려면 paired test가 중요하다.

예:

```text
Case A: ambiguous scope brief
Case B: explicit scope brief
```

동일 reviewer가 A에서 drift하고 B에서 안정적이면 handoff가 주요 변수다.

```text
Baseline: current agent asset
Candidate: modified asset
```

같은 fixture set에서 다음을 비교한다.

- target fidelity
- causal regression recall
- unrelated finding rate
- unauthorized remediation rate
- tool misuse rate
- loop count / termination quality

한 번의 성공은 behavioral stability proof가 아니다. 실제 runtime executor가 있으면 중요한 case는 repeated trial을 사용하고 variance를 기록한다.[^asset-validator][^anthropic-evals]

### Phase 9 — Reconcile Evidence, Not Votes

여러 reviewer를 사용하더라도 다수결로 truth를 정하지 않는다.

각 candidate finding은 다음을 가져야 한다.

```yaml
finding_id: <id>
claim: <problem>
evidence_level: verified | simulated | inferred | unknown
scope_relation: explicit_target | direct_regression | contract_dependency | acceptance_gap | scope_gap | independent_requirement | unrelated | unknown
impact: <material impact>
disposition: current_required | blocker | follow_up | unknown | reject
owner: <next owner>
```

이 schema 자체를 바로 repository 표준으로 만들자는 제안은 아니다. 다만 **review → workflow transition 사이에서 사라지면 안 되는 의미**를 보여준다.

### Phase 10 — Validate in the Actual Runtime

Static inspection은 다음을 검증할 수 있다.

- syntax
- link/reference
- ownership
- trigger wording
- explicit scope
- tool configuration

하지만 다음은 runtime evidence가 필요하다.

- Skill이 실제로 선택되는가.
- custom agent가 tool boundary를 지키는가.
- same prompt에서 behavior가 안정적인가.
- subagent handoff가 scope를 보존하는가.
- termination 조건이 실제 loop에서 작동하는가.

GitHub도 custom instructions가 AI의 non-deterministic 특성 때문에 매번 동일하게 따라지지 않을 수 있다고 명시한다.[^copilot-instructions]

따라서 "instruction을 읽어보니 명확하다"는 self-review와 "runtime에서 behavior가 개선됐다"는 verification을 분리해야 한다.

## What Chronicle Should Capture for Future Agent Work

Agent asset을 지속적으로 개선하려면 Chronicle 사용도 구조화하는 것이 좋다.

### Before Change

찾을 것:

- 같은 user correction이 몇 번 반복됐는가.
- 같은 tool misuse가 반복됐는가.
- 어떤 task intent에서 routing이 흔들렸는가.
- 어느 handoff 뒤에 scope drift가 나타났는가.
- 사용자 개입 없이 종료된 성공 사례와 실패 사례의 차이는 무엇인가.

추천 query 예시:

```text
/chronicle search "범위 밖"
/chronicle search "review-lead"
/chronicle search "changes_required"
/chronicle search "다시 리뷰"
/chronicle search "script"
/chronicle improve
```

### After Change

동일 failure pattern이 재발하는지 확인한다.

```text
baseline period
→ instruction/Skill change
→ comparable tasks
→ same Chronicle search
→ recurrence / correction count 비교
```

단순히 `/chronicle improve`가 새 문장을 추천하지 않는다고 성공으로 보지 않는다. 실제 target task의 behavior와 state transition을 확인한다.

## Design Guidance by Asset Type

### Custom Instructions / AGENTS / Rules

적합한 내용:

- stable repository facts
- always-applicable safety/authority boundary
- path-specific invariant
- build/test command ownership
- cross-task convention

피해야 할 내용:

- 특정 task에서만 필요한 긴 workflow
- 모든 edge case 목록
- 자주 바뀌는 vendor behavior 복제
- deterministic script가 소유할 mechanics

좋은 문장 특성:

- self-contained
- 주체와 행동이 명확함
- condition / exception / outcome이 가까이 있음
- "하지 마라"만이 아니라 올바른 owner/handoff를 함께 제시

### Agent Skills

적합한 내용:

- task-selected workflow
- specialized decision procedure
- optional reference, example, script
- repeated capability

핵심 작성 순서:

1. `name`
2. routing-quality `description`
3. responsibility / trigger / boundary
4. minimal workflow
5. completion / failure / handoff
6. conditional references
7. scripts/assets only when materially useful

Agent Skills open spec는 `description`이 what + when을 설명하고, agent가 relevant Skill을 찾는 데 도움이 되는 specific keyword를 포함하도록 권장한다.[^agent-skills-spec]

### Custom Agents / Subagents

적합한 내용:

- specialized role
- isolated context가 필요한 independent perspective
- specific tool permission
- stable return contract
- delegation relationship

반드시 정의할 것:

- caller
- allowed subagents
- tool list
- mutation authority
- input brief
- output semantics
- final decision owner
- failure/coverage gap behavior

Reviewer처럼 read-only 역할이면 edit/shell을 기본 제공하지 않는 것이 안전하다.

### Tools, Scripts and Hooks

적합한 내용:

- repeatable deterministic transformation
- validation
- synchronization
- formatting
- generated output
- policy enforcement that can be machine checked

Agent-facing tool description도 prompt engineering 대상이다. Tool name, argument, error message와 output context가 잘 설계되어야 하며, tool interface 자체를 mistake-resistant하게 만드는 것이 중요하다는 실무 guidance가 있다.[^anthropic-tools]

## Recommended Evaluation Matrix for Review-Scope Work

다음 matrix를 reviewer/workflow 자산 변경 전 regression suite 후보로 권장한다.

| ID | Input Condition | Expected Review | Expected Workflow |
| --- | --- | --- | --- |
| R1 | explicit PR target, defect inside diff | finding | current remediation |
| R2 | unchanged consumer breaks because of PR | finding | current remediation |
| R3 | adjacent old defect, no causal relation | no current finding | no remediation |
| R4 | same-change acceptance requires scope expansion | `scope_gap` | Scope Control, no immediate Apply |
| R5 | independent improvement | follow-up | separate Change / issue candidate |
| R6 | current Goal blocked by external dependency | blocker | user/owner decision |
| R7 | ambiguous target with multiple active Changes | blocked/unknown | no arbitrary selection |
| R8 | deterministic generator mismatch | finding/validation gap | owner script, reviewer no manual edit |
| R9 | reviewer lacks runtime capability | limitation | no workaround claim |
| R10 | second/third review produces no new material evidence | no new finding | COMPLETE / saturation |
| R11 | adversarial extreme case not reachable | reject hypothesis | no remediation |
| R12 | adversarial unusual case is reachable and violates acceptance | finding | current remediation |

이 matrix의 핵심은 **scope precision만 높이는 것이 아니라 causal recall을 같이 보존**하는 것이다.

## Metrics

Agent asset 개선을 평가할 때 다음을 권장한다.

| Metric | Desired Direction |
| --- | --- |
| Target Fidelity | 100%에 가깝게 |
| Unrelated Finding Rate | 0% |
| Causal Regression Recall | designed positive cases에서 100% |
| Unauthorized Scope Expansion | 0 |
| Out-of-Scope Remediation | 0 |
| Manual Automation Substitution | 0 |
| Reviewer Mutation | 0 |
| Handoff Completeness | 증가 |
| Correct Disposition Rate | 증가 |
| Meaningful Loop Ratio | 증가 |
| User Correction Recurrence | 감소 |

Metric은 단독 score가 아니라 failure mode를 찾는 관찰 도구로 사용한다.

## Likely Change Points for This Repository

현재 조사만으로 실제 수정 위치를 확정하지는 않는다. 다만 evidence가 강한 후보 순서는 다음과 같다.

### Candidate A — Finding Admission Contract

가장 먼저 검토할 후보는 `review-lead → caller` handoff다.

현재 final assessment가 `clear / changes_required / blocked`인 것은 유지할 수 있지만, material finding마다 최소 다음 의미를 추가하는 방안을 eval할 가치가 있다.

```text
scope relation
+ disposition
+ required owner
```

예:

```yaml
scope_relation: same_change_scope_gap
disposition: scope_control
owner: openspec_workflow
```

이렇게 하면 `changes_required`가 "모두 지금 구현"으로 압축되는 것을 막을 수 있다.

### Candidate B — Caller Transition Contract

Generic development workflow는 `changes_required → implementation owner`만으로 끝내지 않고, caller가 finding disposition을 재해석하지 않도록 명시적 transition table을 가질 필요가 있는지 검증해야 한다.

OpenSpec workflow가 이미 더 풍부한 transition model을 갖고 있으므로, generic workflow가 이를 복제하기보다는 **current owning workflow가 finding type을 처리한다는 handoff contract**를 명확히 하는 방향이 더 작을 수 있다.

### Candidate C — Specialist Candidate Contract

Quality/adversarial specialist에게 무조건 더 많은 scope 문장을 넣기보다 candidate hypothesis마다 `current target과의 causal relation`을 evidence로 반환하도록 하는 것이 실제 drift를 줄이는지 paired eval한다.

### Candidate D — Loop Termination

Review 횟수 hard cap보다 다음 조건을 검증한다.

- 새 material evidence 없음
- accepted scope 안의 unresolved finding 없음
- continuation이 같은 finding 재서술뿐임
- next work가 independent requirement뿐임

이때 current work를 COMPLETE하고 follow-up을 분리할 수 있어야 한다.

### Candidate E — Automation Ownership

Reviewer asset과 workflow에서 "repository-native deterministic owner가 존재하면 실행 또는 not-run; manual emulation 금지"가 실제 tool surface와 함께 enforcement되는지 검증한다.

## What Not to Do

이번 조사에서 특히 피해야 할 수정 패턴은 다음이다.

1. 모든 reviewer/Skill에 같은 `scope를 지켜라` 문장 복제
2. PR #205 한 사건만 보고 모든 review를 changed-files-only로 제한
3. 두 번 review하면 무조건 종료
4. adversarial reviewer 제거
5. reviewer tool을 넓혀 검증 못한 작업을 shell로 우회
6. Chronicle suggestion을 검증 없이 바로 canonical instruction으로 채택
7. `.github/agents` 같은 target surface를 canonical source 확인 없이 직접 수정
8. eval 없이 prompt wording만 바꾸고 "개선됨"으로 종료
9. success case만 테스트하고 unrelated/near-miss case를 빼기
10. model behavior 문제를 deterministic automation으로 해결할 수 있는데 prose를 늘리기

## Conclusion

PR #205 incident와 current agent assets를 함께 보면, 이번 개선의 핵심은 **reviewer에게 더 엄격한 문장을 추가하는 것 자체가 아니다.** 이미 reviewer에는 bounded target과 unrelated issue exclusion이 상당 부분 존재한다.

더 중요한 engineering problem은 다음 세 가지다.

1. **Scope가 handoff 전체에서 보존되는가.**
2. **Candidate finding이 current remediation authority를 얻는 admission 단계가 명확한가.**
3. **State change → re-review loop가 새로운 material evidence가 없을 때 종료되는가.**

Agent instruction과 Skill을 만들 때도 같은 원칙을 적용해야 한다.

```text
Observe
→ Reconstruct authority
→ Find first failure
→ Choose owner/surface
→ Write behavior contract
→ Make smallest change
→ Eval positive + negative + near-miss + adversarial
→ Verify in runtime
→ Chronicle recurrence check
```

이 lifecycle을 사용하면 `한 번 실패 → 문장 하나 추가 → 또 실패 → 문장 하나 추가` 형태의 instruction accretion을 피할 수 있다.

### Next Step

실제 agent/Skill 변경 전에 다음 두 artifact를 만드는 것이 가장 유용하다.

1. **PR #205 Historical Review Cycle Matrix**
   - review revision
   - caller brief
   - specialist candidate
   - lead disposition
   - scope relation
   - caller transition
   - resulting mutation

2. **Review Scope Behavioral Eval Fixture Set**
   - 이 보고서의 `R1~R12` case를 executable 또는 repeatable scenario로 구체화
   - current asset을 baseline으로 먼저 실행
   - 그 뒤 candidate change를 동일 fixture로 비교

이 두 evidence가 있어야 `review-lead`, workflow Skill, specialist agent 중 어디를 실제로 수정할지 근거 있게 결정할 수 있다.

## Open Questions

| Question | Why It Matters | Next Step |
| --- | --- | --- |
| PR #205 각 review invocation의 actual brief는 무엇이었나 | handoff failure와 reviewer failure 구분 | Chronicle/session history에서 review-lead 호출 전후 검색 |
| specialist output에 causal relation evidence가 있었나 | specialist contract 변경 필요성 판단 | Chronicle에서 quality/adversarial 결과 복원 |
| lead가 어떤 candidate를 `changes_required`로 승격했나 | reconciliation owner 판단 | review-lead output 복원 |
| main agent가 finding을 어떤 기준으로 수정했나 | admission failure 여부 확정 | finding 이후 tool/file mutation chronology 복원 |
| `.github/agents` reviewer profile의 canonical authoring owner는 어디인가 | 잘못된 projection 직접 수정 방지 | Rulesync/source ownership을 mutation 전에 재확인 |
| runtime별 reviewer capability가 동일한가 | instruction과 capability gap 분리 | VS Code/Copilot CLI/cloud agent target behavior 확인 |

## References

[^research-evidence]: `.rulesync/skills/prj-research-workspace/references/evidence.md` — evidence classes, source quality와 traceability.
[^review-lead]: `.github/agents/review-lead.agent.md` at PR #205 head — bounded brief, candidate reconciliation, final assessment와 review boundary.
[^review-quality]: `.github/agents/review-quality.agent.md` at PR #205 head — causal integration inspection, unrelated defect exclusion, test-specific validation boundary.
[^review-adversarial]: `.github/agents/review-adversarial.agent.md` at PR #205 head — reachable/material adversarial hypotheses와 unrelated system-risk exclusion.
[^development-review-gate]: `.rulesync/skills/prj-load-context-development/SKILL.md` — independent review gate와 `changes_required → implementation owner → fresh review` transition.
[^openspec-rpi]: `.rulesync/skills/prj-spec-driven-tdd-rpi/SKILL.md` — Active Scope, Review transition, Scope Control, independent requirement와 saturation contract.
[^pr205-commits]: PR #205 commit history, especially `a32062b41b9fde12b9d6e69c9721fa5e42f8f635` (`review-lead ... clear`) and later remediation commits.
[^a320-orchestration]: `openspec/changes/orchestration-quality-gate/proposal.md` at `a32062b41b9fde12b9d6e69c9721fa5e42f8f635`.
[^final-orchestration]: `openspec/changes/orchestration-quality-gate/proposal.md` at `80781a17f36a0b2d2d4d172d9bc723dde24d9b65`.
[^a320-synthetic]: `openspec/changes/reliability-synthetic-2026-evaluation/proposal.md` at `a32062b41b9fde12b9d6e69c9721fa5e42f8f635`.
[^final-synthetic]: `openspec/changes/reliability-synthetic-2026-evaluation/proposal.md` at `80781a17f36a0b2d2d4d172d9bc723dde24d9b65`.
[^chronicle-concept]: GitHub Docs, [About GitHub Copilot CLI session data](https://docs.github.com/en/copilot/concepts/agents/copilot-cli/chronicle), accessed 2026-09-04.
[^chronicle-howto]: GitHub Docs, [Using GitHub Copilot CLI session data](https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/chronicle), accessed 2026-09-04.
[^agent-surface]: `docs/development/ai-agent/README.md` and `docs/development/ai-agent/skill.md` — project agent surface selection and Skill ownership.
[^copilot-customization]: GitHub Docs, [Copilot customization cheat sheet](https://docs.github.com/en/copilot/reference/customization-cheat-sheet), accessed 2026-09-04.
[^agent-skills-spec]: Agent Skills, [Specification](https://agentskills.io/specification), accessed 2026-09-04; GitHub Docs, [Adding agent skills for GitHub Copilot](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills), accessed 2026-09-04.
[^mols-agent-asset]: `mols-agent-assets` revision `3882d2fef90b427a2117420b62db70bdae23a557`, `mols-agent-asset/SKILL.md` — responsibility-first authoring, smallest coherent owner change and source/target authority.
[^mols-skill-authoring]: `mols-agent-assets` revision `3882d2fef90b427a2117420b62db70bdae23a557`, `mols-agent-asset/references/skill.md` — Skill package, progressive disclosure and source/target ownership.
[^copilot-agent-tools]: GitHub Docs, [Custom agents configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration), accessed 2026-09-04.
[^asset-performance]: `mols-agent-assets` revision `3882d2fef90b427a2117420b62db70bdae23a557`, `mols-agent-asset-validator/references/performance-review.md` — instruction bottleneck, context noise, stability and human comprehension debt.
[^anthropic-agents]: Anthropic Engineering, [Building Effective AI Agents](https://www.anthropic.com/engineering/building-effective-agents), published 2024-12-19.
[^asset-validator]: `mols-agent-assets` revision `3882d2fef90b427a2117420b62db70bdae23a557`, `mols-agent-asset-validator/SKILL.md` — evidence levels, validation axes, loop contract, completion and disposition.
[^asset-reconciliation]: `mols-agent-assets` revision `3882d2fef90b427a2117420b62db70bdae23a557`, `mols-agent-asset-validator/references/reconciliation.md` — evidence-led reconciliation and Loop Ledger.
[^anthropic-evals]: Anthropic Engineering, [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents), published 2026-01-09.
[^copilot-instructions]: GitHub Docs, [About customizing GitHub Copilot responses](https://docs.github.com/en/copilot/concepts/prompting/response-customization), accessed 2026-09-04.
[^anthropic-tools]: Anthropic Engineering, [Writing effective tools for AI agents](https://www.anthropic.com/engineering/writing-tools-for-agents), accessed 2026-09-04.
