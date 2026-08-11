# MVP Goal: Orchestration

## Goal

MVP reliability control-plane을 Dagster data plane에 암묵적으로 결합하지 않는다.

이번 MVP에서 Orchestration은 새 recovery workflow를 구현하는 domain이 아니라 **기존 실행 경계를 보존하는 domain**이다.

## MVP Boundary

- `pipeline_job`은 Bronze 적재와 dbt 분석만 실행한다.
- incident lifecycle, approval, recovery와 evaluation을 asset graph에 추가하지 않는다.
- MVP acceptance는 별도 reliability/data-operations API 경계에서 수행한다.

## Done When

- MVP 변경 뒤에도 Dagster graph가 reliability side effect를 자동 실행하지 않는다.
- MVP를 위해 schedule, sensor, approval UI 또는 control-plane asset을 추가하지 않는다.

## References

- [Orchestration Domain](../../domains/orchestration.md)
- [Architecture](../../ARCHITECTURE.md)
- [MVP Goal](../../mvp.md)
- `tests/orchestration/`
