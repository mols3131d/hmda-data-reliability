# Next Post-MVP Reliability Capability: Schema-Drift Recovery

현재 MVP는 `volume_drop` 하나의 end-to-end recovery proof를 소유한다. `null_spike` recovery 확장 완료 이후 다음 post-MVP Reliability capability로 `schema_drift` recovery vertical slice를 선택한다.

이 문서는 capability 선택과 구현 진입 조건만 기록한다. 세부 runtime contract와 recovery strategy는 후속 OpenSpec Change가 소유한다.

## Decision

**선택:** `schema_drift` recovery vertical slice

- 현재 detector와 synthetic case가 table-wide schema hash 변화와 single-column type drift를 결정론적으로 재현한다.
- `volume_drop`과 `null_spike`의 row/content quality proof를 table schema contract까지 확장할 수 있다.
- `freshness_delay`보다 scheduling과 wall-clock 의미에 덜 의존해 local deterministic evaluation에 적합하다.
- 기존 safety pattern은 재사용하되 schema mutation 방법은 미리 결정하지 않는다.

## Reuse And Gap

| 구분 | 경계 |
| --- | --- |
| 재사용 | read-only detection/impact/draft, exact approval 원칙, isolated evaluation, replay와 failure evidence |
| 새 contract 필요 | approved before/after schema identity, table-level mutation과 rollback, stale/replay semantics |
| 직접 재사용 불가 | 기존 partition recovery executor는 partition content compare-and-replace이며 table schema를 복원하지 않는다. |
| 미결정 | existing full-table rebuild, targeted schema mutation, 최소 신규 primitive 중 어떤 recovery strategy가 안전한지 |

## Scope

**In scope**

- HMDA table 하나의 controlled single-column type drift
- approved before/after schema identity와 content identity 검증
- candidate 또는 current state 불일치 시 mutation 전 차단
- 승인된 schema/content recovery와 post-recovery incident 해소 검증
- downstream dbt verification, replay, stale target과 failure evidence

**Out of scope**

- multi-table schema recovery와 연쇄 migration
- 범용 schema migration 생성기
- 자동 approval, human approval UI와 production authorization
- `freshness_delay` recovery와 orchestration scheduling

## Ownership

- `project_pivot.reliability`는 approval, recovery semantics와 evaluation evidence를 소유한다.
- `project_pivot.hmda_data`와 `project_pivot.data_platform`은 기존 load/schema primitive만 제공하며, OpenSpec 근거 없이 contract를 확장하지 않는다.
- `project_pivot.data_operations`의 lifecycle은 계속 read-only이며 schema mutation을 소유하지 않는다.

## Implementation Gate

후속 OpenSpec Change는 구현 전에 다음을 결정하고 검증한다.

1. 기존 primitive 조합 또는 최소 신규 primitive 중 recovery strategy를 선택한다.
1. approved before/after schema identity, transaction/rollback, stale target과 replay semantics를 정의한다.
1. 기존 partition recovery contract를 약화하거나 schema recovery로 오용하지 않음을 확인한다.

안전한 local recovery 경계를 만들 수 없으면 구현을 시작하지 않고 capability 선택을 다시 검토한다.
