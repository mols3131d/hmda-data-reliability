# 구현 메모

## Source Discovery

- 원천 루트: `data/raw/hmda`
- 확인 파일:
  - `data/raw/hmda/year_2025.csv`
  - `data/raw/hmda/data_fields.html`
  - `data/raw/hmda/data_fields.md`
- 적재 대상 확장자: `.csv`, `.parquet`
- 현재 실제 원천 데이터: `year_2025.csv`
- 현재 문서/참고 파일: `data_fields.html`, `data_fields.md`
- 현재 원천 루트 크기: 약 4.8GB
- `year_2025.csv` 행 수: 13,543,606
- `year_2025.csv` 컬럼 수: 99
- `year_2025.csv` 주요 필수 컬럼:
  - `activity_year`
  - `loan_purpose`
  - `action_taken`
  - `loan_amount`
  - `income`
  - `state_code`
  - `county_code`

전체 컬럼 목록은 `data/raw/hmda/data_fields.md`와 원천 CSV `DESCRIBE` 결과를 기준으로 한다.

## Module Naming

- 구현 모듈명: `project_pivot.hmda_data`
- 이유: 원천 데이터와 공개 API가 HMDA 의미를 직접 드러내야 하며, `loan_data`보다 현재 변경 범위의 데이터 출처가 명확하다.

## Active Taxi/TLC References

교체 또는 제거 대상은 다음 영역이다.

- Python source:
  - `src/project_pivot/taxi_data/**`
  - `src/project_pivot/pipeline/**`
  - `src/project_pivot/orchestration/**`
  - `src/project_pivot/reliability/metadata/builder.py`
  - `src/project_pivot/reliability/profiling/profile_snapshot_builder.py`
  - `src/project_pivot/reliability/recovery/**`
  - `src/project_pivot/api/app.py`
- dbt:
  - `dbt/models/sources.yml`
  - `dbt/models/staging/stg_yellow_tripdata.sql`
  - `dbt/models/staging/stg_taxi_zones.sql`
  - `dbt/models/staging/schema.yml`
  - `dbt/models/marts/mart_daily_taxi_trips.sql`
  - `dbt/models/marts/schema.yml`
- Tests:
  - `tests/taxi_data/**`
  - `tests/dbt/test_analytics_foundation.py`
  - `tests/pipeline/**`
  - `tests/orchestration/test_dagster_definitions.py`
  - `tests/api/test_app.py`
  - 일부 `tests/reliability/**` fixture와 expected asset 이름
- Docs:
  - `README.md`
  - `docs/dbt-analytics-foundation.md`
  - `docs/backlogs/implement-taxi-data-foundation.md`
  - `docs/backlogs/implement-dbt-analytics-foundation.md`
  - `docs/backlogs/INDEX.csv`

보존 가능한 범위는 archive 성격의 과거 변경 문서뿐이다.
