## ADDED Requirements

### Requirement: Shared MVP pipeline runner

시스템은 ingestion, dbt build, incident lifecycle을 하나의 공용 runner로 실행해야 한다(SHALL).

#### Scenario: runner 실행

- **WHEN** 사용자가 MVP pipeline request를 전달할 때
- **THEN** 시스템은 raw load, dbt build, lifecycle summary를 포함한 Pydantic result를 반환해야 한다.

### Requirement: Dagster orchestration entrypoint

시스템은 MVP pipeline runner를 호출하는 Dagster asset/job을 제공해야 한다(SHALL).

#### Scenario: Dagster definitions 로딩

- **WHEN** Dagster definitions를 import할 때
- **THEN** raw, dbt, lifecycle asset과 MVP pipeline job이 제공되어야 한다.

### Requirement: FastAPI execution endpoint

시스템은 MVP pipeline runner를 호출하는 FastAPI endpoint를 제공해야 한다(SHALL).

#### Scenario: pipeline endpoint 호출

- **WHEN** 사용자가 `POST /pipeline/run`에 pipeline request를 보낼 때
- **THEN** API는 pipeline result를 JSON으로 반환해야 한다.

### Requirement: Health endpoint

시스템은 런타임 상태 확인용 health endpoint를 제공해야 한다(SHALL).

#### Scenario: health check

- **WHEN** 사용자가 `GET /health`를 호출할 때
- **THEN** API는 `{"status": "ok"}`를 반환해야 한다.
