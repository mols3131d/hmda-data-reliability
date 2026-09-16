# Design: Orchestration Quality Gate

기존 `orchestration-pipeline` architecture를 따른다.

## Non-obvious Technical Delta

### DAG task 배치

`evaluate_quality_gate`는 `load_raw_hmda_loans` 완료 후, `build_dbt_loan_analytics` 시작 전에 실행된다.

```text
load_raw_hmda_loans → evaluate_quality_gate → build_dbt_loan_analytics
```

독립 gate task는 canonical dbt source relation인 `raw.hmda_loans`의 전체 Bronze population을 평가한다. 요청 파티션은 observed partition 유무와 관계없이 항상 평가하며, `activity_year`가 `NULL`인 행은 profile 밖으로 제외하지 않고 blocking population 오류로 처리한다. Analytics task는 task 사이 상태 변경을 차단하기 위해 `run_quality_gated_dbt_build()`를 호출한다. 이 API는 bundled `dbt` project와 profile configuration만 허용하고, database mutation lock 안에서 동일한 전체 gate를 재검증한 뒤 lock을 유지한 채 dbt subprocess를 시작한다. 기존 `run_dbt_build()`는 configurable project/profile을 사용하는 orchestration과 분리된 독립 stage API로 유지한다.

### Quality policy ownership

현재 MVP 범위에서 baseline 저장소는 Out of Scope다. 정적 baseline, threshold, 활성 detector와 blocking 판정은 Reliability public boundary가 소유한다. Data Operations는 `DataOperationRequest`를 current profile 생성과 Reliability gate 호출로 조합하고, Airflow task는 성공 또는 domain failure를 task state로 번역한다.

정적 null-rate baseline은 repository가 보존한 accepted 2025 actual-source profile과 일치시킨다. `income`은 `0.16168766279822375`, `loan_amount`는 `0.0`을 사용하고, null spike는 이 기준에서 5%p 이상 증가할 때만 blocking한다.

### 이상 탐지 후 실패 방식

Reliability quality gate 결과에서 blocking 이상이 탐지되면 `QualityGateError`를 발생시키고, DAG 어댑터가 이를 `AirflowException`으로 변환하여 태스크를 명시적 실패로 전환한다.

### Boundary Changes

| Boundary | Owns | Does Not Own |
| --- | --- | --- |
| `reliability` | 정적 baseline, threshold, 활성 detector, blocking 판정과 `QualityGateError` | Airflow request/context와 task state |
| `data_operations` | 전체 Bronze partition profile 생성, Reliability gate 호출과 lock-bound quality-gated dbt build 조합 | quality policy와 Airflow exception translation |
| `orchestration` | task dependency, runtime request 구성, `QualityGateError`를 `AirflowException`으로 번역 | baseline, threshold, detector 선택과 blocking rule |
