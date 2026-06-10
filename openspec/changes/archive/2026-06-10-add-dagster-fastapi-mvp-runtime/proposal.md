## Why

MVP 파이프라인은 단계별 로직은 있지만 사용자가 한 번에 실행하거나 Dagster/FastAPI 경계에서 호출할 수 있는 런타임이 없다. Dagster와 FastAPI를 추가해 로컬 오케스트레이션과 HTTP 실행 진입점을 제공한다.

## What Changes

- ingestion, dbt build, incident lifecycle을 묶는 공용 MVP pipeline runner를 추가한다.
- Dagster asset/job이 같은 runner 단계를 호출하도록 구성한다.
- FastAPI app에 health check와 pipeline 실행 endpoint를 추가한다.
- 실행 결과를 Pydantic response model로 반환한다.

## Capabilities

### New Capabilities

- `mvp-pipeline-runtime`: 로컬 MVP 파이프라인을 Dagster와 FastAPI에서 실행한다.

### Modified Capabilities

- 없음

## Impact

- `src/project_pivot/pipeline/` 모듈이 추가된다.
- `src/project_pivot/orchestration/` Dagster 모듈이 추가된다.
- `src/project_pivot/api/` FastAPI app이 추가된다.
- `fastapi` dependency가 추가된다.
