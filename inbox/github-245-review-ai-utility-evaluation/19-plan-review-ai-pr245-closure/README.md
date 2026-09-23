---
type: plan
title: "PR #245 Staged Closure Plan"
description: "PR #245를 Langfuse 후속 작업 전에 정확하게 닫기 위한 단계별 실행 계획과 각 작업의 완료 gate를 정의합니다."
tags:
  - "domain:review-ai"
  - "capability:reliability-agentic-review"
  - "pull-request"
  - "evaluation"
  - "closure"
---

# PR #245 Staged Closure Plan

이 bundle은 PR #245를 한 번에 크게 수정하지 않고 **OpenSpec preflight → correctness → scope/contract → final evidence → readiness/merge → canonicalization** 순서로 닫기 위한 실행 계획이다. 각 파일은 한 작업만 소유하고, 앞 단계의 gate를 통과하기 전에는 다음 단계의 consequential work를 시작하지 않는다.

같은 session에서 여러 단계를 연속 수행할 수는 있다. 다만 각 단계의 검증과 완료 조건을 별도로 확인하고, material state가 바뀌면 영향을 받는 이전 gate를 다시 검증한다.

Langfuse 도입은 이 bundle의 closure 작업이 아니다. PR #245 merge와 필요한 OpenSpec canonicalization이 끝난 뒤에만 [`14-langfuse-next-pr.md`](14-langfuse-next-pr.md)를 사용한다.

## Current Basis

현재 실행 판단은 다음 우선순위를 따른다.

1. current repository guidance, canonical OpenSpec, source, tests와 live PR state
2. [`../18-review-review-ai-high-confidence/README.md`](../18-review-review-ai-high-confidence/README.md)와 [`../18-review-review-ai-high-confidence/evidence-map.md`](../18-review-review-ai-high-confidence/evidence-map.md)
3. 이 closure bundle

[`../12-proposal-review-ai-utility-evaluation-remediation-and-simplification.md`](../12-proposal-review-ai-utility-evaluation-remediation-and-simplification.md)와 그보다 오래된 Inbox artifact는 historical context다. Current code/spec/review와 충돌하면 현재 source를 따른다.

## Execution Rule

1. 현재 단계의 파일 하나를 선택한다.
1. 시작 전에 current HEAD와 해당 단계의 prerequisites가 여전히 유효한지 확인한다.
1. 해당 파일의 scope 안에서 가장 작은 coherent change를 수행한다.
1. focused validation과 Done When을 확인한다.
1. 실패하면 같은 owning stage로 돌아가 수정하거나 blocker를 남긴다.
1. 완료된 뒤에만 다음 consequential stage로 진행한다.

## Stage 0 — OpenSpec Preflight

| Order | Work | Gate |
| --- | --- | --- |
| 00 | [`00-revalidate-openspec-planning.md`](00-revalidate-openspec-planning.md) | F1–F3이 current HEAD에서 재확인되고 owning planning/task state가 실제 remediation을 허용 |

**Stage 0 Gate:** active `spec-driven-tdd` Change가 code-facing remediation의 lifecycle owner다. 필요한 task reopen 또는 planning correction을 구현보다 먼저 반영한다.

## Stage 1 — Correctness

| Order | Work | Gate |
| --- | --- | --- |
| 01 | [`01-fix-context-overflow.md`](01-fix-context-overflow.md) | Context overflow가 typed rejection으로 닫힘 |
| 02 | [`02-complete-quality-basis-controls.md`](02-complete-quality-basis-controls.md) | Durable basis가 required control semantics를 모두 증명 |
| 03 | [`03-align-bounded-evidence-refs.md`](03-align-bounded-evidence-refs.md) | Prompt-visible ID와 validator allowlist가 일치 |
| 04 | [`04-lock-negative-regressions.md`](04-lock-negative-regressions.md) | F1–F3 negative path가 regression proof로 고정 |

**Stage 1 Gate:** current implementation defect와 owning OpenSpec task가 모두 닫히고 focused tests가 통과해야 한다.

## Stage 2 — Contract and Scope

| Order | Work | Gate |
| --- | --- | --- |
| 05 | [`05-reconcile-openspec-after-apply.md`](05-reconcile-openspec-after-apply.md) | Planning artifacts, task state, implementation과 tests가 같은 current contract를 설명 |
| 06 | [`06-resolve-eli5-scope.md`](06-resolve-eli5-scope.md) | ELI5 repository-level 변경의 유지/제거가 근거로 결정되고 diff가 coherent함 |

[`07-refresh-inbox-navigation.md`](07-refresh-inbox-navigation.md)는 non-blocking hygiene다. stale navigation이 실제 handoff를 방해할 때 수행하되, correctness와 merge readiness를 대신하지 않는다.

**Stage 2 Gate:** PR diff가 Review AI utility-evaluation change로 설명 가능하고 OpenSpec/source/tests 사이에 알려진 semantic drift가 없어야 한다.

## Stage 3 — Freeze and Closure Evidence

| Order | Work | Gate |
| --- | --- | --- |
| 08 | [`08-run-final-validation.md`](08-run-final-validation.md) | Candidate HEAD가 freeze되고 current validation evidence 존재 |
| 09 | [`09-refresh-pr-description.md`](09-refresh-pr-description.md) | PR body가 frozen HEAD의 exact state와 validation을 설명 |
| 10 | [`10-run-fresh-review.md`](10-run-fresh-review.md) | Frozen HEAD의 non-mutating fresh review에 blocking finding 없음 |

**Stage 3 Gate:** 08 이후 tracked file을 변경하면 candidate HEAD freeze가 깨진다. 그런 변경이 생기면 08부터 다시 수행한다. Fresh review 결과는 PR review/comment 등 HEAD를 바꾸지 않는 surface를 우선한다.

## Stage 4 — Readiness and Merge

| Order | Work | Gate |
| --- | --- | --- |
| 11 | [`11-assess-review-readiness.md`](11-assess-review-readiness.md) | Repository 기준으로 `ready` 판정 가능 |
| 12 | [`12-merge-pr-245.md`](12-merge-pr-245.md) | 명시적 인간 승인 후 merge 및 post-merge 확인 |

`ready`는 correctness approval이나 merge authorization이 아니다. Draft → Ready 또는 merge처럼 mutable lifecycle action은 해당 시점의 명시적 권한과 current state를 다시 확인한다.

## Stage 5 — Canonicalize Before Langfuse

| Order | Work | Gate |
| --- | --- | --- |
| 13 | [`13-canonicalize-openspec-before-langfuse.md`](13-canonicalize-openspec-before-langfuse.md) | #245의 durable spec-level behavior가 canonical OpenSpec에 반영되고 active change lifecycle이 정리됨 |

OpenSpec archive/sync가 repository workflow상 별도 PR을 요구하면 그 PR이 Langfuse보다 먼저다. #245 merge만으로 `changes/**`의 delta가 canonical `specs/**`가 되었다고 가정하지 않는다.

## Stage 6 — Follow-Up Only

PR #245 merge와 Stage 5가 완료된 뒤에만 [`14-langfuse-next-pr.md`](14-langfuse-next-pr.md)를 handoff seed로 사용한다. 새 Langfuse branch/PR이 생기면 active planning은 그 새 work unit이 소유하며, 이 파일은 historical handoff context로만 남긴다.

## Stop Conditions

다음 상황에서는 다음 단계로 진행하지 않는다.

- current HEAD에서 새로운 correctness blocker가 발견됨
- OpenSpec planning owner 또는 task state가 remediation과 불일치함
- Stage 1 defect를 고치기 위해 unrelated architecture redesign이 필요함
- final validation이 실패함
- frozen HEAD가 변경됨
- fresh review가 blocking finding을 남김
- base/head가 바뀌어 readiness evidence가 stale해짐
- Ready 전환 또는 merge에 필요한 인간 권한이 없음
- #245 merge 후 canonical OpenSpec state가 아직 정리되지 않았는데 Langfuse 구현을 시작하려 함
