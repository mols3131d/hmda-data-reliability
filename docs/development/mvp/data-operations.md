# MVP Domain Milestone: Data Operations

## Goal

HMDA ingestion과 dbt build를 명시적인 request/result 경계로 조합하고, 실패한 실행이
current Data Lake state를 암묵적으로 변경하지 않게 한다.

## Outcomes

- 하나의 실행 request가 target database, source scope와 dbt target을 명확히 식별한다.
- Bronze ingestion과 dbt build 결과를 구조화된 결과와 오류로 구분할 수 있다.
- candidate 또는 failed dbt execution은 current artifact state를 바꾸지 않는다.
- 검증된 결과만 current evidence로 promotion할 수 있다.
- Reliability lifecycle에 필요한 raw/dbt identity를 caller에게 전달할 수 있다.

## Done When

대표 HMDA 실행을 raw load → dbt build까지 재현하고, 성공 결과와 실패 결과가
current state를 오염시키지 않는 명확한 execution contract로 관찰되면 완료한다.

## Non-Goals

- incident detection rule과 LLM 판단
- approval policy와 recovery mutation 구현
- scheduler policy, retry scheduler 또는 production workflow engine

## References

- [Data Operations Domain](../../domains/data-operations.md)
- [MVP](README.md)
- `tests/data_operations/`
