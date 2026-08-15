# Next Reliability Milestone: Schema-Drift Recovery Vertical Slice

`volume_drop`과 `null_spike` recovery vertical slice 완료 이후 선정된 차기 Reliability milestone 정의 문서다.

## 1. 재사용 가능한 Contract 자산

`volume_drop` 및 `null_spike` 구현에서 확립되어 `schema_drift`에 직접 재사용 가능한 계약과 실행 자산:

| 영역 | 재사용 Contract / API | 역할 및 보증 |
| --- | --- | --- |
| **Read-Only Lifecycle** | `run_incident_lifecycle`, `detect_basic_incidents` | `schema_drift` (schema hash 불일치) 탐지, manifest 기반 lineage 영향 분석, 결정론적 `RemediationDraft` 생성. 데이터 변경 없음 보증. |
| **Approval Contract** | `RecoveryProposal`, `Approval`, `ApprovedBackfillRequest`, `ApprovalGateError` | incident, 대상 partition, candidate identity, 승인 전후 상태, target action을 immutable하게 결합. 불일치 시 mutation 전 차단. |
| **Recovery Execution** | `execute_approved_backfill`, `BackfillValidationResult` | DuckDB 트랜잭션 기반 compare-and-replace, replay idempotency (`already_recovered` 시 `resume_verification`), content/schema identity oracle. |
| **Evaluation Framework** | `build_recovery_evaluation_case`, `write_evaluation_report` | isolated disposable database preflight (target, clean, candidate 독립 검증), pre-mutation/post-mutation 실패 구분, structured exception handling. |

## 2. Milestone 선정: `schema_drift` Recovery Vertical Slice

### 선정 이유

- **최소 범위 (Smallest Capability):** 기본 탐지 항목(`volume_drop`, `null_spike`, `schema_drift`, `freshness_delay`) 중 `schema_drift`는 동일한 단일 partition/table 트랜잭션 복구 경계 내에 위치한다.
- **Orchestration 의존성 배제:** `freshness_delay`는 파이프라인 스케줄링 및 wall-clock 시간 의존성을 포함하지만, `schema_drift`는 결정론적 fixture와 schema hash oracle로 완결된다.
- **YAGNI / 메타 작업 방지:** 신규 workflow나 거대 추상화 없이 기존 safety primitives 위에 vertical slice로 확장 가능하다.

## 3. Milestone 정의

### Scope

- **In Scope:**
  - 단일 partition 대상 controlled `schema_drift` synthetic defect (컬럼 변경/누락으로 인한 schema hash 불일치).
  - Clean baseline fixture로부터 expected schema hash 및 content identity 유도.
  - Candidate schema hash 검증 (불일치 시 mutation 전 거부).
  - Approved recovery를 통한 schema 및 content의 정확한 복원 검증.
  - Replay stability (중복 overwrite 방지 및 verification 재개).
  - Safety failure 경로 (invalid candidate, stale target, incomplete approval, downstream dbt failure) 구조화 evidence 검증.
- **Out of Scope:**
  - Multi-table / Multi-partition 동시 drift 복구.
  - Schema migration 자동 생성 및 DDL 자동 실행.
  - Human approval UI 및 자동 승인.

### Owning Packages

- `project_pivot.reliability`: `evaluate_schema_drift_vertical_slice`, evaluation case builder, report.
- `project_pivot.data_operations`: 기존 read-only lifecycle 및 stage execution (변경 없음/재사용).
- `project_pivot.data_platform` / `project_pivot.hmda_data`: 테이블 및 dbt 모델 계약 (재사용).

### Validation Boundary

- **Isolated Workspace:** target, workspace clean, candidate database의 상호 독립 및 사전 부재 preflight 검증.
- **Deterministic Oracles:** schema hash 일치 및 post-recovery incident 해소 검증.
- **Spec-Driven TDD:** OpenSpec change 생성 후 RED/GREEN 사이클로 구현.
