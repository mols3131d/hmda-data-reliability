---
type: report
title: Schema Recovery 구현 중단 보고서
description: Exact table restoration OpenSpec change의 구현 완료 범위, 검증 evidence, 미완료 작업과 재개 절차를 기록한다.
tags:
  - reliability
  - schema-drift
  - recovery
  - implementation-handoff
---

> [!IMPORTANT]
> **중단 상태:** `reliability-schema-recovery-exact-table-restoration` 구현 task는 `28/33` 완료됐다. 실행 task `1.1~6.4`는 구현·검증됐고, 남은 5개는 전부 Self-Review다. 독립 review, 최종 task 마감, commit, PR과 OpenSpec archive는 수행하지 않았다.

## Status

| Item | State |
| --- | --- |
| 중단 시각 | 2026-08-16 04:50 KST |
| Branch | `main` |
| OpenSpec change | [`reliability-schema-recovery-exact-table-restoration`](../../openspec/changes/reliability-schema-recovery-exact-table-restoration/proposal.md) |
| Schema | `spec-driven-tdd` |
| Progress | `28/33` |
| 실행 task | `1.1~6.4` 완료 |
| 남은 task | Self-Review 5개 |
| Working tree | 구현·test·문서·OpenSpec 변경이 미commit 상태로 남아 있음 |
| Commit / PR / Archive | 미수행 |

이 문서는 중단 시점의 non-canonical snapshot이다. 요구사항과 설계의 source of truth는 OpenSpec [proposal](../../openspec/changes/reliability-schema-recovery-exact-table-restoration/proposal.md), [delta Specs](../../openspec/changes/reliability-schema-recovery-exact-table-restoration/specs), [design](../../openspec/changes/reliability-schema-recovery-exact-table-restoration/design.md), [tasks](../../openspec/changes/reliability-schema-recovery-exact-table-restoration/tasks.md)다.

## Completed Work

### Managed DuckDB mutation serialization

- Canonical database path별 sidecar `fcntl` exclusive lock과 typed lock error를 추가했다.
- Relative, absolute와 symlink path가 같은 lock을 사용하고 in-memory database는 lock file을 만들지 않게 했다.
- HMDA full-load와 partition replacement가 공통 mutation lock에 참여하도록 연결했다.
- Expected-state partition writer가 앞 writer의 commit 후 identity를 다시 계산하고 stale state를 거부하도록 검증했다.
- `run_dbt_build()`가 target DuckDB mutation lock을 subprocess 종료까지 유지하도록 연결했다.
- Schema recovery, HMDA ingestion과 dbt build가 실제로 같은 lock을 공유하는 concurrency test를 추가했다.

### Complete table state and schema recovery contracts

- `TableStateIdentity`를 추가해 table name, name/type schema hash, total row count와 정렬된 complete `source_year` partition identity set을 묶었다.
- Null 또는 누락 population, duplicate/overlapping scope와 equal-count content drift를 거부하는 builder와 test를 추가했다.
- Existing partition recovery model을 변경하지 않고 schema-specific proposal, approval, request와 result contract를 추가했다.
- Incident `observation_partition`과 actual table mutation scope를 분리했다.
- Public reliability package export와 typed schema recovery error를 추가했다.

### Candidate preflight and immutable staging

- Isolated candidate의 exact schema/content state와 dbt projection evidence를 target 접근 및 approval 전에 검증하는 preflight를 추가했다.
- Candidate schema mismatch, content drift, missing population과 dbt failure를 pre-mutation failure로 처리했다.
- Approval 이후 candidate state를 다시 확인하고 complete table을 temporary Parquet로 export했다.
- Export 결과의 table state를 재검증해 approval 후 또는 export 중 candidate 변경을 차단했다.

### Approval-safe exact table restoration

- Approval exactness를 candidate access 전에 재검증하는 schema recovery executor를 추가했다.
- Current target을 approved before, expected after와 third state로 구분했다.
- Before state에서만 `CREATE OR REPLACE TABLE ... read_parquet(...)` exact replacement를 수행했다.
- Replacement, exact after-state와 aligned profile validation을 하나의 DuckDB transaction에서 실행했다.
- Transaction 내부 failure에서 exact before-state rollback과 `retry_same_approval` evidence를 검증했다.
- Expected after-state replay에서는 table replacement 없이 `resume_verification`으로 진행했다.
- Diverged target은 기존 approval로 추가 mutation하지 않고 새 validation/approval을 요구했다.

### Schema-drift evaluation vertical slice

- Distinct disposable clean, target과 candidate database path preflight를 추가했다.
- Complete source population으로 clean baseline을 만들고 target의 `loan_amount`를 실제 `VARCHAR` schema로 변경해 controlled drift를 구성했다.
- Read-only lifecycle에서 단일 `schema_drift` detection과 table-state evidence를 수집했다.
- Candidate validation, external approval, exact restoration, replay, post-recovery lifecycle와 target dbt validation을 연결했다.
- Candidate/approval failure, stale/diverged target, transaction rollback, replay failure와 post-restoration dbt failure를 structured evaluation case로 분류했다.
- Existing generic report model을 재사용하고 partition-specific mutation state를 schema recovery에 사용하지 않았다.

### Documentation

다음 canonical domain 문서에 구현된 boundary를 반영했다.

- [Data Operations](../../docs/domains/data-operations.md): dbt writer lock 참여와 failure boundary
- [Data Platform](../../docs/domains/data-platform.md): database mutation lock primitive와 제한
- [HMDA Data](../../docs/domains/hmda-data.md): full/partition writer serialization
- [Reliability](../../docs/domains/reliability.md): table state, schema recovery와 evaluation API

## Validation Evidence

중단 전에 다음 결과를 확인했다.

| Validation | Observed result |
| --- | --- |
| Focused cross-domain regression | `152 passed` |
| Changed Python Ruff format | `29 files formatted` |
| Changed Python Ruff lint | `All checks passed` |
| Markdown format/frontmatter/heading/link | 변경 문서 12개 통과 |
| OpenSpec validation | `17/17 valid` |
| Default pytest suite | `267 passed, 1 skipped` |
| Editor diagnostics | 마지막 확인 대상에서 new error 없음 |

> [!NOTE]
> 위 결과는 중단 전에 실행한 evidence다. 이 보고서를 작성하면서 test suite를 다시 실행하지 않았다. 재개 후 추가 수정이 있으면 해당 검증을 다시 수행해야 한다.

## Remaining Work

현재 [tasks](../../openspec/changes/reliability-schema-recovery-exact-table-restoration/tasks.md)의 미완료 항목은 다음 Self-Review 5개다.

- [ ] 모든 관련 Requirement와 Scenario가 구현 및 test에 반영됐는지 확인한다.
- [ ] Design Decision과 Boundary를 지키면서 중복과 불필요한 복잡성을 제거한다.
- [ ] 관련 test, 실패 경로와 정적 검사가 통과하는지 최종 확인한다.
- [ ] 필요한 문서, 설정과 운영 절차가 모두 갱신됐는지 확인한다.
- [ ] 알려진 제약과 후속 작업을 명시한다.

실질적으로 남은 작업은 다음 순서다.

1. Working tree diff에 대해 quality review와 adversarial review를 수행한다.
1. Finding이 있으면 owning code, test 또는 OpenSpec artifact를 수정하고 focused/default validation을 다시 실행한다.
1. Finding이 없거나 해결되면 Self-Review 5개를 [tasks](../../openspec/changes/reliability-schema-recovery-exact-table-restoration/tasks.md)에서 완료 처리한다.
1. OpenSpec apply progress가 `33/33`인지 확인한다.
1. 필요하면 delta Specs를 current Specs와 sync한다.
1. 변경을 coherent commit 단위로 정리하고 PR을 생성한다.
1. Merge 및 검증 완료 후 OpenSpec change를 archive한다.

## Known Boundaries

- Mutation lock은 single-host Project Pivot managed writer의 cooperative contract다.
- Direct external SQL/dbt writer, hardlink alias와 multi-host writer는 lock 보장 범위 밖이다.
- 첫 recovery slice는 `raw.hmda_loans` 한 table과 existing `loan_amount -> VARCHAR` drift family만 다룬다.
- Schema identity는 current detector와 같은 column name/type semantics다. Column order, nullability, default와 constraint drift는 포함하지 않는다.
- Complete table state 계산과 candidate export는 모든 year partition을 hash/materialize하므로 큰 table에서 비용이 증가할 수 있다.
- Existing partition backfill public semantics와 full-load validation-after-replacement semantics는 유지했다.
- Lifecycle은 계속 read-only이고 approval, recovery와 evaluation은 별도 API다.

## Working Tree Snapshot

중단 시점에는 commit되지 않은 변경이 다음 영역에 남아 있다.

| Area | Main paths |
| --- | --- |
| OpenSpec | `openspec/changes/reliability-schema-recovery-exact-table-restoration/` |
| Data Platform | `src/project_pivot/data_platform/duckdb.py`, package export와 tests |
| Data Operations | `src/project_pivot/data_operations/runner.py`, dbt runner tests |
| HMDA ingestion | `src/project_pivot/hmda_data/ingestion/full_load.py`, `partition.py`, ingestion tests |
| Reliability contracts/profile | `contracts/table_state.py`, `contracts/schema_recovery.py`, `profiling/table_state_builder.py` |
| Reliability recovery | `recovery/schema_candidate.py`, `schema_executor.py`, `schema_request.py`, `schema_result.py` |
| Reliability evaluation | `evaluation/schema_drift.py`, exports와 report tests |
| Domain docs | `docs/domains/data-operations.md`, `data-platform.md`, `hmda-data.md`, `reliability.md` |

Tracked diff summary는 보고서 작성 직전 `20 files changed, 713 insertions, 67 deletions`였다. 여기에 untracked OpenSpec, 새 implementation module과 test file이 별도로 존재한다. Working tree를 clean하다고 가정하거나 기존 변경을 되돌려서는 안 된다.

## Resume Checklist

1. `git status --short`로 위 working tree가 그대로인지 확인한다.
1. `openspec instructions apply --change reliability-schema-recovery-exact-table-restoration --json`으로 progress와 context를 다시 읽는다.
1. [tasks](../../openspec/changes/reliability-schema-recovery-exact-table-restoration/tasks.md)가 `28/33`인지 확인한다.
1. OpenSpec proposal, Specs, design과 현재 diff를 quality/adversarial 관점으로 review한다.
1. Finding 수정 후 focused regression, Ruff, Markdown, OpenSpec validation과 default pytest를 다시 실행한다.
1. Self-Review 5개를 evidence와 함께 완료 처리한다.
1. Commit/PR/archive는 review와 `33/33` 확인 뒤 진행한다.

## RPI Handoff

- Entry: `apply` paused by user
- Change: `reliability-schema-recovery-exact-table-restoration`
- Research: transferred to OpenSpec planning and implementation
- Feedback: independent review not started
- Next: review current diff, resolve findings, complete Self-Review `5/5`
