---
type: openspec-spec-driven-tdd-tasks
category: tasks
---

# Tasks: Orchestration Quality Gate

## Task 1: `QualityGateError` 및 `evaluate_quality_gate` 도메인 함수 구현

**Result:** `src/hmda_reliability/orchestration/quality_gate.py`가 존재하며, `evaluate_quality_gate(request)` 호출 시 이상이 없으면 정상 반환하고, 이상이 탐지되면 `QualityGateError`를 발생시킨다.

**Completion:**

- [x] `QualityGateError` 예외 클래스가 정의되어 있다.
- [x] `evaluate_quality_gate(request: DataOperationRequest) -> None`이 정의되어 있다.
- [x] 내장 baseline이 `profile_columns`와 일치하는지 사전 검증된다.
- [x] `create_profile_snapshot` → `detect_basic_incidents` 순서로 호출한다.
- [x] 이상 탐지 시 `QualityGateError`가 발생하고 탐지된 인시던트 유형이 메시지에 포함된다.
- [x] 이상 없으면 예외 없이 반환된다.
- [x] Airflow 의존성이 없다.
- [x] 단위/통합 테스트가 통과한다.

## Task 2: DAG thin-adapter에 `evaluate_quality_gate` 태스크 추가

**Result:** `hmda_data_plane` DAG에 `evaluate_quality_gate` 태스크가 추가되고, `load_raw_hmda_loans → evaluate_quality_gate → build_dbt_loan_analytics` 실행 순서가 보장된다.

**Completion:**

- [x] `evaluate_quality_gate` Airflow 태스크가 DAG에 정의되어 있다.
- [x] `QualityGateError` 발생 시 `AirflowException`으로 변환된다.
- [x] 이상 탐지 시 태스크가 실패하고 `build_dbt_loan_analytics`는 실행되지 않는다.
- [x] 이상 없으면 태스크가 정상 완료되고 `build_dbt_loan_analytics`가 실행된다.
- [x] `source_year`, `asset_name`, `detected_incident_types` 또는 `status: clean`이 로그에 기록된다.
- [x] 통합 테스트가 통과한다.
