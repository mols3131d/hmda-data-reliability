# MVP Goal: Orchestration

## Goal

MVP reliability control-plane을 Dagster data plane에 암묵적으로 결합하지 않는다.

이번 MVP에서 Orchestration은 새 recovery workflow를 구현하는 domain이 아니라 기존 실행 경계를 보존하는 domain이다.

## Outcomes

- `pipeline_job`은 Bronze 적재와 dbt 분석의 data plane에 머문다.
- incident lifecycle, approval, recovery와 evaluation이 Dagster graph에서 자동 실행되지 않는다.
- MVP acceptance는 별도 reliability/data-operations API 경계에서 수행할 수 있다.

## Non-Goals

- reliability schedule 또는 sensor
- approval UI
- control-plane asset 추가

## References

- [Orchestration Domain](../../domains/orchestration.md)
- [Architecture](../../ARCHITECTURE.md)
- [MVP](README.md)
- `tests/orchestration/`
