---
type: review
title: System Recovery E2E Test & Oracle Hardening Review
description: PR #220의 도구 격리(PR #221) 및 main 동기화 이후 남은 E2E 테스트 및 오라클 개선 과제에 대한 review-lead 검토 결과다.
status: in_progress
tags:
  - data-operations
  - testing
  - reliability
  - review-lead
  - pr-220
---

# System Recovery E2E Test & Oracle Hardening Review

> [!IMPORTANT]
> **Verdict: Revise (Changes Required).** 무관한 Rulesync 및 Lockfile 변경은 PR #221 머지 및 `main` 동기화를 통해 완결(Resolved)되었습니다. 현재 남은 핵심 과제는 [tests/data_operations/test_system_recovery_e2e.py](../../tests/data_operations/test_system_recovery_e2e.py) 내 (1) 사전 승인 정규식 오버매칭, (2) 분석 마트 얕은 오라클, (3) 라이프사이클 출력 결합 누락, (4) S7 Replay 물리적 무변경(Provenance) 단언 부재, (5) Vertical Slice 평가기 반환 필드 검증 누락 등 5건의 테스트 오라클 방어력 보강입니다.

## Overview

| Target | Revision | Scope | Verdict |
| --- | --- | --- | --- |
| [tests/data_operations/test_system_recovery_e2e.py](../../tests/data_operations/test_system_recovery_e2e.py), [tests/data_operations/test_system_recovery_e2e.design.md](../../tests/data_operations/test_system_recovery_e2e.design.md) | Branch `agent/test/system-recovery-e2e`, Head `d4ceb37b588593c8f7a91a837e42395b23510466` (post `main` sync) | E2E 테스트 오라클, 상태 전이 시나리오, 사전 승인 안전 단언 | Revise (Changes Required) |

`review-lead` 주관 하에 `review-quality`와 `review-adversarial`의 교차 분석을 바탕으로, 실제 결함이 발생했을 때 테스트가 이를 놓치지 않고 안정적으로 포착할 수 있도록(False Green 방지) 세부 오라클 결함을 식별했습니다.

## Resolved Items

### R1. Unrelated Rulesync & Lockfile Changes Separated and Merged

- **Status** - Resolved (Closed)
- **Resolution** - 커밋 `0728c1d`의 Rulesync 및 [uv.lock](../../uv.lock) 변경을 별도 브랜치 `agent/chore/sync-agent-skills-tooling`로 격리하여 PR #221로 분리 후 `main`에 머지 완료. 현재 작업 브랜치에 `origin/main`을 병합하여 PR #220의 diff에서 무관한 6개 파일이 완전히 제거됨.

## Findings

### F1. Pre-Approval Safety Test Regex Overmatching & Exception Masking

- **Severity** - Major
- **Disposition** - `current_required` (`explicit_target`)
- **Location** - [tests/data_operations/test_system_recovery_e2e.py](../../tests/data_operations/test_system_recovery_e2e.py#L527), [tests/data_operations/test_system_recovery_e2e.py](../../tests/data_operations/test_system_recovery_e2e.py#L564)
- **Evidence** - [tests/data_operations/test_system_recovery_e2e.py](../../tests/data_operations/test_system_recovery_e2e.py#L527)에서 `expected_error_match="diverged|일치"`를 사용하여 불일치 예외를 매칭합니다. 패턴에 포함된 `"|일치"`는 상위 단계의 제안 불일치나 소스 불일치 오류까지 모두 매칭(False Green)합니다. 또한 [tests/data_operations/test_system_recovery_e2e.py](../../tests/data_operations/test_system_recovery_e2e.py#L564)의 `expected_error_match="action"` 역시 단순 부분 매칭으로 구체적인 누락 액션 계약을 검증하지 않습니다.
- **Impact** - 타깃 파티션 상태 발산(diverged state) 감지 방어선이 무력화되거나 다른 단계에서 에러가 발생해도 테스트가 통과될 수 있습니다.
- **Required Change** - [tests/data_operations/test_system_recovery_e2e.py](../../tests/data_operations/test_system_recovery_e2e.py#L527)의 단언 패턴을 `expected_error_match=r"diverged state입니다"`로 명확히 한정하고, [tests/data_operations/test_system_recovery_e2e.py](../../tests/data_operations/test_system_recovery_e2e.py#L564)를 `expected_error_match=r"backfill 승인에 필요한 action이 없습니다"`로 구체화합니다.

### F2. Shallow Oracle in Analytics Verification Helper

- **Severity** - Major
- **Disposition** - `current_required` (`explicit_target`)
- **Location** - [tests/data_operations/test_system_recovery_e2e.py](../../tests/data_operations/test_system_recovery_e2e.py#L121-L134), [tests/data_operations/test_system_recovery_e2e.py](../../tests/data_operations/test_system_recovery_e2e.py#L386-L393)
- **Evidence** - `_assert_analytics_outputs` 헬퍼는 `staging_count == expected_rows` 및 `mart_count > 0`만 확인합니다. S0 단계에서 dbt build로 생성된 mart 테이블(2건)이 잔류하므로, S6(복구 후 재검증)에서 dbt build가 mart 갱신에 실패하더라도 `mart_count > 0`은 항상 통과됩니다. 또한 결함 주입 대상이었던 `income` 컬럼의 staging 뷰 null 개수 확인이 누락되었습니다.
- **Impact** - 다운스트림 분석 마트가 실제로 정상 복원되었는지 독립적으로 증명하지 못합니다.
- **Required Change** - `mart_count[0] == 2`를 엄격히 단언하고, staging 모델의 `SELECT count(*) FROM staging.stg_hmda_loans WHERE income IS NULL` 건수가 0임을 직접 확인하는 단언을 추가합니다.

### F3. Unlinked Incident Lifecycle Output in Proposal Binding

- **Severity** - Minor
- **Disposition** - `current_required` (`explicit_target`)
- **Location** - [tests/data_operations/test_system_recovery_e2e.py](../../tests/data_operations/test_system_recovery_e2e.py#L330-L366)
- **Evidence** - [src/hmda_reliability/data_operations/incident_lifecycle.py](../../src/hmda_reliability/data_operations/incident_lifecycle.py)는 복구 제안 바인딩을 위해 `target_content_identity`를 반환하지만, S2에서 `assert lifecycle_result.target_content_identity == dirty_identity` 단언이 누락되었습니다. 또한 S3에서 `_build_proposal` 호출 시 라이프사이클 결과 객체 대신 S1 단계의 로컬 변수 `dirty_identity`를 직접 재사용하여 컴포넌트 간 데이터 전달 계약 검증이 우회되었습니다.
- **Impact** - 인시던트 분석과 복구 제안 간의 실제 런타임 결합 계약이 E2E 수준에서 보장되지 않습니다.
- **Required Change** - S2에 `assert lifecycle_result.target_content_identity == dirty_identity`를 추가하고, S3의 `_build_proposal`에 `approved_before_identity=lifecycle_result.target_content_identity`로 전달하도록 수정합니다.

### F4. Missing Physical Provenance Oracle in S7 Replay

- **Severity** - Major
- **Disposition** - `current_required` (`explicit_target`)
- **Location** - [tests/data_operations/test_system_recovery_e2e.py](../../tests/data_operations/test_system_recovery_e2e.py#L395-L404), [tests/data_operations/test_system_recovery_e2e.design.md](../../tests/data_operations/test_system_recovery_e2e.design.md#L18)
- **Evidence** - [src/hmda_reliability/hmda_data/ingestion/identity.py](../../src/hmda_reliability/hmda_data/ingestion/identity.py)에 따라 `PartitionContentIdentity`는 `ingested_at`을 제외한 논리 다이제스트만을 검사합니다. S7에서 executor가 반환한 `mutation_state == "already_recovered"`와 `actual_identity == clean_identity`만 검증할 뿐, 테이블이 물리적으로 재작성되지 않았음을 증명하는 타임스탬프(`partition_max_ingested_at`) 불변성 검증이 누락되었습니다.
- **Impact** - executor의 분기 결함으로 파티션 교체가 물리적으로 재실행되더라도 동일한 클린 소스가 적재되면 단언을 통과하는 False Green 위험이 있습니다.
- **Required Change** - S7 실행 직전 대상 DB 파티션의 `partition_max_ingested_at`을 기록하고, S7 실행 후 타임스탬프가 엄격히 변경되지 않았음을 단언합니다.

### F5. Missing Assertions on Vertical Slice Result Fields

- **Severity** - Minor
- **Disposition** - `current_required` (`explicit_target`)
- **Location** - [tests/data_operations/test_system_recovery_e2e.py](../../tests/data_operations/test_system_recovery_e2e.py#L450-L460)
- **Evidence** - `evaluate_null_spike_vertical_slice` 평가기는 내부에서 replay를 수행하여 그 결과를 `result.replay`에 담고, dbt 상태를 `result.target_dbt_failure`로 반환합니다. 그러나 `test_null_spike_evaluator_real_dbt_e2e`는 이 두 핵심 필드에 대한 검증을 누락했습니다.
- **Impact** - 수직 슬라이스 내부의 replay 단계가 누락되거나 dbt 실패 컨텍스트가 잔존하더라도 assertion을 통과할 수 있습니다.
- **Required Change** - `assert result.replay is not None`, `assert result.replay.mutation_state == "already_recovered"`, `assert result.target_dbt_failure is None` 단언을 추가합니다.

### F6. Overstated Execution Boundary in Design Document

- **Severity** - Minor
- **Disposition** - `follow_up` (`explicit_target`)
- **Location** - [tests/data_operations/test_system_recovery_e2e.design.md](../../tests/data_operations/test_system_recovery_e2e.design.md#L3-L5)
- **Evidence** - 설계 문서의 "complete loop across the Data Plane" 표현이 Airflow 오케스트레이션 런타임까지 포함하는 것으로 오독될 소지가 있습니다. 실제 구현은 Direct Python API 순차 호출입니다.
- **Impact** - MVP 오케스트레이션 검증 경계와 본 통합 E2E 코어의 범위가 혼동될 수 있습니다.
- **Required Change** - Airflow 런타임을 배제한 "Data Operations ↔ Reliability 결정론적 통합 E2E 코어"임을 문서 Contract에 명시합니다.

## Validation

| Check | Evidence | Result |
| --- | --- | --- |
| Rulesync & Lockfile Isolation | PR #221 머지 및 `origin/main` 병합 완료, PR #220 diff에서 6개 도구 파일 완전 제거 확인 | Pass |
| Codebase Static Diagnostics | [tests/data_operations/test_system_recovery_e2e.py](../../tests/data_operations/test_system_recovery_e2e.py) 정적 분석 및 프로덕션 계약 대조 완료 | Pass |
| Review-Lead Specialist Delegation | `review-quality` 및 `review-adversarial` 독립 위임 및 종합 완료 | Pass |

## Action Items

1. [tests/data_operations/test_system_recovery_e2e.py](../../tests/data_operations/test_system_recovery_e2e.py)의 정규식 오버매칭(`F1`) 수정.
1. `_assert_analytics_outputs` 헬퍼에 마트 2건 및 `income IS NULL` 0건 검증 단언(`F2`) 추가.
1. S2/S3 파이프라인 결과(`lifecycle_result.target_content_identity`) 전달 결합(`F3`) 보강.
1. S7 실행 전후 `partition_max_ingested_at` 타임스탬프 불변 단언(`F4`) 추가.
1. 수직 슬라이스 평가기 테스트에 `result.replay` 및 `result.target_dbt_failure` 단언(`F5`) 추가.
1. [tests/data_operations/test_system_recovery_e2e.design.md](../../tests/data_operations/test_system_recovery_e2e.design.md) 경계 문구 정제(`F6`).
