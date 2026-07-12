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

- source: `raw.hmda_loans`
- staging: `stg_hmda_loans`
  - `activity_year`, `state_code`, `county_code`, `loan_purpose`, `action_taken`
  - `loan_amount`, `income`, `source_file`, `source_year`
- mart: `mart_hmda_loan_outcomes`
  - grain: `activity_year + state_code + loan_purpose`
  - 지표: `application_count`, `approval_count`, `denial_count`, `approval_rate`, `average_loan_amount`, `average_income`

`action_taken` 값 `1`, `2`는 승인 건수, `3`, `7`은 거절 건수에 포함한다. mart의 `mart_grain_key`에는 `not_null`, `unique` 테스트를 적용한다.

## Artifact

- `dbt/target/manifest.json`
- `dbt/target/run_results.json`

`dbt_loan_analytics` asset이 dbt build를 실행하고 artifact 경로를 materialization metadata에 기록한다. `incident_lifecycle`은 artifact를 lineage와 영향 분석 입력으로 사용한다.
