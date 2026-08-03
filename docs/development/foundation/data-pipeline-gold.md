# Gold

Silver 데이터를 downstream 분석이 사용하는 mart로 집계하는 단계다.

## 기준

- mart별 grain과 grouping을 먼저 정한다.
- 핵심 metric과 approval/denial 집계를 임의로 바꾸지 않는다.
- downstream 영향 분석이 사용할 asset과 grain을 보존한다.
- incident lifecycle과 recovery는 Gold가 실행하지 않는다.

구현 위치: `dbt/models/marts/`  
검증 위치: `tests/dbt/`, `dbt/target/manifest.json`
