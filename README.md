# project-pivot

project-pivot은 HMDA 공개 대출 신청 데이터를 DuckDB에 적재하고, dbt 분석 모델과 데이터 신뢰성 incident lifecycle을 로컬에서 검증하는 파이프라인이다.

## 데이터 계약

- 원천 경로: `data/raw/hmda`
- 지원 형식: CSV, Parquet
- 필수 원천 컬럼: `activity_year`, `state_code`, `county_code`, `loan_purpose`, `action_taken`, `loan_amount`, `income`
- raw 테이블: `raw.hmda_loans`
- 추적 컬럼: `source_file`, `source_file_name`, `source_year`, `ingested_at`
- dbt 모델: `stg_hmda_loans`, `mart_hmda_loan_outcomes`

## 실행 진입점

### Dagster UI

```bash
PYTHONPATH=src uv run dagster dev -m project_pivot.orchestration.definitions
```

Dagster job 이름은 `pipeline_job`이고 asset 순서는 `raw_hmda_loans -> dbt_loan_analytics -> incident_lifecycle`이다.

직접 실행:

```bash
PYTHONPATH=src uv run dagster job execute \
  -m project_pivot.orchestration.definitions \
  -a defs \
  -j pipeline_job
```

정의 확인:

```bash
PYTHONPATH=src uv run dg list defs --json
```

## 검증

```bash
uv run ruff check src tests
uv run mypy src tests
uv run pytest tests/hmda_data tests/dbt tests/data_operations tests/orchestration
```
