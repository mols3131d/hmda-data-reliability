## ADDED Requirements

### Requirement: Reusable pipeline stage functions

시스템은 raw 적재, dbt build, incident lifecycle용 Dagster 비종속 Python 함수를 제공해야 한다(SHALL).

#### Scenario: 단계 함수 직접 호출

- **WHEN** 코드가 유효한 request로 단계 함수를 호출할 때
- **THEN** 함수는 해당 단계의 결과 모델을 반환해야 한다.
- **AND** 다른 단계의 실행 순서를 조율하지 않아야 한다.
