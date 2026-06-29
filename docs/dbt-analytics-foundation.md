# dbt Analytics Foundation

## 실행

DuckDB raw 테이블을 먼저 적재한 뒤 dbt를 실행한다.

```bash
PROJECT_PIVOT_DUCKDB_PATH=data/project_pivot.duckdb \
DBT_PROFILES_DIR=dbt \
uv run dbt build --project-dir dbt
```

설정 확인:

```bash
PROJECT_PIVOT_DUCKDB_PATH=data/project_pivot.duckdb \
DBT_PROFILES_DIR=dbt \
uv run dbt debug --project-dir dbt
```

## 모델 계약

- `stg_hmda_loans`: HMDA 신청 연도, 지역, 대출 목적, action, 금액/소득 컬럼 정리
- `mart_hmda_loan_outcomes`: `activity_year`, `state_code`, `loan_purpose` grain

`mart_hmda_loan_outcomes.activity_year`는 후속 Dagster source year 기준 materialization 후보로 유지한다.

## Artifact

- `dbt/target/manifest.json`
- `dbt/target/run_results.json`

후속 profile, impact analysis, Dagster 도입 단계는 위 모델명과 artifact 경로를 기준으로 연결한다.
