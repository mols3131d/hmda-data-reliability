# MVP Domain: Data Platform

## Mission

HMDA 데이터를 로컬에서 **저장·변환·검증할 수 있는 최소 analytical lake**를 제공한다.

Data Platform domain은 Project Pivot이 단순한 in-memory anomaly demo가 아니라 실제 데이터
상태와 transformation evidence를 가진 Data Lake 위에서 동작한다는 것을 증명한다.

## MVP Contribution

- DuckDB에 Bronze raw state를 안정적으로 보존한다.
- Bronze를 dbt staging과 mart로 변환할 최소 analytical layer를 제공한다.
- dbt run/result/manifest 등 downstream reliability가 사용할 execution evidence를 보존한다.
- candidate, failed run과 current last-known-good evidence를 구분할 수 있게 한다.
- artifact promotion 중 서로 다른 run의 evidence가 하나의 정상 current state처럼 보이지 않게 한다.

## Done When

같은 Bronze input에서 raw → staging → mart를 로컬에서 다시 만들 수 있고, 결과가 어떤
transformation과 dbt evidence에서 나왔는지 추적할 수 있다.

완료 판단은 model 수가 아니라 다음 proof로 한다.

- Bronze가 downstream transformation의 안정적인 source가 된다.
- staging/mart가 최소 분석 가능한 projection을 제공한다.
- candidate 또는 failed validation이 current evidence를 파괴하지 않는다.
- 채택된 artifact pair의 identity가 downstream Reliability까지 유지된다.

## Boundary

**Owns**

- DuckDB data/storage primitives
- dbt source, staging/mart와 data tests
- dbt artifact와 lineage projection
- current/candidate artifact identity primitives

**Does not own**

- 원천 파일 discovery와 parsing policy
- dbt subprocess의 실행 순서와 promotion decision
- incident 판단, Agentic review와 recovery policy
- Dagster orchestration policy

## Acceptance Evidence

- `dbt/`
- `src/project_pivot/data_platform/`
- `tests/data_platform/`
- `tests/dbt/`

## References

- [MVP](README.md)
- [Data Platform Domain](../../domains/data-platform.md)
