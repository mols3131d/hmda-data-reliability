## Context

현재 실행 흐름은 CLI raw load, dbt CLI, Python reliability 모듈, 노트북으로 나뉘어 있다. 새 런타임은 이 단계를 하나의 공용 service API로 묶고, Dagster/FastAPI는 얇은 adapter로 둔다.

## Goals / Non-Goals

**Goals:**

- `run_mvp_pipeline()` 함수로 로컬 파이프라인을 실행한다.
- Dagster asset/job에서 ingestion -> dbt -> lifecycle 순서로 실행 가능하게 한다.
- FastAPI `POST /pipeline/run` endpoint로 동일 파이프라인을 실행한다.
- 결과는 Pydantic model로 직렬화한다.

**Non-Goals:**

- production API authentication
- remote executor / daemon deployment
- Dagster schedule/sensor
- 비동기 job queue
- cloud object storage 연동

## Decisions

### Core runner를 먼저 둔다

Dagster와 FastAPI가 각각 실행 로직을 소유하면 경계마다 결과가 달라진다. 공용 runner가 유일한 실행 계약을 가진다.

### FastAPI endpoint는 request-response 실행으로 둔다

MVP에서는 로컬 소규모 실행 확인이 목적이다. 핸들러는 async로 선언하되 pipeline runner는 요청 안에서 직접 호출한다. 긴 실행/비동기 큐는 후속 작업으로 둔다.

### Dagster는 asset 3단계로 구성한다

`raw_taxi_data`, `dbt_analytics`, `mvp_incident_lifecycle` asset을 둬 실행 순서와 단계별 결과를 확인한다.

## Risks / Trade-offs

- [Risk] FastAPI 요청이 실행 중 block된다. -> MVP에서는 단순성을 우선한다.
- [Risk] dbt build가 외부 process라 테스트 비용이 크다. -> unit test는 `run_dbt_build=False`와 fixture artifact로 runner contract를 검증한다.
