# Next Post-MVP Reliability Capability: Schema-Drift Recovery

현재 MVP는 `volume_drop` 하나의 end-to-end recovery proof를 소유한다. `null_spike` recovery 확장 완료 이후 다음 post-MVP Reliability capability로 `schema_drift` recovery vertical slice를 선택한다.

이 문서는 capability 선택과 구현 전 safety boundary만 정의한다. 세부 runtime contract와 구현 방법은 후속 OpenSpec Change에서 검증한다.

## Decision

**다음 capability:** `schema_drift` recovery vertical slice

선정 이유:

- 현재 detector와 synthetic case가 schema hash 변화와 단일 column type drift를 결정론적으로 재현한다.
- `null_spike`까지 다룬 row/content quality recovery에서 table schema contract recovery로 Reliability proof를 확장할 수 있다.
- `freshness_delay`보다 scheduling과 wall-clock 의미에 덜 의존해 local deterministic evaluation을 유지하기 쉽다.
- 기존 safety pattern은 재사용할 수 있지만, schema 복구 자체를 기존 partition overwrite로 해결할 수 있다고 가정하지 않는다.

## Reuse And Required Gap

| 영역 | 상태 | 경계 |
| --- | --- | --- |
| Read-only lifecycle | 재사용 | `run_incident_lifecycle`와 `detect_basic_incidents`가 table-wide schema hash drift를 탐지하고 impact/draft를 계산한다. |
| Approval pattern | 확장 | 기존 approval gate 원칙은 재사용하되 approved before/after schema identity(최소 expected schema hash)를 recovery contract에 포함해야 한다. |
| Partition recovery | 직접 재사용 불가 | `execute_approved_backfill`은 partition content compare-and-replace용이므로 table schema를 복원하지 않는다. |
| Bronze full-table load | 후보 primitive | `hmda_data`의 full-table replacement는 schema materialization을 제공하지만 approval, stale-state, replay를 포함한 recovery contract는 아니다. 안전하게 조합할지 최소 확장할지는 OpenSpec에서 결정한다. |
| Evaluation pattern | 재사용 | isolated workspace, pre/post-mutation failure 구분, structured evidence와 replay 원칙을 유지한다. |
| Synthetic fixture | 재사용 | 첫 vertical slice는 기존 `schema_drift` fixture의 단일 column type drift를 기준 case로 사용한다. |

## Capability Boundary

### In Scope

- HMDA table 하나의 controlled single-column type drift와 table-wide schema hash 불일치.
- Clean baseline에서 expected schema identity와 target content identity를 유도하는 validation.
- Candidate schema/content가 승인 대상과 다르면 mutation 전에 차단하는 approval gate.
- 승인된 target에 한해 schema와 content를 기대 상태로 복원하는 table-level recovery boundary.
- Recovery 후 schema hash, content identity, incident 해소와 downstream dbt verification.
- Exact after-state replay에서는 mutation을 반복하지 않고 verification만 재개하는 안정성.
- Stale target, invalid candidate, incomplete approval, post-recovery verification failure의 구조화 evidence.

### Out of Scope

- Multi-table schema recovery와 연쇄 migration.
- 범용 schema migration 생성기 또는 임의의 rename/add/drop/type-change 지원.
- 자동 approval, human approval UI와 production authorization system.
- `freshness_delay` recovery와 orchestration scheduling 개선.

## Ownership

- `project_pivot.reliability`: schema recovery contract, approval semantics, evaluation과 recovery evidence를 소유한다.
- `project_pivot.hmda_data`: 기존 Bronze full-table/partition 적재와 `schema_drift` synthetic fixture를 제공하며 approval/recovery policy는 소유하지 않는다.
- `project_pivot.data_platform`: 기존 DuckDB schema/table metadata helper를 제공하며 recovery policy는 소유하지 않는다.
- `project_pivot.data_operations`: 기존 read-only lifecycle 조합을 재사용하며 schema mutation은 소유하지 않는다.

후속 OpenSpec 설계는 기존 load/helper를 우선 조합한다. correctness에 필요한 최소 primitive가 없을 때만 owning domain의 contract를 명시적으로 확장한다.

## Validation Boundary

**Before mutation**

- Candidate schema identity와 content identity가 approved expected state와 일치한다.
- Current target의 schema/content state가 approved before state와 일치한다.
- Approval과 recovery proposal의 target, identities, actions가 exact match다.

**After mutation**

- Target schema identity와 content identity가 expected after state와 일치한다.
- Post-recovery lifecycle에서 target `schema_drift` incident가 해소된다.
- Downstream dbt verification 결과와 failure stage가 evidence로 남는다.
- Replay target이 exact after state면 mutation하지 않고 verification을 재개하며, 제3의 state면 새 validation과 approval을 요구한다.

## Implementation Gate

후속 OpenSpec Change는 먼저 기존 full-table replacement를 approval-safe recovery로 조합할 수 있는지 검증한다. 부족할 때만 table-level schema recovery primitive와 transaction/rollback semantics를 최소 범위로 설계하고 RED/GREEN으로 구현한다. 안전한 local recovery 경계를 만들 수 없으면 기존 partition executor를 억지로 확장하지 않고 capability 선택을 다시 검토한다.
