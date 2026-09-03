# Design: Orchestration Quality Gate

기존 `orchestration-pipeline` architecture를 따른다.

## Non-obvious Technical Delta

### DAG task 배치

`evaluate_quality_gate`는 `load_raw_hmda_loans` 완료 후, `build_dbt_loan_analytics` 시작 전에 실행된다.

```text
load_raw_hmda_loans → evaluate_quality_gate → build_dbt_loan_analytics
```

### baseline 제공 방식

현재 MVP 범위에서 baseline 저장소는 Out of Scope다.
baseline은 `_BASELINE_NULL_RATES` 정적 매핑을 통해 내장하며, `profile_columns`와 일치 여부를 사전 검증한다.

### 이상 탐지 후 실패 방식

`detect_basic_incidents()` 결과에서 이상이 탐지되면 `QualityGateError`를 발생시키고, DAG 어댑터가 이를 `AirflowException`으로 변환하여 태스크를 명시적 실패로 전환한다.

### 새 모듈 위치

`src/hmda_reliability/orchestration/quality_gate.py`

- `evaluate_quality_gate(request: DataOperationRequest) -> None` 함수를 노출한다.
- 내부적으로 `create_profile_snapshot` → `_build_baseline` → `detect_basic_incidents`를 순서대로 호출한다.
- `AirflowException`은 DAG 파일에서만 import하고, `quality_gate.py`는 Airflow에 의존하지 않는다.
  - 이상 탐지 시 `QualityGateError`(도메인 예외)를 발생시키고, DAG 어댑터가 이를 `AirflowException`으로 변환한다.
