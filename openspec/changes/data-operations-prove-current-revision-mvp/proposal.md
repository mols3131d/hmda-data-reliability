---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: "Current-Revision MVP Proof Preparation"
description: "기존 MVP contract를 같은 revision에서 검증하기 위한 실행·판정·근거 기록 경계를 준비한다."
---

## Why

과거의 서로 다른 revision proof만으로 `docs/mvp.md`의 same-revision acceptance를 입증할 수 없다. PR #239의 기존 proposal과 checklist를 실행 가능한 준비 상태로 정렬한다.

## What Changes

- Existing pytest/live entrypoint와 여섯 acceptance의 evidence mapping을 고정한다.
- Final proof SHA를 바꾸지 않는 runtime evidence 기록 위치와 live success 판정을 명시한다.
- 인계 Research와 bounded execution plan을 owning Inbox work unit에 남긴다.

## Boundaries

- **In Scope:** proof preparation 문서와 기존 executable contract의 검증.
- **Out of Scope:** 새 product behavior, dependency, architecture, canonical Spec 변경. 재현된 implementation defect는 먼저 owning planning scope와 task를 정렬한 뒤 최소 수정한다.

## Capabilities

Spec-level behavior 변화가 없어 `skip_specs: true`를 사용한다. New/Modified Capability는 없다. 기존 `data-operations-stage-execution`, `orchestration-pipeline`, `reliability-recovery-backfill`, `reliability-agentic-review` contract를 검증한다.

## Impact

Runtime/source/test contract는 유지한다. Preparation deliverable은 Inbox와 이 Change가 소유하고, 실행 결과 및 MVP acceptance는 exact SHA에 연결된 runtime evidence와 PR metadata로 판정한다.
