---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Schema Drift Exact Table Restoration
description: 승인된 complete-table candidate로 HMDA schema drift를 안전하게 복구하고 evaluation evidence까지 제공한다.
tags:
  - "domain:reliability"
  - "capability:data-operations-stage-execution"
  - "capability:data-platform-duckdb-access"
  - "capability:hmda-data-ingestion"
  - "capability:reliability-schema-recovery"
  - "capability:reliability-evaluation-report"
  - "schema-drift"
---

> [!NOTE]
> 기존 `schema_drift` synthetic case와 detection은 유지한다. 이 변경은 `raw.hmda_loans`의 table-wide schema/content state를 approval에 결합하고, 검증된 complete-table candidate를 transaction 안에서 exact replacement한 뒤 recovery와 replay evidence를 제공하는 post-MVP vertical slice를 추가한다.

## Overview

| Why | What | Capabilities |
| --- | --- | --- |
| 현재 partition backfill은 table schema를 복원할 수 없고 DuckDB transaction만으로는 stale check 뒤 concurrent writer를 차단하지 못한다. | 공통 local mutation lock, 별도 table-schema recovery contract와 schema-drift evaluation vertical slice를 추가한다. | `data-operations-stage-execution`, `data-platform-duckdb-access`, `hmda-data-ingestion`, `reliability-schema-recovery`, `reliability-evaluation-report` |

> [!IMPORTANT]
> Reliability lifecycle은 계속 read-only이며 recovery는 external approval 이후 별도 API에서만 실행한다. 기존 `reliability-recovery-backfill`의 partition 의미와 public contract는 변경하지 않는다.

## Why

현재 repository는 deterministic `loan_amount -> VARCHAR` synthetic defect, name/type 기반 schema hash와 `schema_drift` detection을 제공한다. 그러나 승인과 mutation은 partition content identity 및 partition overwrite에 결합되어 있어 table-wide schema를 clean state로 되돌릴 수 없다.

기능을 detection에서 끝내지 않으려면 schema와 complete content를 함께 승인하고 검증하는 table-level recovery boundary가 필요하다. 첫 slice는 범용 migration engine 대신 한 table과 기존 controlled type drift를 대상으로 exact clean-state restoration을 증명한다.

## What Changes

- **Add:** `raw.hmda_loans`의 schema identity와 complete partition content identity set을 하나의 table state로 표현하고 approval의 before/candidate/expected-after state에 결합한다.
- **Add:** File-based DuckDB의 Project Pivot mutation API를 database identity별 cooperative exclusive lock으로 직렬화한다.
- **Modify:** HMDA full-load와 partition replacement가 같은 database mutation lock을 사용한다. Full-load는 call 종료까지, partition replacement는 expected-state check부터 transaction commit/rollback까지 lock을 유지한다.
- **Modify:** `dbt build` stage가 같은 target DuckDB mutation lock을 subprocess 종료까지 유지한다.
- **Add:** isolated complete-table candidate를 target mutation 전에 schema, content completeness와 downstream dbt evidence로 검증한다.
- **Add:** approved before-state에서만 transactional exact table restoration을 수행하고 expected after-state replay와 diverged target을 구분한다.
- **Add:** schema/content/lifecycle/dbt 결과와 rollback, replay, failure stage를 구조화하는 schema-drift evaluation vertical slice를 제공한다.
- **Modify:** `reliability-evaluation-report`가 schema recovery result를 기존 generic case/report surface에 투영할 수 있게 한다.

## Boundaries

| In Scope | Out of Scope |
| --- | --- |
| `raw.hmda_loans` 한 table | multi-table 또는 multi-database recovery |
| Single-host Project Pivot writer의 canonical-path DuckDB mutation serialization | multi-host coordination, hardlink alias와 lock을 우회한 external direct SQL/dbt writer |
| 기존 `loan_amount -> VARCHAR` controlled drift family | arbitrary DDL 또는 범용 schema migration planner |
| column name/type schema identity | column order, nullability, default와 constraint drift |
| complete candidate의 schema/content preflight | partial-table 또는 partition-only schema recovery |
| external approval에 결합된 exact table restoration | automatic repair, approval UI와 Dagster scheduling |
| transaction rollback, stale/diverged state와 replay | production authorization과 장기 audit system |
| post-recovery lifecycle 및 dbt verification evidence | `freshness_delay` recovery |

## Capabilities

### Modified Capabilities

#### `data-operations-stage-execution`

- `dbt build` subprocess는 target DuckDB의 공통 mutation lock을 획득한 뒤 실행하고 process 종료까지 유지한다.
- Lock failure는 dbt process 시작 전에 Data Operations domain failure로 변환한다.

#### `data-platform-duckdb-access`

- Canonical file-based DuckDB path에 결합된 local exclusive mutation lock primitive를 제공한다.
- Lock acquisition/release failure를 typed platform error로 노출하고 body failure를 가리지 않는다.
- In-memory connection은 다른 connection과 database state를 공유하지 않는 현재 access contract에 따라 file lock 대상에서 제외한다.

#### `hmda-data-ingestion`

- Full-load와 partition replacement는 target database mutation 전에 공통 mutation lock을 획득한다. Full-load는 call 종료까지, partition replacement는 transaction commit/rollback까지 lock을 유지한다.
- Expected-state partition replacement는 lock 획득 후 actual identity를 다시 계산해 concurrent managed writer의 변경을 stale state로 식별한다.

#### `reliability-evaluation-report`

- Controlled schema drift부터 external approval, exact table restoration, lifecycle resolution, dbt verification과 replay/failure evidence까지 하나의 deterministic evaluation case로 표현한다.
- Generic report model은 재사용하되 partition-specific `BackfillValidationResult`나 `partition_changed` 의미를 schema recovery에 강제하지 않는다.

### New Capabilities

#### `reliability-schema-recovery`

- Table-wide schema/content state, complete candidate validation, exact approval binding, transactional restoration, post-recovery verification과 replay reconciliation을 담당한다.
- Incident의 partition은 detection observation scope로 유지하고 실제 recovery target table과 명시적으로 분리한다.
- Existing partition backfill API나 contract를 일반화하지 않고 별도 table-schema recovery surface를 제공한다.

## Impact

| Area | Impact |
| --- | --- |
| Code / Systems | Data Platform mutation lock, HMDA/dbt writer lock participation, Reliability contracts, recovery executor와 schema-drift evaluation path가 추가된다. |
| Data / Contracts | Schema hash와 complete sorted partition identity set으로 table before/candidate/after state를 비교한다. |
| Interfaces / APIs | External approval을 요구하는 별도 schema recovery API와 schema-specific result가 public reliability surface에 추가된다. 기존 backfill API는 유지한다. |
| Operations / Dependencies | stdlib `fcntl` local lock과 DuckDB transaction으로 stale-state recheck, exact replacement, final verification과 rollback을 보호한다. 새 runtime dependency는 추가하지 않는다. |

## Appendix

### Alternatives

| Alternative | Why Rejected |
| --- | --- |
| Existing partition backfill contract 확장 | Table-wide mutation scope와 partition public semantics가 충돌한다. |
| Reverse `ALTER COLUMN TYPE` | Content restoration proof가 약하고 conversion history 및 future migration semantics로 범위가 팽창한다. |
| Existing full-load 직접 호출 | Candidate validation 전에 target을 교체하므로 zero-mutation rejection을 보장하지 못한다. |
| DuckDB transaction만 사용 | DuckDB 1.5.5 실험에서 stale read 뒤 concurrent update/insert가 table replacement에 의해 덮어써졌다. |
| Generic schema migration engine | 첫 controlled drift proof에 필요하지 않은 DDL planning과 approval surface를 만든다. |

### Trade-offs

| Choice | Gain | Cost |
| --- | --- | --- |
| Separate exact table restoration capability | Existing partition contract를 보존하면서 schema/content safety invariant를 명확히 한다. | 별도 state, request와 result contract가 필요하다. |
| Schema hash + complete partition identity set | Existing stable identity를 재사용하고 candidate completeness를 partition별로 감사할 수 있다. | Candidate가 전체 partition population을 열거해야 한다. |
| Cooperative database mutation lock | Project Pivot writer 사이 stale check와 first mutation의 직렬화를 실제로 보장한다. | Direct external writer, hardlink alias와 multi-host writer는 이 계약 밖에 남는다. |
| One-table controlled first slice | Transaction, rollback과 replay를 작은 범위에서 실제로 증명한다. | 다른 schema drift family는 후속 change가 필요하다. |
