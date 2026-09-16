---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: "Current-Revision MVP Proof"
description: "기존 MVP proof를 준비하고 baseline에서 재현된 classifier test의 repository-state 의존을 제거한다."
---

## Why

과거의 서로 다른 revision proof만으로 `docs/mvp.md`의 same-revision acceptance를 입증할 수 없다. PR #239의 기존 proposal과 checklist를 실행 가능한 준비 상태로 정렬한다.

## What Changes

- Baseline에서 실패한 CI classifier 테스트의 active Change setup을 임시 OpenSpec tree로 격리한다. Classifier runtime와 기존 assertion은 유지한다.
- MVP domain gate와 acceptance를 production owner 및 독립 oracle에 매핑한다.
- Approval과 exact proposal이 일치해도 실제 request의 table/year/file이 다르면 source 처리 전에 차단한다. 기존 `reliability-recovery-backfill` Approval gate를 충족하는 수정이다.
- Existing pytest/live entrypoint와 여섯 acceptance의 evidence mapping을 고정한다.
- Final proof SHA를 바꾸지 않는 runtime evidence 기록 위치와 live success 판정을 명시한다.
- 인계 Research와 bounded execution plan을 owning Inbox work unit에 남긴다.

## Boundaries

- **In Scope:** proof preparation, MVP implementation gap audit, classifier test fixture remediation, 기존 approval contract의 request target scope 사전 검증 누락 보완.
- **Out of Scope:** 새 product behavior, dependency, architecture, canonical Spec 변경. 재현된 implementation defect는 먼저 owning planning scope와 task를 정렬한 뒤 최소 수정한다.

## Capabilities

기존 canonical contract를 변경하지 않아 `skip_specs: true`를 사용한다. New/Modified Capability는 없다. 기존 `data-operations-stage-execution`, `orchestration-pipeline`, `reliability-recovery-backfill`, `reliability-agentic-review` contract를 검증한다.

## Impact

Classifier runtime와 기존 oracle을 유지한다. Recovery executor는 기존 approval contract에 맞게 request target scope 불일치를 source staging 전에 차단한다. Preparation deliverable은 Inbox와 이 Change가 소유하고, 실행 결과 및 MVP acceptance는 exact SHA에 연결된 runtime evidence와 PR metadata로 판정한다.
