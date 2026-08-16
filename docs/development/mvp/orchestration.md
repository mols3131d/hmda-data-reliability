# MVP Domain: Orchestration

## Mission

최소 Data Lake의 data plane을 **로컬에서 반복 실행 가능한 Dagster dependency graph**로 제공한다.

Orchestration domain은 business logic을 흡수하지 않는다. 이미 정의된 ingestion과 dbt
capability를 관찰 가능한 실행 단위로 연결해, MVP가 수동 함수 호출 모음이 아니라 하나의
재실행 가능한 pipeline임을 증명한다.

## MVP Contribution

- Bronze ingestion과 dbt analytical layer의 dependency를 Dagster graph로 표현한다.
- 실행 config를 domain request로 변환하는 얇은 boundary를 유지한다.
- 같은 local input으로 data plane을 다시 실행할 수 있게 한다.
- asset/run 결과가 downstream Reliability가 사용할 data/dbt state와 모순되지 않게 한다.
- Reliability, Agentic review와 approval lifecycle을 data plane에 암묵적으로 자동 결합하지 않는다.

## Done When

로컬 Dagster execution으로 HMDA source에서 Bronze와 dbt analytical layer까지의 최소 data
plane을 재실행할 수 있고, 각 asset의 책임이 owning domain contract를 우회하지 않는다.

완료 판단은 asset 수가 아니라 다음 proof로 한다.

- Bronze가 dbt analytical layer보다 먼저 준비되는 dependency가 명확하다.
- local config로 동일한 pipeline boundary를 다시 실행할 수 있다.
- orchestration failure가 domain state를 임의로 조작하지 않는다.
- Reliability control-plane이 별도 boundary로 유지된다.

## Boundary

**Owns**

- Dagster asset/job dependency
- orchestration config adaptation
- local data-plane execution boundary

**Does not own**

- source parsing과 transformation business logic
- dbt model semantics와 artifact promotion policy
- incident detection과 Agentic reasoning
- approval, recovery와 reliability scheduling/control-plane

## Acceptance Evidence

- `src/project_pivot/orchestration/`
- `tests/orchestration/`

## References

- [MVP](README.md)
- [Orchestration Domain](../../domains/orchestration.md)
- [Architecture](../../ARCHITECTURE.md)
