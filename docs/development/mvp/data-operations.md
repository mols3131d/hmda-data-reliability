# MVP Domain: Data Operations

## Mission

Data Lake의 ingestion, dbt execution과 Reliability 호출을 **명시적인 실행·채택 boundary**로
연결하고, 각 stage의 side effect와 failure를 caller가 구분할 수 있게 한다.

Data Operations domain은 각 domain의 기능을 다시 구현하지 않는다. 무엇을 실행했고 어떤
결과를 current artifact로 채택했는지, 실패가 어느 state-change boundary에서 발생했는지를
명시해 MVP의 end-to-end proof가 암묵적인 side effect에 의존하지 않게 한다.

## MVP Contribution

- ingestion과 dbt stage를 명시적인 request/result boundary로 실행한다.
- dbt build candidate와 current artifact projection의 채택을 분리한다.
- 실패한 candidate artifact가 last-known-good current artifact projection을 자동으로 대체하지 않게 한다.
- mutation 가능 stage의 failure가 발생 위치와 후속 reconciliation 판단에 필요한 evidence를 남기게 한다.
- Reliability가 판단에 필요한 target state와 dbt evidence identity를 전달받을 수 있게 한다.

## Done When

같은 pipeline action의 success/failure가 구조화된 결과로 구분되고, **candidate 생성과 current
artifact 채택이 별도 사건**으로 유지되며 mutation 가능 failure의 실제 결과를 숨기지 않는다.

완료 판단은 orchestration step 수가 아니라 다음 proof로 한다.

- source validation처럼 mutation 전 실패는 target 변경 전에 중단된다.
- dbt build 성공 자체가 current artifact projection을 자동으로 바꾸지 않는다.
- failed/incomplete candidate가 last-known-good current artifact pair를 자동으로 대체하지 않는다.
- downstream Reliability가 실행 결과와 채택된 evidence identity를 연결할 수 있다.
- mutation 이후 실패는 rollback을 가정하지 않고 별도 reconciliation 대상으로 식별된다.

이 gate는 모든 stage에 transactional rollback을 약속하지 않는다. 특히 dbt build는 target
DuckDB를 변경할 수 있으므로 실패 시 보존되는 상태와 reconciliation은 owning runtime contract와
evidence에 따라 판단한다.

## Boundary

**Owns**

- stage execution request/result
- dbt execution과 artifact promotion boundary
- cross-domain execution sequencing
- stage-level failure와 reconciliation evidence

**Does not own**

- source parsing과 Source→Bronze load semantics
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
