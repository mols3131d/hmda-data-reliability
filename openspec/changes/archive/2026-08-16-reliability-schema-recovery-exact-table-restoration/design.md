---
type: openspec-spec-driven-tdd-design
category: design
title: Schema Drift Exact Table Restoration Design
description: Cooperative DuckDB mutation lock과 complete-table state를 사용해 승인된 schema restoration을 안전하게 실행한다.
---

> [!NOTE]
> File-based DuckDB의 managed writer를 canonical database path별 sidecar `fcntl` lock으로 직렬화하고, schema recovery는 별도 table state·approval·request·result contract를 사용한다. Candidate는 approval 전에 complete schema/content/dbt preflight를 통과하고 실행 시 immutable Parquet로 다시 staging된다. Target replacement, exact after-state와 aligned profile 확인은 하나의 transaction에서 완료하며 lifecycle/dbt acceptance는 commit 이후 schema-specific evaluator가 담당한다.

## Context

- **Current State:** `schema_drift` synthetic case와 name/type schema hash detection은 존재한다. `PartitionContentIdentity`, `RecoveryProposal`과 `execute_approved_backfill()`은 `source_year`/optional file partition에 결합되어 table schema를 복원하지 않는다. `load_hmda_loans()`는 full-table replacement가 가능하지만 validation-before-mutation contract가 아니다.
- **Verified DuckDB Behavior:** Project environment의 DuckDB 1.5.5에서 transaction 안의 `CREATE OR REPLACE TABLE` rollback은 기존 schema와 content를 복원했다. 반면 stale read 뒤 다른 connection이 update/insert를 commit한 경우 transaction의 table replacement와 partition `DELETE + INSERT`가 concurrent 변경을 오류 없이 덮어썼다.
- **Constraints:** Lifecycle은 read-only다. Recovery와 evaluation은 external approval 뒤 별도 API다. Single-host Project Pivot writer만 cooperative lock contract에 포함한다. Direct external SQL/dbt writer, hardlink alias와 multi-host coordination은 범위 밖이다.
- **Dependencies:** Existing `calculate_schema_hash()`, year-scoped `PartitionContentIdentity`, HMDA source/full-load semantics, artifact-isolated dbt build, generic `EvaluationCaseResult`와 report rendering을 재사용한다. Runtime dependency는 추가하지 않는다.

## Goals / Non-Goals

| Goals | Non-Goals |
| --- | --- |
| Managed DuckDB writer 사이 stale-check/mutation 직렬화 | External 또는 multi-host writer coordination |
| `raw.hmda_loans`의 complete schema/content state | Generic catalog snapshot 또는 arbitrary table support |
| Existing controlled type drift의 exact clean-state restoration | Reverse DDL planning과 forward schema migration |
| Pre-mutation candidate/approval rejection과 transaction rollback | Existing full-load validation failure semantics 변경 |
| Replay, lifecycle와 dbt evidence를 가진 vertical slice | Generic recovery/evaluation framework 선행 |

## Architecture

`data_platform`은 canonical database path에서 sidecar lock path를 결정하고 local exclusive lock을 제공한다. HMDA full/partition ingestion, `dbt build`와 schema recovery는 이 primitive를 직접 사용한다. Connection manager 자체는 잠그지 않아 read-only lifecycle과 long-lived connection을 불필요하게 직렬화하지 않는다.

Schema recovery는 partition backfill contract를 확장하지 않는다. `TableStateIdentity`가 name/type schema hash와 겹치지 않는 `source_year` partition identity tuple을 묶고, `SchemaRecoveryProposal`과 approval은 exact before/candidate/after state 및 `replace_table`, `rerun_profile_snapshot` action에 결합된다.

### Components

| Component | Responsibility | Change |
| --- | --- | --- |
| `data_platform.duckdb` | Current database path와 local mutation lock | Canonical path, sidecar `fcntl` lock과 typed error를 추가한다. |
| HMDA full/partition ingestion | Bronze target mutation | File database mutation을 lock 안에서 실행하고 partition identity를 lock 획득 후 다시 확인한다. |
| `data_operations.run_dbt_build` | DuckDB-writing dbt subprocess | Target mutation lock을 subprocess 종료까지 유지한다. |
| Schema recovery contracts | Table state, proposal, approval, request와 result | Partition recovery와 분리된 immutable Pydantic models를 추가한다. |
| Schema recovery state builder | Complete target/candidate identity | Schema hash, distinct year partitions와 total population을 검증한다. |
| Schema recovery executor | Approval gate, staging, reconciliation과 exact replacement | Candidate와 target lock, transaction, rollback과 replay를 소유한다. |
| Schema-drift evaluator | Controlled defect와 end-to-end acceptance | Clean/drift/candidate setup, lifecycle/dbt와 failure evidence를 조합한다. |
| Evaluation adapter/report | Generic case projection | Schema-specific mutation state를 `EvaluationCaseResult`에 투영한다. |

### Boundaries

| Boundary | Owns | Does Not Own |
| --- | --- | --- |
| Database mutation lock | Managed single-host writer serialization | DuckDB native lock 대체, external writer 강제와 distributed lock |
| HMDA ingestion | Source-to-Bronze mutation과 existing validation semantics | Schema recovery approval과 acceptance |
| Schema recovery executor | Exact approval, immutable candidate, target transaction과 profile evidence | Incident detection, lifecycle execution과 dbt subprocess |
| Schema-drift evaluator | Controlled defect, candidate/target dbt, lifecycle resolution과 report evidence | Production approval UI와 generic orchestration framework |
| Read-only lifecycle | Incident, impact와 remediation draft | Lock-protected mutation, approval과 evaluation write |

## Data Flow

| Step | From | To | Data / Contract |
| ---: | --- | --- | --- |
| 1 | Original complete sources | Clean database | Full `raw.hmda_loans`, baseline profile와 expected `TableStateIdentity` |
| 2 | Clean table export | Synthetic generator | Provenance-preserving Parquet with `loan_amount -> VARCHAR` |
| 3 | Drifted Parquet | Target database | New drifted table materialized under target mutation lock |
| 4 | Baseline + target | Read-only lifecycle | Partition-observed `schema_drift`, impact와 remediation draft |
| 5 | Original complete sources | Candidate database | Expected clean state and candidate dbt projection |
| 6 | Expected state + candidate | Candidate preflight | Exact schema, all year partitions, total population and dbt evidence |
| 7 | Target + candidate evidence | Proposal / external approval | Incident observation, table target, before/candidate/after state and actions |
| 8 | Approved candidate database | Immutable staging | Candidate lock, state recheck and complete Parquet export |
| 9 | Approved request | Target lock | Current target equals before, after or diverged state |
| 10 | Before-state target | DuckDB transaction | Exact table replacement, after-state and aligned profile validation |
| 11 | Committed target | Evaluator | Post-recovery lifecycle, target dbt validation and report evidence |
| 12 | Same approval replay | Recovery executor | No replacement at exact after-state; verification resumes |

## Decisions

### D1. Canonical-path sidecar lock을 공통 mutation primitive로 사용한다

- **Decision** - `Path.resolve(strict=False)`로 정규화한 database path에 대응하는 sidecar file을 `fcntl.flock(LOCK_EX)`로 잠근다. In-memory database는 no-op lock을 사용한다.
- **Rationale** - Existing artifact projection lock과 같은 stdlib/local pattern이며 새 database file을 미리 빈 파일로 만들지 않는다. Relative, absolute와 symlink path는 같은 canonical lock으로 수렴한다.
- **Trade-off** - Hardlink alias, lock을 사용하지 않는 external writer와 multi-host writer는 보호하지 않는다.
- **Alternatives** - DuckDB transaction만으로는 재현 실험에서 lost update를 막지 못했다. Database file 자체를 미리 잠그면 새 빈 file을 DuckDB가 invalid database로 거부했다.

### D2. Mutation API만 lock에 참여한다

- **Decision** - HMDA full/partition ingestion, dbt subprocess와 schema recovery가 명시적으로 lock을 획득한다. `DuckDBConnectionManager`의 모든 read-write connection을 자동 잠그지 않는다.
- **Rationale** - 실제 writer를 모두 보호하면서 read-only lifecycle, metadata read와 long-lived connection을 직렬화하지 않는다.
- **Trade-off** - 새 managed writer가 추가되면 같은 primitive 사용을 contract와 test로 요구해야 한다.
- **Alternatives** - Connection lifetime lock은 callback nesting과 긴 read에서 self-deadlock 및 불필요한 blocking 위험이 크다.

### D3. Complete content grain은 `source_year` partition set이다

- **Decision** - `TableStateIdentity`는 table name, name/type schema hash, total row count와 `source_file=None`인 year partition identities를 year 오름차순 tuple로 보존한다. Duplicate year, null year, overlapping file scope와 partition row-count 합계 불일치는 거부한다.
- **Rationale** - Existing stable partition identity를 재사용하면서 모든 file population을 겹치지 않는 year grain으로 덮고 sentinel year 누락을 식별한다.
- **Trade-off** - Table state 계산은 모든 year partition content를 hash하며 large table에서는 비용이 증가한다.
- **Alternatives** - Monolithic row digest는 existing identity logic을 중복하고 source manifest는 actual logical equality를 증명하지 못한다.

### D4. Partition recovery contract를 일반화하지 않는다

- **Decision** - `SchemaRecoveryProposal`, `SchemaRecoveryApproval`, `ApprovedSchemaRecoveryRequest`와 `SchemaRecoveryValidationResult`를 별도로 둔다. Existing `Approval`, `RecoveryProposal`, request/result와 executor semantics는 유지한다.
- **Rationale** - Partition과 table mutation scope, identity grain, action 및 mutation state가 다르다.
- **Trade-off** - 일부 approval field와 gate validation이 반복된다. 실제 공통점이 안정된 뒤에만 pure helper를 추출한다.
- **Alternatives** - Union proposal이나 generic recovery base model은 existing public meaning과 caller type을 넓힌다.

### D5. Candidate는 실행 시 immutable artifact로 다시 staging한다

- **Decision** - Approval exactness를 candidate access 전에 확인한다. 이후 candidate database lock 아래 current state를 approved candidate state와 비교하고 complete table을 temporary Parquet로 export한 뒤 staged state를 다시 확인한다.
- **Rationale** - Approval 후 candidate database 변경과 source replacement를 target mutation 전에 차단하고 mutation input을 고정한다.
- **Trade-off** - Recovery마다 complete-table export와 identity 계산 비용이 든다.
- **Alternatives** - Candidate database를 transaction에서 직접 읽으면 별도 database connection과 target mutation 사이 immutable snapshot을 보장하기 어렵다.

### D6. Replacement와 primary validation을 한 transaction에서 완료한다

- **Decision** - Target lock을 획득한 뒤 before/after/diverged state를 조정한다. Before state에서 `CREATE OR REPLACE TABLE ... AS SELECT * FROM read_parquet(...)`, exact after-state 계산과 aligned profile 생성이 모두 성공해야 commit한다. 실패하면 rollback하고 exact before-state를 보존한다.
- **Rationale** - DuckDB 1.5.5에서 DDL rollback이 schema/content를 복원함을 확인했고, schema-only 또는 content-only success를 commit하지 않는다.
- **Trade-off** - Profile 계산까지 transaction과 lock 시간이 늘어난다. 첫 local HMDA slice에서는 safety를 우선한다.
- **Alternatives** - Reverse `ALTER COLUMN TYPE`은 content restoration proof가 없고, commit 후 profile validation은 피할 수 있는 post-mutation failure를 만든다.

### D7. Lifecycle과 dbt acceptance는 commit 이후 evaluator가 소유한다

- **Decision** - Executor는 exact table state와 aligned profile까지만 반환한다. Evaluator는 lock이 해제된 뒤 post-recovery lifecycle과 target dbt build를 실행한다.
- **Rationale** - Read-only lifecycle과 external process를 mutation lock 안에서 호출하지 않아 self-deadlock을 피하고 architecture boundary를 보존한다.
- **Trade-off** - Lifecycle/dbt failure는 committed target의 post-mutation failure이며 replay에서 `resume_verification`이 필요하다.
- **Alternatives** - Callback을 executor transaction 안에 넣으면 dbt build가 같은 mutation lock을 다시 요구한다.

### D8. Schema-specific evaluator와 adapter를 먼저 만든다

- **Decision** - `SchemaDriftVerticalSliceResult`와 schema recovery adapter를 추가하고 generic `EvaluationCaseResult`/report surface만 재사용한다.
- **Rationale** - Existing adapter는 `BackfillValidationResult`와 `partition_changed`에 결합되어 있다.
- **Trade-off** - Volume-drop/null-spike evaluator와 일부 composition 중복이 남는다.
- **Alternatives** - Base class, registry 또는 recovery DSL은 세 mutation family의 차이를 먼저 고정할 위험이 있다.

## Testability

| Boundary / Behavior | Test Strategy | Evidence |
| --- | --- | --- |
| Database mutation lock | Component concurrency | Same canonical path writer ordering, symlink alias와 typed lock failure |
| HMDA writer participation | Component concurrency/regression | Second expected-state writer waits then stale-fails; full-load existing failure semantics 유지 |
| dbt writer participation | Component with controlled subprocess | Process starts after lock release and lock failure prevents process invocation |
| Table state identity | Unit + component DuckDB | Stable sorted year set, null/missing/duplicate population rejection and exact schema hash |
| Candidate/approval gate | Unit + component | Candidate access/mutation 전에 schema/content/dbt 및 exact binding rejection |
| Transaction restoration | Component DuckDB | Exact after-state commit, injected state/profile failure rollback and sentinel year preservation |
| Reconciliation | Component | Before replaces, after resumes without replacement, third state requests new approval |
| Controlled vertical slice | Integration | Actual drifted target schema, incident, clean state restoration, lifecycle/dbt and replay evidence |
| Read-only boundary | Regression | Lifecycle-only call produces no approval, staging, lock-protected target mutation or report write |

- **TDD Boundary:** 공통 mutation lock이 없으면 두 managed writer가 stale state를 덮어쓰는 RED를 먼저 고정한다. 다음 RED는 expected schema지만 sentinel year가 빠진 candidate를 mutation 전에 거부하고, injected in-transaction failure가 exact before-state를 보존하도록 한다.
- **Failure Signals:** Lost update, candidate/target state equality false-positive, target mutation before approval, committed schema-only state, missing sentinel partition, repeated replacement on replay와 lifecycle-triggered mutation을 명시적으로 실패시킨다.

## Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| External writer가 sidecar lock을 사용하지 않는다. | Managed freshness guarantee 밖에서 target이 변경될 수 있다. | Single-host Project Pivot writer로 contract를 제한하고 direct external mutation을 문서화한다. |
| Nested mutation lock | Same process가 blocking될 수 있다. | Executor lock 안에서 ingestion/dbt callback을 호출하지 않고 lock ownership을 public mutation entry마다 한 번만 둔다. |
| Candidate에 null `source_year` row가 있다. | Partition set이 complete population을 숨긴다. | Total row count와 partition 합계를 비교하고 null/uncovered row를 거부한다. |
| Complete-table hashing/export 비용 | Large table recovery 시간이 증가한다. | 첫 slice를 local `raw.hmda_loans`에 제한하고 성능 문제를 측정한 뒤 별도 최적화한다. |
| Schema hash semantics가 name/type뿐이다. | Constraint/default/order drift는 복구 proof에 포함되지 않는다. | Current detector와 동일한 semantics로 명시하고 확장은 별도 Change로 둔다. |
| dbt build lock 시간이 길다. | Ingestion/recovery가 build 종료까지 대기한다. | Correctness를 우선하고 timeout은 existing dbt stage contract를 유지한다. |

## Migration

| Phase | Change | Verification |
| ---: | --- | --- |
| 1 | Data Platform mutation lock과 HMDA/dbt writer participation | Focused concurrency 및 existing ingestion/data-operations tests |
| 2 | Table state와 schema recovery contracts/gate | Contract, identity와 pre-mutation rejection tests |
| 3 | Transactional executor와 reconciliation | Real DuckDB commit/rollback, stale/diverged와 replay tests |
| 4 | Schema-drift evaluator와 public exports | End-to-end controlled drift, lifecycle/dbt 및 report tests |
| 5 | Domain documentation과 validation | Ruff, pytest, Markdown와 OpenSpec validation |

- **Compatibility:** Existing backfill request/result/API와 full-load validation semantics는 유지한다. New schema recovery API와 lock participation은 additive behavior이며 concurrent managed writes만 직렬화한다.
- **Rollback:** New evaluator/recovery exports를 제거하고 managed writer lock wrapping을 되돌리면 이전 runtime으로 복원된다. Delta Specs와 domain docs도 함께 되돌린다.
