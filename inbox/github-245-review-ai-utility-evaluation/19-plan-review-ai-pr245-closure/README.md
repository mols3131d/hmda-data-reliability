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

이 bundle은 PR #245를 한 번에 크게 수정하지 않고 **correctness → contract/scope → validation/review → readiness/merge** 순서로 닫기 위한 실행 계획이다. 각 파일은 한 작업만 소유하며, 앞 단계의 gate를 통과하기 전에는 다음 단계로 넘어가지 않는다.

Langfuse 도입은 이 bundle의 closure 작업이 아니다. PR #245가 실제로 병합된 뒤에만 [`13-langfuse-next-pr.md`](13-langfuse-next-pr.md)를 사용한다.

## Current Basis

- Owning PR: `#245 feat(review-ai): prove MVP utility evaluation`
- Review basis: [`../18-review-review-ai-high-confidence/README.md`](../18-review-review-ai-high-confidence/README.md)
- Detailed evidence: [`../18-review-review-ai-high-confidence/evidence-map.md`](../18-review-review-ai-high-confidence/evidence-map.md)
- Remediation direction: [`../12-proposal-review-ai-utility-evaluation-remediation-and-simplification.md`](../12-proposal-review-ai-utility-evaluation-remediation-and-simplification.md)

이 Inbox는 비정본 working context다. 실제 작업 시에는 현재 `main`, PR HEAD, canonical OpenSpec, code, tests와 repository guidance를 다시 확인한다. 이 문서의 SHA, finding 번호 또는 과거 validation 결과를 현재 사실로 자동 승계하지 않는다.

## Execution Rule

한 번의 작업 session에서 모든 파일을 처리하려고 하지 않는다.

1. 현재 단계의 파일 하나를 선택한다.
1. 해당 파일의 scope 밖 변경을 하지 않는다.
1. focused validation과 완료 조건을 확인한다.
1. 실패하면 같은 단계에서 수정하거나 blocker를 기록한다.
1. 완료된 뒤에만 다음 파일로 이동한다.

단계 사이에서 PR HEAD나 `main`이 materially 바뀌면 현재 상태를 다시 확인하고 필요한 검증을 반복한다.

## Stage 1 — Correctness

| Order | Work | Gate |
| --- | --- | --- |
| 01 | [`01-fix-context-overflow.md`](01-fix-context-overflow.md) | Context overflow가 typed rejection으로 닫힘 |
| 02 | [`02-complete-quality-basis-controls.md`](02-complete-quality-basis-controls.md) | Durable basis가 required control semantics를 모두 증명 |
| 03 | [`03-align-bounded-evidence-refs.md`](03-align-bounded-evidence-refs.md) | Prompt-visible ID와 validator allowlist가 일치 |
| 04 | [`04-lock-negative-regressions.md`](04-lock-negative-regressions.md) | F1-F3 negative path가 regression test로 고정 |

**Stage 1 Gate:** 18번 high-confidence review의 F1-F3에 대응하는 현재 구현 defect가 모두 수정되고 focused tests가 통과해야 한다. 하나라도 남으면 Stage 2로 가지 않는다.

## Stage 2 — Contract and Scope

| Order | Work | Gate |
| --- | --- | --- |
| 05 | [`05-reconcile-openspec-contract.md`](05-reconcile-openspec-contract.md) | Spec/tasks와 실제 구현·검증 상태가 일치 |
| 06 | [`06-clean-unrelated-eli5-scope.md`](06-clean-unrelated-eli5-scope.md) | PR에 불필요한 repository-wide asset 변경이 남지 않음 |
| 07 | [`07-refresh-inbox-navigation.md`](07-refresh-inbox-navigation.md) | Inbox navigation이 현재 artifact를 찾게 하되 status owner가 되지 않음 |

**Stage 2 Gate:** PR diff가 Review AI utility-evaluation change로 설명 가능하고, OpenSpec과 working artifact가 오래된 완료 주장이나 unrelated scope를 현재 사실처럼 남기지 않아야 한다.

## Stage 3 — Closure Evidence

| Order | Work | Gate |
| --- | --- | --- |
| 08 | [`08-run-final-validation.md`](08-run-final-validation.md) | Final candidate HEAD에 current validation evidence 존재 |
| 09 | [`09-refresh-pr-description.md`](09-refresh-pr-description.md) | PR body가 exact current state와 validation을 설명 |
| 10 | [`10-run-fresh-review.md`](10-run-fresh-review.md) | Exact final HEAD의 fresh review에 blocking finding 없음 |

**Stage 3 Gate:** 과거 CI나 과거 review가 아니라 final candidate HEAD에 묶인 검증과 fresh review가 있어야 한다. 새 finding이 나오면 관련 Stage 1 또는 Stage 2 작업으로 돌아간다.

## Stage 4 — Readiness and Merge

| Order | Work | Gate |
| --- | --- | --- |
| 11 | [`11-assess-review-readiness.md`](11-assess-review-readiness.md) | Repository 기준으로 `ready` 판정 가능 |
| 12 | [`12-merge-pr-245.md`](12-merge-pr-245.md) | 명시적 인간 승인 후 merge 및 post-merge 확인 |

`ready`는 correctness approval이나 merge authorization이 아니다. Agent는 repository policy에 따라 readiness를 평가할 수 있지만 Draft → Ready 전환이나 merge처럼 mutable lifecycle action은 해당 시점의 명시적 권한을 확인한다.

## Stage 5 — Follow-Up Only

PR #245가 `main`에 병합된 뒤에만 [`13-langfuse-next-pr.md`](13-langfuse-next-pr.md)를 시작한다. Langfuse 작업은 #245 closure를 대신하거나 F1-F3을 우회하지 않는다.

## Stop Conditions

다음 상황에서는 다음 단계로 진행하지 않는다.

- current HEAD에서 새로운 correctness blocker가 발견됨
- Stage 1 defect를 고치기 위해 unrelated architecture redesign이 필요함
- OpenSpec과 구현 중 어느 쪽이 authoritative requirement인지 확인되지 않음
- final validation이 실패함
- fresh review가 blocking finding을 남김
- base/head가 바뀌어 기존 readiness evidence가 stale해짐
- Ready 전환 또는 merge에 필요한 인간 권한이 없음
