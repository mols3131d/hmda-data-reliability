# Orchestration

파이프라인의 실행 순서만 정한다. business rule과 approval은 소유하지 않는다.

## 기준

- Bronze 적재 뒤 dbt 분석을 실행한다.
- 각 asset은 input, output, partition을 분명히 한다.
- Dagster는 data plane 실행만 담당하며 schedule, sensor, asset check를 Foundation 완료 조건으로 요구하지 않는다.
- reliability lifecycle을 pipeline에 자동으로 묶지 않는다.
- recovery와 evaluation은 별도 실행으로 둔다.

구현 위치: `src/project_pivot/orchestration/`  
검증 위치: `tests/orchestration/`
