# project-pivot

project-pivot은 로컬 파일 기반 lakehouse MVP다. DuckDB raw 적재, dbt 변환, reliability incident lifecycle을 하나의 로컬 파이프라인으로 검증한다.

## 실행 진입점

### CLI

```bash
uv run python scripts/run_mvp_pipeline.py \
  --output scratch/evaluation/pipeline_run_result.json
```

dbt까지 실행하려면 `--run-dbt-build`를 추가한다.

### FastAPI

```bash
PYTHONPATH=src uv run uvicorn project_pivot.api.app:app --host 127.0.0.1 --port 8000
```

```bash
curl -X POST http://127.0.0.1:8000/pipeline/run \
  -H 'content-type: application/json' \
  -d '{"run_dbt_build": false}'
```

### Dagster

```bash
PYTHONPATH=src uv run dagster dev -m project_pivot.orchestration.dagster.definitions
```

Dagster job 이름은 `mvp_pipeline_job`이고 asset 순서는 `raw_taxi_data -> dbt_analytics -> mvp_incident_lifecycle`이다.

## 검증

```bash
uv run ruff check src tests
uv run mypy src tests
uv run pytest tests/pipeline tests/api tests/orchestration
```
