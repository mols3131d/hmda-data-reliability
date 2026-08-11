# MVP Goal: Data Operations

## Goal

Candidate validation과 reliability lifecycle을 조합하면서 검증 이전의 작업이 current data 또는 dbt evidence를 암묵적으로 바꾸지 않게 한다.

## Outcomes

- candidate 또는 failed dbt execution은 current artifact state를 변경하지 않는다.
- current dbt evidence는 target validation이 성공한 뒤에만 변경될 수 있다.
- incident lifecycle 결과가 recovery 판단에 필요한 target와 dbt evidence identity를 전달한다.
- pre-validation failure와 post-mutation verification failure를 caller가 구분할 수 있다.

## Non-Goals

- incident rule과 approval policy
- recovery mutation 자체
- Dagster에서 reliability lifecycle 자동 실행

## References

- [Data Operations Domain](../../domains/data-operations.md)
- [MVP Goal](../../mvp.md)
- `tests/data_operations/`
