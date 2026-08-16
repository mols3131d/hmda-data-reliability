# MVP Domain Milestone: Orchestration

## Goal

최소 Data Lake data plane을 Dagster asset graph로 로컬에서 실행하되 Reliability
control-plane과 approval을 자동으로 결합하지 않는다.

## Outcomes

- HMDA Bronze ingestion과 dbt analytics가 명시적인 asset dependency로 표현된다.
- local config로 target database와 source scope를 전달할 수 있다.
- 같은 data plane을 개발 환경에서 재실행하고 실패 위치를 식별할 수 있다.
- Reliability lifecycle, LLM review, approval과 recovery는 Dagster graph 밖의 명시적
  control-plane 경계를 유지한다.

## Done When

Dagster에서 Bronze → dbt analytics의 최소 graph를 로컬로 실행할 수 있고,
Reliability/Agentic 경계를 암묵적으로 자동 실행하지 않음을 검증하면 완료한다.

## Non-Goals

- cloud Dagster deployment
- reliability schedule, sensor 또는 automatic recovery
- approval UI와 long-running human-in-the-loop orchestration
- domain business logic을 asset 내부로 이동

## References

- [Orchestration Domain](../../domains/orchestration.md)
- [Architecture](../../ARCHITECTURE.md)
- [MVP](README.md)
- `tests/orchestration/`
