---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: Schema Drift Exact Table Restoration Tasks
description: DuckDB writer serialization부터 approved table restoration과 schema-drift evaluation까지 test-first로 구현한다.
tasks_completed: 28
tasks_total: 33
---

> [!NOTE]
> 먼저 managed DuckDB writer의 lost-update 경계를 잠근다. 그 위에 complete table state와 별도 schema recovery contract, immutable candidate staging, transactional exact replacement를 구현한 뒤 controlled `schema_drift` evaluator를 연결한다. Existing partition backfill API와 full-load validation semantics는 유지한다.

## Tasks

### 1. Local DuckDB mutation serialization

- [x] 1.1 **RED** — Canonical database path별 exclusive lock, symlink alias, in-memory no-op과 lock/body failure 우선순위를 고정하는 Data Platform component tests를 작성한다.
  - **Covers:** `Local database mutation lock`
  - **Done when:** Same canonical path의 두 writer가 동시에 lock을 획득하거나 lock I/O failure가 typed error로 변환되지 않는 assertion에서 의도한 RED가 발생한다.

- [x] 1.2 **GREEN** — `data_platform.duckdb`에 sidecar `fcntl` mutation lock context와 typed error를 최소 구현하고 public Data Platform surface에서 export한다.
  - **Done when:** File database writer는 직렬화되고 relative/absolute/symlink path는 같은 lock을 사용하며 in-memory database는 file을 만들지 않는다.

- [x] 1.3 **RED/GREEN** — HMDA full-load와 expected-state partition replacement를 mutation lock 안에서 실행하고 concurrent managed writer behavior를 검증한다.
  - **Covers:** `Serialized managed Bronze mutation`
  - **Done when:** Second partition writer는 first commit 뒤 identity를 다시 계산해 stale-fails하고 full-load 및 unrelated partition writer는 database-level 순서를 지키며 existing full-load failure semantics regression tests가 통과한다.

- [x] 1.4 **RED/GREEN** — `run_dbt_build()`가 target mutation lock을 subprocess 종료까지 유지하고 lock failure 시 process를 시작하지 않는 tests와 구현을 추가한다.
  - **Covers:** `Serialized dbt database mutation`
  - **Done when:** Controlled subprocess는 recovery/ingestion lock release 뒤 시작하고 dbt-held lock 동안 다른 managed writer가 target state를 확인하지 않으며 lock failure가 `DataOperationError`로 변환된다.

### 2. Complete table state and contracts

- [x] 2.1 **RED** — Schema hash, sorted year identities, total row count와 complete population invariant를 고정하는 table-state unit/component tests를 작성한다.
  - **Covers:** `Composite table state`, `Equivalent complete table state`, `Equal schema with missing partition`, `Equal row count with different content`
  - **Done when:** Null year, duplicate/overlapping scope, missing sentinel year 또는 equal-count content drift를 valid state로 받아들이는 assertion에서 의도한 RED가 발생한다.

- [x] 2.2 **GREEN** — Immutable `TableStateIdentity`와 current table state builder를 reliability contract/profile boundary에 최소 구현한다.
  - **Done when:** Builder는 distinct `source_year` population을 오름차순 identity tuple으로 반환하고 partition 합계가 total population과 다르면 typed validation failure로 종료한다.

- [x] 2.3 **RED** — Schema recovery proposal, approval, request와 result의 exact target/state/action binding 및 observation/mutation scope를 고정하는 contract tests를 작성한다.
  - **Covers:** `Exact table-recovery approval`, `Observation and mutation scope separation`
  - **Done when:** Partition identity, missing `replace_table`, mismatched candidate/after state 또는 incident partition을 mutation scope로 사용하는 contract가 허용되는 assertion에서 의도한 RED가 발생한다.

- [x] 2.4 **GREEN** — Partition recovery models를 변경하지 않고 schema-specific immutable contracts, validation errors와 package exports를 추가한다.
  - **Done when:** Valid exact proposal/approval/request/result만 생성되며 existing recovery contract tests와 public imports가 그대로 통과한다.

### 3. Candidate preflight and immutable staging

- [x] 3.1 **RED** — Candidate schema mismatch, content drift, missing population과 dbt failure가 approval callback 및 target access 전에 차단되는 tests를 작성한다.
  - **Covers:** `Complete candidate preflight`
  - **Done when:** Invalid candidate가 proposal/approval로 진행하거나 target mutation을 허용하는 assertion에서 의도한 RED가 발생한다.

- [x] 3.2 **GREEN** — Isolated candidate state와 caller-provided dbt projection evidence를 검증해 schema recovery proposal input을 만드는 최소 preflight API를 구현한다.
  - **Done when:** Exact complete candidate만 immutable state/evidence를 반환하고 invalid candidate는 structured pre-mutation failure로 종료한다.

- [x] 3.3 **RED** — Approval 이후 candidate database 변경과 export 중 candidate 변경을 approved state mismatch로 차단하는 component tests를 작성한다.
  - **Covers:** `Mismatched staged candidate`
  - **Done when:** Changed candidate가 target replacement input으로 사용되는 assertion에서 의도한 RED가 발생한다.

- [x] 3.4 **GREEN** — Candidate database lock 아래 approved state를 재확인하고 complete table을 temporary Parquet로 export한 뒤 staged state를 재검증한다.
  - **Done when:** Target mutation은 approved immutable staged artifact만 사용하고 candidate mismatch는 target lock 획득 및 mutation 전에 종료된다.

### 4. Approval-safe exact table restoration

- [x] 4.1 **RED** — Current target의 approved before, expected after와 third-state reconciliation을 고정하는 executor component tests를 작성한다.
  - **Covers:** `Table-recovery reconciliation`, `Stale target before mutation`
  - **Done when:** Before state 외 mutation, after-state duplicate replacement 또는 third-state existing approval mutation assertion에서 의도한 RED가 발생한다.

- [x] 4.2 **GREEN** — Approval exactness를 candidate access 전에 확인하고 target lock 아래 before/after/diverged state를 분기하는 schema recovery executor entry를 구현한다.
  - **Done when:** Before는 replacement path, after는 `resume_verification`, diverged는 새 validation/approval 요구로 분기되고 target mutation 전 failure evidence가 구분된다.

- [x] 4.3 **RED** — Exact replacement success, sentinel year preservation, schema-only false-green과 injected replacement/final-state/profile failure rollback tests를 작성한다.
  - **Covers:** `Transactional exact table restoration`, `Post-restoration validation result`
  - **Done when:** Missing sentinel, wrong content, committed partial state 또는 rollback 뒤 before-state 손실 assertion에서 의도한 RED가 발생한다.

- [x] 4.4 **GREEN** — Target lock과 DuckDB transaction 안에서 staged table replacement, exact after-state와 aligned profile validation, commit/rollback 및 mutation-aware result를 구현한다.
  - **Done when:** Success는 exact after-state로 commit되고 in-transaction failure는 exact before-state와 retryable same-approval state를 보존한다.

- [x] 4.5 **RED/GREEN** — Schema recovery와 HMDA/dbt managed writer가 같은 database lock을 실제로 공유하는 cross-domain concurrency test와 필요한 integration wiring을 추가한다.
  - **Covers:** `Serialized file-database writers`, `Recovery holds database mutation lock`, `dbt build holds database mutation lock`
  - **Done when:** Recovery stale check와 commit 사이 managed ingestion/dbt writer가 끼어들지 않고 lock release 뒤 관찰한 current state에 따라 정상 진행 또는 stale-fails한다.

### 5. Schema-drift evaluation vertical slice

- [x] 5.1 **RED** — Existing/aliased evaluation path rejection, clean baseline과 실제 `loan_amount: VARCHAR` target materialization을 고정하는 integration tests를 작성한다.
  - **Covers:** `Existing or aliased evaluation database`, `Clean baseline`, `Controlled table schema drift`
  - **Done when:** Existing clean table에 partition insert한 결과를 drift proof로 받아들이거나 schema hash mismatch 없이 evaluation이 진행되는 assertion에서 의도한 RED가 발생한다.

- [x] 5.2 **GREEN** — Distinct disposable clean/target/candidate database와 provenance-preserving controlled schema drift setup을 구성하고 read-only lifecycle까지 실행한다.
  - **Done when:** Clean case는 incident가 없고 target은 expected `schema_drift` 하나와 baseline/target table state evidence를 반환한다.

- [x] 5.3 **RED** — Complete candidate, external approval, exact restoration, lifecycle resolution, target dbt와 replay acceptance를 연결하는 happy-path integration test를 작성한다.
  - **Covers:** `Approved schema-drift restoration`, `Schema-drift replay stability`, `Read-only lifecycle preservation`
  - **Done when:** Schema/content exact equality, incident 해소, target dbt success 또는 no-replacement replay 중 미구현 oracle에서 의도한 RED가 발생한다.

- [x] 5.4 **GREEN** — Schema-specific evaluator/result가 candidate preflight, approval callback, executor, post-recovery lifecycle/dbt와 replay를 조합하도록 구현한다.
  - **Done when:** Successful case는 baseline/drift/recovery/replay state와 projection evidence를 보존하고 lifecycle-only path는 approval, mutation과 report write를 실행하지 않는다.

- [x] 5.5 **RED** — Incomplete candidate false-green, stale schema/content, rollback, diverged replay와 post-restoration dbt failure evidence matrix를 작성한다.
  - **Covers:** `Incomplete candidate false-green guard`, `Stale schema or content evidence`, `Replacement rollback evidence`, `Schema-drift safety failure evidence`
  - **Done when:** Failure stage, committed mutation 여부 또는 reconciliation action이 잘못 분류되는 assertion에서 의도한 RED가 발생한다.

- [x] 5.6 **GREEN** — Schema-specific evaluation adapter와 failure mapping을 추가해 pre-mutation, rolled-back, committed post-mutation과 replay failure를 구분한다.
  - **Done when:** Rollback은 no committed mutation/retryable approval, post-dbt failure는 `resume_verification`, diverged target은 새 validation/approval을 반환하며 partition mutation state를 사용하지 않는다.

- [x] 5.7 Reliability evaluation package와 top-level reliability package에서 schema recovery/evaluator public API를 export하고 generic report rendering regression tests를 추가한다.
  - **Done when:** Public import smoke와 report case aggregation이 통과하고 existing volume-drop/null-spike output이 변하지 않는다.

### 6. Documentation and validation

- [x] 6.1 Data Platform, HMDA Data, Data Operations와 Reliability domain documentation에 mutation lock 범위, schema recovery API, table state grain과 external-writer 제한을 반영한다.
  - **Done when:** Canonical docs가 proposal/design의 ownership과 read-only lifecycle boundary를 반복 없이 설명한다.

- [x] 6.2 Data Platform lock, HMDA ingestion, dbt runner, schema recovery와 schema-drift evaluator focused tests 및 existing recovery/evaluation regressions를 실행한다.
  - **Done when:** 관련 node/path tests가 project marker policy로 통과하고 failure가 있으면 owning artifact 또는 implementation으로 route된다.

- [x] 6.3 Ruff, Markdown formatter와 OpenSpec validation을 실행한다.
  - **Done when:** Changed Python/Markdown files와 active Change가 format, lint, frontmatter/header/link 및 `openspec validate --all --json` 검증을 통과한다.

- [x] 6.4 Default pytest suite를 실행하고 validation evidence를 기록한다.
  - **Done when:** `uv run pytest`가 통과하거나 이번 Change와 무관한 baseline/environment failure가 명확히 분류된다.

## Self-Review

- [ ] 모든 관련 Requirement와 Scenario가 구현 및 테스트에 반영되었는지 확인한다.
- [ ] Design의 Decision과 Boundary를 지키면서 중복과 불필요한 복잡성을 제거한다.
- [ ] 관련 테스트, 실패 경로와 정적 검사가 통과하는지 확인한다.
- [ ] 필요한 문서, 설정과 운영 절차를 갱신한다.
- [ ] 알려진 제약과 후속 작업을 명시한다.
