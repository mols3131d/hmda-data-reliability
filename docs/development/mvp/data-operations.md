# MVP Goal: Data Operations

## Goal

MVP validation이 current data와 dbt evidence를 암묵적으로 변경하지 않도록 실행 경계를 조합하고, recovery 판단에 필요한 identity를 reliability 계층으로 전달한다.

## MVP Responsibilities

- dbt build를 run-scoped target에서 실행하고 candidate artifact를 반환한다.
- downstream validation을 통과한 artifact만 explicit promotion으로 current projection에 반영한다.
- incident lifecycle에 target content identity와 dbt projection identity를 전달한다.
- 실패 원인을 호출자가 구분할 수 있는 application error boundary를 유지한다.

## Done When

- failed candidate dbt run은 current artifact projection을 변경하지 않는다.
- successful candidate도 명시적 promotion 전에는 current projection을 변경하지 않는다.
- lifecycle 결과가 recovery proposal을 만들기에 충분한 current identities를 포함한다.
- validation 이전과 이후의 실패 경계가 evidence에서 구분된다.

## Non-Goals

- incident rule, approval policy와 recovery mutation 자체
- Dagster에서 reliability lifecycle 자동 실행

## References

- [Data Operations Domain](../../domains/data-operations.md)
- [MVP Goal](../../mvp.md)
- `tests/data_operations/`
