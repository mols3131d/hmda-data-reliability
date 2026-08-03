# Silver

Bronze 데이터를 dbt staging model로 읽고 최소한의 변환과 품질 검증을 적용하는 단계다.

## 기준

- source contract와 staging 책임을 분리한다.
- 핵심 column과 타입을 test로 확인한다.
- raw 보존과 mart aggregation은 Silver의 책임이 아니다.

구현 위치: `dbt/models/staging/`  
검증 위치: `dbt/models/sources.yml`, `tests/dbt/`
