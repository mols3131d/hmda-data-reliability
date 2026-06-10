# Pipeline Walkthrough

## 현재 정의

이 프로젝트는 `local file-based lakehouse MVP`다.

원천 파일은 `data/raw/tlc` 아래 Parquet/CSV로 두고, DuckDB가 로컬 query engine과 warehouse 역할을 한다. dbt는 staging/mart 변환을 담당하고, reliability 모듈은 evidence, incident, impact, remediation, recovery, evaluation 흐름을 담당한다.

## 전체 흐름

```text
1. Ingestion
   raw 파일 -> DuckDB raw table

2. Transformation
   raw table -> dbt staging -> dbt mart

3. Evidence
   table metadata evidence
   profile snapshot
   dbt lineage evidence

4. Detection
   baseline profile vs current profile
   -> incident 생성

5. Impact
   dbt manifest 기준 downstream asset 계산

6. Remediation
   RCA summary
   test/backfill/validation action 제안

7. Recovery
   ApprovalStatus.APPROVED 확인
   -> partition overwrite backfill
   -> profile snapshot 재생성

8. Evaluation
   synthetic case 결과
   -> evaluation_report.md
```

## 코드 위치

| 단계 | 위치 |
|---|---|
| 적재 | `src/project_pivot/taxi_data/ingestion/` |
| 적재 CLI | `src/project_pivot/taxi_data/cli.py` |
| 통합 runner | `src/project_pivot/pipeline/` |
| Dagster 진입점 | `src/project_pivot/orchestration/dagster/` |
| FastAPI 진입점 | `src/project_pivot/api/app.py` |
| dbt staging | `dbt/models/staging/` |
| dbt mart | `dbt/models/marts/` |
| metadata evidence | `src/project_pivot/reliability/metadata/` |
| profile snapshot | `src/project_pivot/reliability/profiling/` |
| incident detection | `src/project_pivot/reliability/detection/` |
| impact analysis | `src/project_pivot/reliability/impact/` |
| remediation draft | `src/project_pivot/reliability/remediation/` |
| approval recovery | `src/project_pivot/reliability/recovery/` |
| evaluation report | `src/project_pivot/reliability/evaluation/` |

## 실행 방식

데이터 적재만 직접 확인할 때는 CLI를 사용한다.

```bash
env UV_CACHE_DIR=/tmp/uv-cache PYTHONPATH=src uv run python -m project_pivot.taxi_data.cli load-raw \
  --database data/project_pivot.duckdb \
  --source-root data/raw/tlc \
  --year 2024
```

dbt 변환은 dbt CLI로 실행한다.

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run dbt build --project-dir dbt --profiles-dir dbt
```

통합 runner는 raw load, 선택적 dbt build, incident lifecycle을 한 번에 실행한다.

```bash
env UV_CACHE_DIR=/tmp/uv-cache PYTHONPATH=src uv run python -c "from project_pivot.pipeline import MvpPipelineRunRequest, run_mvp_pipeline; result = run_mvp_pipeline(MvpPipelineRunRequest(run_dbt_build=False)); print(result.status)"
```

마리모 노트북에서는 같은 개념을 셀 단위로 분해해서 확인한다.

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run marimo edit notebooks/mvp_pipeline_playground.mo.py
```

FastAPI로는 같은 runner를 HTTP에서 호출한다.

```bash
env UV_CACHE_DIR=/tmp/uv-cache PYTHONPATH=src uv run uvicorn project_pivot.api.app:app --host 127.0.0.1 --port 8000
```

```bash
curl -X POST http://127.0.0.1:8000/pipeline/run \
  -H 'content-type: application/json' \
  -d '{"run_dbt_build": false}'
```

Dagster에서는 asset graph로 실행한다.

```bash
env UV_CACHE_DIR=/tmp/uv-cache PYTHONPATH=src uv run dagster dev -m project_pivot.orchestration.dagster.definitions
```

## 현재 한계

FastAPI 실행은 request-response 안에서 끝나는 동기식 MVP 경로다. 장시간 실행, 인증, async job queue, Dagster schedule/sensor는 아직 없다.
