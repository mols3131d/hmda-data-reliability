# 시작하기

## 데이터 준비

- 원천 경로: `data/raw/hmda`
- 지원 형식: CSV, Parquet
- 필수 컬럼: `activity_year`, `state_code`, `county_code`, `loan_purpose`, `action_taken`, `loan_amount`, `income`
- Raw table: `raw.hmda_loans`
- 추적 컬럼: `source_file`, `source_file_name`, `source_year`, `ingested_at`
- dbt models: `stg_hmda_loans`, `mart_hmda_loan_outcomes`

## 실행

Dagster UI:

```bash
PYTHONPATH=src uv run dagster dev -m project_pivot.orchestration.definitions
```

`pipeline_job`은 `raw_hmda_loans`, `dbt_loan_analytics` 순서로 실행한다. Lifecycle은 caller baseline을 받는 독립 Python API이며 Dagster graph에 포함되지 않는다.

Job 직접 실행:

```bash
PYTHONPATH=src uv run dagster job execute \
  -m project_pivot.orchestration.definitions \
  -a defs \
  -j pipeline_job
```

Definitions 확인:

```bash
PYTHONPATH=src uv run dg list defs --json
```

## 검증

```bash
uv run ruff check src tests
uv run mypy src tests
uv run pytest tests/hmda_data tests/dbt tests/data_operations tests/orchestration
```
