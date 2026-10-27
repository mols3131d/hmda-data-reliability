---
type: review
title: Reliability Recovery Test Design Review
description: 승인·staging·CAS·복구·replay·mutation evidence의 테스트 설계와 cleanup·profile 정렬 공백을 검토합니다.
---

# Reliability Recovery Test Design Review

> [!NOTE]
> 실제 상태·승인·rollback oracle은 강하다. Staging 종료 실패와 다른 population의 profile 성공을 놓치며, schema replay의 no-replacement 관측이 부족하다.

- **Target**: Reliability recovery의 partition/backfill·schema candidate/executor·runtime evidence.
- **Revision**: `3ab899100fc0b35e23d464bd761f3b144a978ae7`.
- **Scope**: [backfill](../../../../tests/reliability/test_approval_backfill_validation.py), [schema candidate](../../../../tests/reliability/test_schema_recovery_candidate.py), [schema executor](../../../../tests/reliability/test_schema_recovery_executor.py), [runtime evidence](../../../../tests/reliability/test_recovery_runtime_evidence.py) 전체와 관련 계약·교차 E2E.

## Findings

| ID | Severity | Finding | Action |
| --- | --- | --- | --- |
| R1 | Major | commit 뒤 staging cleanup만 실패하면 mutation evidence를 잃는다 | 두 API의 context 종료 실패와 actual after-state 동시 검증 |
| R2 | Major | 다른 population의 빈 profile이 성공 evidence로 붙는다 | profile discriminator와 승인 observation의 정렬 검사 |
| R3 | Minor | schema replay가 동일 상태를 재생성해도 반환값·state만으로 통과할 수 있다 | replacement 진입 부재를 독립 관측 |

## Subview Assessment

| Area | Scenario And Independent Oracle | Mock Boundary And Limit |
| --- | --- | --- |
| Approval/backfill | 승인·action·exact proposal·target scope를 source 접근 전 차단; copy update도 재검증 | 실제 모델·DuckDB·Parquet, 외부 승인 결정은 fixture |
| Content/temporal CAS | diverged/expired/temporal race, 원본 교체 후 approved staged source 사용, exact expected-after | content와 temporal state를 분리해 검사 |
| Post-mutation failure | profile 실패 뒤 actual identity·mutation/reconciliation evidence | 실패 지점만 patch, 실제 DB를 재조회 |
| Schema candidate | schema/content/complete population/dbt 실패, 승인 후·export 도중 변경, immutable proposal | 실제 DB·Parquet·thread, dbt validation callback만 통제 |
| Schema executor | exact approval, 전체 table·다른 partition sentinel, transaction/final-state/profile rollback, shared lock | 실제 DB와 파일, unlock/close fault만 좁게 주입 |
| Replay | before/after/diverged 구분, action·state·profile 재검증 | partition no-write는 E2E의 ingestion timestamp가 보완; schema는 R3 |
| Runtime evidence | overwrite-attempt 로그에 incident/approval/year/table context 보존 | staging·identity·loader가 fake인 로그 unit; 실제 mutation safety 증거는 아님 |

### R1 — Major: Staging Cleanup After Commit

#### Locations: R1

- [test_approval_backfill_validation.py](../../../../tests/reliability/test_approval_backfill_validation.py)
  - 715행은 staging 생성 실패, 634행은 post-mutation profile 실패다.
- [test_schema_recovery_executor.py](../../../../tests/reliability/test_schema_recovery_executor.py)
  - 122행의 cleanup 회귀는 target unlock·connection close를 보호한다.
- [executor.py](../../../../src/hmda_reliability/reliability/recovery/executor.py)
  - `TemporaryDirectory` 종료의 `OSError`가 일반 오류로 포장된다.
- [schema_executor.py](../../../../src/hmda_reliability/reliability/recovery/schema_executor.py)
  - staging directory context가 mutation-aware try 바깥에 있다.

#### Evidence: R1

Caller의 [B1 재현](../validation.md#b1-committed-recovery-cleanup)은 정상 mutation·profile·실제 staging 정리를 마친 후 context 종료에서만 `OSError`를 던졌다. Partition은 expected-after 2행인데 mutation/reconciliation metadata가 없는 `BackfillValidationError`, schema는 expected-after 전체 3행인데 raw `OSError`를 반환했다. 기존 생성·profile·unlock·close 검사는 각각 유효하며 이와 다른 exit 경계다.

#### Impact: R1

DB에는 반영됐지만 caller가 오류만 보고 완료 상태를 판별하기 어려워진다. 데이터가 rollback됐다고 추론하거나 일반 staging 시작 실패와 같은 것으로 처리하면 실제 상태와 기록이 갈라진다.

평가 adapter에서는 이 metadata 부재가 mutation 전 실패로 투영되거나 raw 오류로 빠질 수 있다. [Evaluation 교차 대조](evaluation.md#cross-domain-reconciliation)는 같은 root cause의 affected surface이며 별도 runtime 재현이나 중복 결함으로 세지 않는다.

#### Action: R1

두 API에 context 종료만 실패하는 사례를 추가하고 실제 after-state와 완료 mutation·reconciliation evidence를 함께 요구한다. Commit 후 cleanup의 오류 정책을 정하되 이미 반영된 상태를 숨기지 않아야 한다. 자동 승인 우회나 실제 재변경이 재현됐다고 확대하지 않는다.

### R2 — Major: Profile Population Binding

#### Locations: R2

- [backfill request](../../../../src/hmda_reliability/reliability/recovery/request.py)
  - `_validate_profile_partition`: table·partition 값 중심 검증.
- [schema request](../../../../src/hmda_reliability/reliability/recovery/schema_request.py)
  - `_validate_exact_approval`: profile table·partition label 검증.
- [backfill 테스트](../../../../tests/reliability/test_approval_backfill_validation.py)
  - 812행 fixture는 정상 연도 선택 컬럼을 사용한다.
- [schema 테스트](../../../../tests/reliability/test_schema_recovery_executor.py)
  - 543행 fixture도 정상 discriminator만 사용한다.

#### Evidence: R2

정상 constructor 검증을 통과한 request에서 partition `2025`를 유지하고 `partition_column="income"`만 지정하면 두 API 모두 성공·`validation_passed=True`와 profile 0행을 반환한다. [B2 재현](../validation.md#b2-profile-scope-alignment)의 실제 target은 expected-after와 같고 observation은 2행이다. Identity 검증이 잘못된 것이 아니라 그 결과와 결합된 profile population이 다르다.

#### Impact: R2

복구한 observation과 다른 데이터의 profile이 성공 evidence로 남는다. 계산 예외만 검사하는 기존 negative case는 계산 자체가 정상 완료되는 이 오류를 구별하지 못한다.

#### Action: R2

정상 검증된 입력에서 discriminator만 바꾸는 negative scenario를 추가한다. 요청을 거부해 target을 보존하거나 승인된 observation population과 일치하는 profile을 요구한다. `activity_year`·`source_year`처럼 현재 허용하는 동등한 scope는 유지해야 하며, content 검증에 임의의 품질 정책을 합치는 수정은 제안하지 않는다.

### R3 — Minor: Schema Replay No Replacement

#### Locations: R3

- [test_schema_recovery_executor.py](../../../../tests/reliability/test_schema_recovery_executor.py)
  - 104행은 exact state와 `already_restored`·`resume_verification`·actions를 검사한다.
- [System recovery E2E](../../../../tests/data_operations/test_system_recovery_e2e.py)
  - 402행은 partition replay의 timestamp 보존을 별도로 보호한다.

#### Evidence: R3

동일 Parquet로 table을 다시 교체한 뒤 정상 replay labels를 반환하는 구현은 같은 schema/content identity를 만들 수 있다. 현재 expected-after branch는 올바르게 replacement를 건너뛴다. 이 항목은 정적 설계 공백이며 mutant 실행 결과가 아니다.

#### Action: R3

Schema replay에서 `_replace_table` 진입 시 실패하는 관측을 추가하고 실제 profile verification·state 비교를 유지한다. Partition recovery 전체의 no-write 공백으로 확대하지 않는다.

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 두 관점 full-body 검토 | Batch B, 관련 승인·계약·safeguard 대조 |
| ✅ Pass | 현재 정상 suite | [전체 실행 근거](../validation.md#test-execution) |
| ❌ Fail | staging 종료의 mutation evidence | B1 두 경로 재현 |
| ❌ Fail | profile population alignment | B2 두 경로 재현 |
| ⚪ Not Verified | schema replay mutant | 정적 도출, 실행하지 않음 |

## Risks And Limits

실제 filesystem 장애 빈도·모든 resource failure 조합·운영 승인 절차를 검증하지 않았다. 이번 작업에서 승인 모델이나 복구 동작을 변경하지 않았다. 모든 finding은 후속 제안이다.
