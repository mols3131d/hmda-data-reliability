---
type: report
title: Schema Drift Exact Table Restoration 코드 및 설계 리뷰 보고서
description: reliability-schema-recovery-exact-table-restoration OpenSpec change 구현 범위, contract 안전성, 테스트 커버리지 및 오버엔지니어링 감사 결과를 기록한다.
tags:
  - reliability
  - schema-drift
  - code-review
  - handoff
---

# Schema Drift Exact Table Restoration 리뷰 보고서

> [!NOTE]
> 이 문서는 OpenSpec archive와 PR 생성 **직전 시점의 historical review snapshot**이다. 이후 Self-Review, Specs sync, PR 생성과 archive가 완료됐다. 현재 보존된 Change는 [`openspec/changes/archive/2026-08-16-reliability-schema-recovery-exact-table-restoration/`](../../openspec/changes/archive/2026-08-16-reliability-schema-recovery-exact-table-restoration/)에 있으며, 아래 Handoff의 “다음 단계”는 당시 시점의 기록이다.

## 1. Executive Summary

| 항목 | 내용 |
| --- | --- |
| **대상 Change** | [`reliability-schema-recovery-exact-table-restoration`](../../openspec/changes/archive/2026-08-16-reliability-schema-recovery-exact-table-restoration/proposal.md) |
| **리뷰 결과** | **APPROVED** (결함 없음, 전 항목 통과) |
| **검토 범위** | Data Platform mutation lock, HMDA ingestion, dbt runner lock, Table State / Schema Recovery contracts & executor, Schema-drift evaluation slice, 도메인 문서 및 테스트 일체 |
| **핵심 성과** | DuckDB transaction + `fcntl` cooperative lock 기반 안전한 exact table restoration 및 멱등 replay 보장 |
| **다음 단계** | 당시 기준 Self-Review 5개 완료 처리 (`33/33`), OpenSpec specs sync, Commit & PR 생성 |

---

## 2. 영역별 상세 검토 결과

### 1) Data Platform: Cooperative Mutation Lock

- **구현 검토 (`src/project_pivot/data_platform/duckdb.py`)**:
  - `canonical_path = Path(database_path).resolve(strict=False)`를 통한 canonical lock path 유도 (`.{name}.mutation.lock`).
  - `:memory:` 및 `None` 연결에 대한 no-op 처리로 불필요한 파일 I/O 방지.
  - Body exception 우선 보존 패턴 (`body_failed` 플래그)으로 에러 은폐 방지.
- **평가**: 표준 라이브러리 `fcntl` 기반의 가장 단순하고 견고한 잠금 구현 (YAGNI 준수).

### 2) HMDA Ingestion & dbt Operations Lock 참여

- **구현 검토 (`hmda_data/ingestion/`, `data_operations/runner.py`)**:
  - `load_hmda_loans` 및 `load_hmda_loans_partition`이 `current_database_path(connection)`을 통해 mutation lock에 참여.
  - 파티션 적재 시 lock 획득 후 `expected_identity`를 재계산하여 concurrent write로 인한 stale state를 안전하게 거부 (`HMDAStalePartitionError`).
  - `run_dbt_build`가 target DuckDB lock을 프로세스 시작 전 획득하고 subprocess 종료까지 유지. Lock 실패 시 프로세스를 시작하지 않고 `DataOperationError`로 변환.
- **평가**: 외부 의존성 추가 없이 writer 직렬화 경계를 보호.

### 3) Reliability Contracts & State Identity

- **구현 검토 (`reliability/contracts/`, `reliability/profiling/`)**:
  - `TableStateIdentity`: `schema_hash`, `row_count`, 정렬된 distinct `source_year` partition identities 결합. Duplicate year, null year, 누락 population을 불변 모델 validator에서 사전 차단.
  - `SchemaRecoveryProposal` / `SchemaRecoveryApproval`: 파티션 recovery 모델과 speculatively 통합하지 않고, exact table-wide restoration에 필요한 전용 contract로 분리하여 SRP 준수.
  - `observation_partition`과 실제 `table_name` mutation scope를 명시적으로 분리.
- **평가**: 모델 간 결합도를 낮추고 데이터 무결성을 타입 및 validation 레벨에서 강제함.

### 4) Candidate Preflight & Transactional Executor

- **구현 검토 (`reliability/recovery/`)**:
  - `preflight_schema_recovery_candidate`: Target 접근 및 승인 전에 candidate database의 exact schema, complete content, dbt projection을 사전 검증.
  - `stage_approved_schema_recovery_candidate`: 승인 후 candidate database lock 아래에서 검증 후 임시 Parquet로 staging하여 불변 snapshot 생성.
  - `execute_approved_schema_recovery`:
    - Target lock 획득 후 before/after/diverged 3개 상태로 분기.
    - Before state: 단일 DuckDB transaction에서 `CREATE OR REPLACE TABLE ... read_parquet(...)`, exact after-state 검증, aligned profile snapshot 생성 수행. 실패 시 rollback 및 `retry_same_approval` 반환.
    - Expected after state (Replay): Target 변경 없이 `resume_verification`으로 downstream 검증 재개.
    - Diverged state: 추가 mutation 없이 `request_new_validation_and_approval` 요구.
- **평가**: 부분 실패 시 rollback 및 Before 상태 보존을 계약과 test로 검증함.

### 5) Schema-drift Evaluation Vertical Slice

- **구현 검토 (`reliability/evaluation/schema_drift.py`)**:
  - Disposable DB 경로 사전 검증 (`clean`, `target`, `candidate` 경로 중복/기존 파일 차단).
  - 실제 `loan_amount: VARCHAR` drift를 주입하여 clean baseline 대비 drift 탐지 -> 승인 -> 복구 -> Replay -> Lifecycle 해소 -> downstream dbt build 성공까지 E2E acceptance 증명.
  - Read-only lifecycle 경계 보존 (lifecycle 단독 호출 시 승인/복구/리포트 쓰기 미발생).
- **평가**: 합성 데이터셋 기반으로 전체 복구 생명주기를 deterministic하게 검증 가능.

---

## 3. 오버엔지니어링 & 단순성 감사 (Ponytail Audit)

- **Standard Library / Native 우선**: 복잡한 분산 락, 메타데이터 카탈로그, 또는 generic DDL migration 엔진 대신 `fcntl.flock`과 DuckDB의 네이티브 `read_parquet` 트랜잭션을 활용.
- **YAGNI 원칙 준수**: Partition recovery와 Table schema recovery를 억지로 하나의 복잡한 다형성 클래스로 추상화하지 않고, 각자의 불변 계약으로 단순 분리.
- **Minimal Surface**: Single-host cooperative contract로 범위를 명확히 제한하여 오버헤드 최소화.

---

## 4. Self-Review 체크리스트 검증 결과

Archived OpenSpec [tasks.md](../../openspec/changes/archive/2026-08-16-reliability-schema-recovery-exact-table-restoration/tasks.md)의 Self-Review 5개 항목에 대한 당시 검토 결과:

- [x] **Requirement & Scenario 반영 확인**: Composite table state, Candidate preflight, Exact approval, Scope separation, Transactional restoration, Post-restoration result, Replay reconciliation, Read-only lifecycle 전 시나리오 반영 완료.
- [x] **Decision & Boundary 준수 및 단순성 확인**: D1~D8 Decision 충족, 단일 호스트 cooperative lock, read-only lifecycle 분리 유지, 불필요한 복잡성 제거.
- [x] **테스트 및 정적 검사 통과 확인**: 152개 focused regression, 267개 default pytest suite, Ruff format/lint 및 Markdown/OpenSpec validation 통과 확인.
- [x] **도메인 문서 갱신 확인**: `data-operations.md`, `data-platform.md`, `hmda-data.md`, `reliability.md` 4개 도메인 문서에 잠금 및 스키마 복구 경계 명시 완료.
- [x] **제약 및 후속 작업 명시 확인**: Single-host 제한, `raw.hmda_loans` 단일 테이블 범위, name/type 스키마 한계 등 Known boundaries 문서화 완료.

---

## 5. Handoff & 재개 가이드 (Historical Next Actions)

다음 항목은 **리뷰 당시의 후속 절차**이며 현재는 완료된 historical record다.

1. **OpenSpec Tasks 완료 처리**:
   - archived [tasks.md](../../openspec/changes/archive/2026-08-16-reliability-schema-recovery-exact-table-restoration/tasks.md)의 Self-Review 5개 체크 및 `tasks_completed: 33`으로 업데이트.
1. **OpenSpec Specs 동기화**:
   - delta Specs를 canonical Specs와 sync.
1. **VCS Commit & PR 생성**:
   - 변경 사항을 커밋 단위로 정리하고 PR 생성 (`docs/development/vcs-git/README.md` 가이드 준수).
1. **OpenSpec Archive**:
   - 완료된 Change를 archive.
