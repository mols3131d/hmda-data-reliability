---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: Airflow 신뢰성 품질 게이트 구축 작업
description: Airflow data-plane DAG에 신뢰성 품질 게이트 태스크를 추가하고 이상 발생 시 파이프라인 실패를 보장한다.
tasks_completed: 5
tasks_total: 5
---

# Tasks: Orchestration Quality Gate

- [x] Task 1: `QualityGateError` 및 `evaluate_quality_gate` 도메인 함수 구현
  - **Result:** `reliability.evaluate_profile_quality_gate(current)`가 baseline, threshold, detector와 blocking 판정을 소유하고, `data_operations.evaluate_quality_gate(request)`가 current profile I/O를 조합한다. 이상 탐지 시 `QualityGateError`가 발생하고, 두 경계 모두 Airflow에 의존하지 않으며 단위/통합 테스트가 통과한다.

- [x] Task 2: DAG thin-adapter에 `evaluate_quality_gate` 태스크 추가
  - **Result:** `hmda_data_plane` DAG에 `evaluate_quality_gate` 태스크가 추가되고, `load_raw_hmda_loans → evaluate_quality_gate → build_dbt_loan_analytics` 실행 순서가 보장된다.
  - `evaluate_quality_gate` Airflow 태스크가 DAG에 정의되어 있다.
  - `QualityGateError` 발생 시 `AirflowException`으로 변환된다.
  - 이상 탐지 시 태스크가 실패하고 `build_dbt_loan_analytics`는 실행되지 않는다.
  - 이상 없으면 태스크가 정상 완료되고 `build_dbt_loan_analytics`가 실행된다.
  - `source_year`, `asset_name`, `detected_incident_types` 또는 `status: clean`이 로그에 기록된다.
  - 통합 테스트가 통과한다.

- [x] Task 3: Quality policy를 Reliability public boundary로 이동
  - **Done when:** 정적 baseline이 accepted 2025 actual-source profile과 일치하고, threshold, detector 선택, 필수 profile column의 정확한 coverage, null spike와 empty partition만 포함하는 blocking 판정이 `reliability`에 위치하며, 약 16%의 정상 income null rate는 통과하고 baseline 대비 5%p 이상 증가는 차단하는 integration regression이 통과한다. Profile coverage 거부 로그는 partition identity를 보존하고, `data_operations`가 request를 current profile과 gate 호출로 조합하며 Airflow DAG는 `QualityGateError`만 task failure로 번역한다.
  - **Covers:** `Data quality gate execution`의 `Delegated quality policy` scenario
  - **Test first:** 필수 `income` profile을 누락한 요청이 현재 gate를 우회하는 동작, Orchestration package가 policy를 소유하지 않는 경계와 예상 밖 오류가 broad normalization되지 않는 동작을 회귀 테스트로 고정한다.

- [x] Task 4: 3-stage data-plane durable contract 동기화
  - **Done when:** architecture, orchestration domain guide와 canonical orchestration spec이 raw load → read-only blocking quality gate → analytics build 순서, gate failure의 downstream blocking, `run_dbt_build=false`에서 gate 실행 후 analytics만 skip되는 의미를 일관되게 설명하고 Markdown/OpenSpec 검증을 통과한다.
  - **Covers:** `Data quality gate execution`, `Disabled analytics skip semantics`

- [x] Task 5: dbt input 전체 gate와 lock-bound build 재검증
  - **Done when:** 독립 gate task가 canonical `raw.hmda_loans.activity_year`의 전체 Bronze population을 평가하고, 요청하지 않은 dirty 파티션, 요청 파티션 부재와 `NULL` partition discriminator를 차단하며 alternate relation/column request를 거부한다. `run_quality_gated_dbt_build()`는 bundled canonical dbt project/profile만 허용하고 database mutation lock 안에서 동일 gate를 재검증한 뒤 같은 lock에서 dbt subprocess를 시작하며, analytics task는 재검증 `QualityGateError`를 causal context가 보존된 `AirflowException`으로 변환한다. 독립 `run_dbt_build()`의 configurable project/profile 동작은 유지된다.
  - **Covers:** `Dirty non-requested partition`, `Canonical dbt source relation`, `Canonical quality-gated dbt configuration`, `Requested partition is absent`, `Missing partition discriminator`, `Bronze changes after gate task`
  - **Test first:** clean 요청 파티션과 dirty 비대상 파티션이 공존할 때 현재 gate가 통과하는 동작, lock 안 재검증 없이 dbt subprocess가 시작되는 동작을 실패 테스트로 고정한다.
