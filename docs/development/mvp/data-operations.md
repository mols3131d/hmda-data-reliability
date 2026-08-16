# MVP Domain: Data Operations

## Mission

Data Lake의 ingestion, dbt execution과 Reliability 호출을 **명시적이고 실패에 안전한 실행
계약**으로 연결한다.

Data Operations domain은 각 domain의 기능을 다시 구현하지 않는다. 단계 사이에서 무엇이
실행됐고 무엇이 current state로 채택됐는지를 분명하게 만들어 MVP의 end-to-end proof가
우연한 side effect에 의존하지 않게 한다.

## MVP Contribution

- ingestion과 dbt stage를 명시적인 request/result boundary로 실행한다.
- candidate validation과 current promotion을 구분한다.
- 실패한 candidate나 incomplete execution이 current data/dbt evidence를 암묵적으로 바꾸지 않게 한다.
- Reliability가 판단에 필요한 target state와 dbt evidence identity를 전달받을 수 있게 한다.
- failure가 state change 전인지 후인지 구분할 수 있는 execution evidence를 제공한다.

## Done When

같은 pipeline action의 success/failure가 구조화된 결과로 구분되고, 실패한 작업은 기존
current state를 보존하며 성공한 결과만 명시적인 boundary를 통해 채택된다.

완료 판단은 orchestration step 수가 아니라 다음 proof로 한다.

- pre-validation failure가 current state를 변경하지 않는다.
- 성공한 target validation 뒤에만 current evidence가 갱신된다.
- downstream Reliability가 실행 결과와 evidence identity를 연결할 수 있다.
- post-mutation failure가 pre-mutation failure와 다른 reconciliation 대상으로 남는다.

## Boundary

**Owns**

- stage execution request/result
- dbt execution과 promotion boundary
- cross-domain execution sequencing
- stage-level failure evidence

**Does not own**

- source parsing과 schema semantics
- DuckDB/dbt storage primitives 자체
- incident rule과 Agentic reasoning
- recovery authorization과 mutation policy
- Dagster graph definition

## Acceptance Evidence

- `src/project_pivot/data_operations/`
- `tests/data_operations/`
- 관련 stage-execution / incident-lifecycle OpenSpec

## References

- [MVP](README.md)
- [Data Operations Domain](../../domains/data-operations.md)
