---
type: plan
title: "PR #245 Staged Closure Plan"
description: "PR #245를 현재 contract의 correctness와 scope만으로 닫고, Langfuse 후속 작업을 별도 transition으로 분리하는 단계별 계획입니다."
tags:
  - "domain:review-ai"
  - "capability:reliability-agentic-review"
  - "pull-request"
  - "evaluation"
  - "closure"
---

# PR #245 Staged Closure Plan

이 bundle은 PR #245를 **현재 contract의 correctness와 scope만으로 닫는 계획**이다. Langfuse 도입은 #245를 더 일반화해야 하는 이유가 아니며, merge 뒤 canonical OpenSpec transition을 확인한 다음 별도 work unit에서 판단한다.

실행 순서는 **OpenSpec preflight → correctness → contract/scope → final evidence → readiness/merge**다. 같은 session에서 여러 단계를 진행할 수 있지만 각 단계의 gate를 따로 확인한다. Material state가 바뀌면 영향을 받는 가장 이른 gate부터 다시 검증한다.

PR #245 closure는 12에서 끝난다. [`13-verify-openspec-before-langfuse.md`](13-verify-openspec-before-langfuse.md)는 post-merge transition gate이고, [`14-langfuse-next-pr.md`](14-langfuse-next-pr.md)는 그 이후 새 work unit을 시작하기 위한 seed다.

## Current Basis

현재 판단 우선순위는 다음과 같다.

1. current repository guidance, canonical OpenSpec, source, tests와 live PR state
2. [`../18-review-review-ai-high-confidence/README.md`](../18-review-review-ai-high-confidence/README.md)와 [`../18-review-review-ai-high-confidence/evidence-map.md`](../18-review-review-ai-high-confidence/evidence-map.md)
3. 이 closure bundle

[`../12-proposal-review-ai-utility-evaluation-remediation-and-simplification.md`](../12-proposal-review-ai-utility-evaluation-remediation-and-simplification.md)와 더 오래된 Inbox artifact는 historical context다. Current source/spec/review와 충돌하면 현재 source를 따른다.

## Scope Filter

#245에서 수행할 작업은 다음 질문을 모두 통과해야 한다.

1. 현재 #245의 requirement 또는 reachable correctness defect를 직접 닫는가?
1. Langfuse가 없어도 필요한가?
1. 더 작은 existing contract/test 수정으로 해결할 수 없는가?

하나라도 `no`라면 기본적으로 #245에서 하지 않는다.

특히 다음은 **Langfuse를 예상한다는 이유만으로 #245에 추가하지 않는다.**

- generic evaluator/backend/plugin abstraction
- repository-native human-score 입력 UI 또는 CLI
- standalone evaluation persistence API
- Langfuse trace/score ID를 core contract에 추가하는 작업
- provider `trace_id`의 의미 변경
- dataset/experiment registry
- two-way synchronization framework
- `output_fixture_id` optionalization 또는 새 evaluation source abstraction
- rubric score anchor를 새 schema로 일반화하는 작업

마지막 두 항목이 **현재 #245 contract 자체를 거짓되거나 unusable하게 만드는 문제**로 확인되면 Langfuse와 무관한 contract defect로 다시 분류할 수 있다. 단순한 future integration 편의는 merge blocker가 아니다.

## Execution Rule

1. 현재 단계의 파일 하나를 선택한다.
1. 시작 전에 current HEAD, base/main relation과 prerequisites를 확인한다.
1. Scope Filter를 통과하는 가장 작은 coherent change만 수행한다.
1. focused validation과 Done When을 확인한다.
1. 실패하면 실제 owner로 돌아가 수정하거나 blocker를 남긴다.
1. 다음 단계에 필요한 material gap이 없을 때만 진행한다.

## Stage 0 — OpenSpec Preflight

| Order | Work | Gate |
| --- | --- | --- |
| 00 | [`00-revalidate-openspec-planning.md`](00-revalidate-openspec-planning.md) | F1–F3이 current HEAD에서 재확인되고 owning planning/task state가 actual remediation을 허용 |

**Stage 0 Gate:** active `spec-driven-tdd` Change가 code-facing remediation lifecycle을 소유한다. Future Langfuse compatibility를 위한 새 requirement를 만들지 않는다.

## Stage 1 — Correctness

| Order | Work | Gate |
| --- | --- | --- |
| 01 | [`01-fix-context-overflow.md`](01-fix-context-overflow.md) | Context overflow가 typed rejection으로 닫힘 |
| 02 | [`02-complete-quality-basis-controls.md`](02-complete-quality-basis-controls.md) | Durable basis가 required control semantics를 모두 증명 |
| 03 | [`03-align-bounded-evidence-refs.md`](03-align-bounded-evidence-refs.md) | Prompt-visible ID와 validator allowlist가 일치 |
| 04 | [`04-lock-negative-regressions.md`](04-lock-negative-regressions.md) | F1–F3 negative path가 regression proof로 고정 |

**Stage 1 Gate:** current correctness defect와 owning OpenSpec task가 닫히고 focused tests가 통과한다. Langfuse 관련 코드나 abstraction은 없다.

## Stage 2 — Contract and Scope

| Order | Work | Gate |
| --- | --- | --- |
| 05 | [`05-reconcile-openspec-after-apply.md`](05-reconcile-openspec-after-apply.md) | Planning artifacts, task state, implementation과 tests가 같은 current contract를 설명 |
| 06 | [`06-resolve-eli5-scope.md`](06-resolve-eli5-scope.md) | ELI5 repository-level 변경의 유지/제거가 #245 필요성으로 결정되고 diff가 coherent함 |

[`07-refresh-inbox-navigation.md`](07-refresh-inbox-navigation.md)는 non-blocking hygiene다. 실제 handoff를 방해할 때만 수행한다.

**Stage 2 Gate:** PR diff가 Review AI utility-evaluation change만으로 설명되고 OpenSpec/source/tests에 알려진 semantic drift가 없다. Future Langfuse integration을 편하게 만들기 위한 speculative contract change가 남아 있지 않다.

## Stage 3 — Freeze and Closure Evidence

| Order | Work | Gate |
| --- | --- | --- |
| 08 | [`08-run-final-validation.md`](08-run-final-validation.md) | Candidate HEAD가 freeze되고 current validation evidence 존재 |
| 09 | [`09-refresh-pr-description.md`](09-refresh-pr-description.md) | PR body가 frozen HEAD의 exact state와 validation을 설명 |
| 10 | [`10-run-fresh-review.md`](10-run-fresh-review.md) | Frozen HEAD의 non-mutating fresh review에 blocking finding 없음 |

**Stage 3 Gate:** 08 이후 tracked file을 변경하면 freeze가 깨지고 08부터 다시 수행한다. Fresh review는 correctness와 scope를 검토하되 future Langfuse convenience를 이유로 새 abstraction을 요구하지 않는다.

## Stage 4 — Readiness and Merge

| Order | Work | Gate |
| --- | --- | --- |
| 11 | [`11-assess-review-readiness.md`](11-assess-review-readiness.md) | Repository 기준으로 `ready` 판정 가능 |
| 12 | [`12-merge-pr-245.md`](12-merge-pr-245.md) | 명시적 인간 승인 후 merge 및 post-merge 확인 |

`ready`는 correctness approval이나 merge authorization이 아니다. Draft → Ready 또는 merge 같은 mutable lifecycle action은 해당 시점의 명시적 권한과 current state를 다시 확인한다.

## Post-Merge Transition Gate

| Order | Work | Gate |
| --- | --- | --- |
| 13 | [`13-verify-openspec-before-langfuse.md`](13-verify-openspec-before-langfuse.md) | #245의 durable spec-level behavior가 canonical OpenSpec에 반영되고 active change lifecycle이 정리됨 |

OpenSpec archive/sync가 별도 PR을 요구하면 그 작업이 Langfuse보다 먼저다. 이미 canonical하면 추가 maintenance PR을 만들지 않는다.

## Follow-Up Only

PR #245 merge와 13 완료 뒤에만 [`14-langfuse-next-pr.md`](14-langfuse-next-pr.md)를 사용한다. 14는 Langfuse 도입을 자동 승인하지 않는다. 현재 공식 integration surface를 조사하고, 실제로 줄어드는 수작업과 추가되는 복잡도를 비교해 가장 작은 vertical slice를 선택한다.

새 Langfuse branch/PR이 생기면 active planning은 그 새 work unit이 소유한다. 이 bundle은 historical handoff context로만 남긴다.

## Stop Conditions

다음 상황에서는 다음 단계로 진행하지 않는다.

- current HEAD에서 새로운 correctness blocker가 발견됨
- base/main divergence가 current remediation 또는 validation을 stale하게 만듦
- OpenSpec planning owner 또는 task state가 remediation과 불일치함
- Stage 1 defect를 고치기 위해 unrelated architecture redesign이 필요함
- Langfuse future compatibility만을 이유로 #245 scope가 늘어남
- final validation이 실패함
- frozen HEAD가 변경됨
- fresh review가 blocking finding을 남김
- base/head가 바뀌어 readiness evidence가 stale해짐
- Ready 전환 또는 merge에 필요한 인간 권한이 없음
- #245 merge 후 canonical OpenSpec state가 정리되지 않았는데 Langfuse 구현을 시작하려 함
