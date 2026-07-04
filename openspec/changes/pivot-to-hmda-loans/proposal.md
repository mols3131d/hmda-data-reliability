## Why

프로젝트의 기본 분석 방향을 택시 운행 분석에서 대출 리스크와 승인 의사결정 데이터 제품으로 전환한다. `data/raw/hmda`를 기준 원천으로 삼아 HMDA 대출 데이터 적재, 변환, 오케스트레이션 계약을 먼저 고정해야 구현 중 도메인 명칭과 요구사항이 흔들리지 않는다.

## What Changes

- **BREAKING**: TLC/NYC Taxi 원천 데이터(`data/raw/tlc`)와 `taxi_data` 도메인을 기본 데이터 소스로 사용하지 않는다.
- HMDA 원천 파일을 DuckDB raw 레이어로 적재하는 데이터 파운데이션을 추가한다.
- 파티션 인제스션 기준을 택시 픽업 일자에서 HMDA 기준 연도/파일 단위로 전환한다.
- dbt source, staging, mart 모델을 HMDA 대출 분석에 맞게 재정의한다.
- Dagster asset 이름과 metadata를 HMDA Bronze, Silver/Gold, Control 흐름에 맞게 변경한다.
- 문서, 테스트, CLI 명칭에서 TLC/Taxi 중심 표현을 HMDA/Loan 중심 표현으로 정리한다.

## Capabilities

### New Capabilities

- `hmda-data-foundation`: `data/raw/hmda` 원천 파일을 로컬 DuckDB raw 레이어에 안정적으로 적재하고 검증하는 계약을 정의한다.

### Modified Capabilities

- `partition-ingestion`: 파티션 키와 멱등 적재 기준을 택시 일자 파티션에서 HMDA 연도/파일 파티션으로 전환한다.
- `dbt-analytics-foundation`: raw taxi source, staging, mart 요구사항을 HMDA loan source, staging, mart 요구사항으로 전환한다.
- `standard-dagster-orchestration`: Dagster asset key, asset metadata, materialization 순서를 HMDA 대출 데이터 흐름에 맞게 전환한다.

## Impact

- Affected code: `src/project_pivot/taxi_data`, `src/project_pivot/pipeline`, `src/project_pivot/orchestration`, `dbt/models`, `tests/taxi_data`, `tests/dbt`, `tests/orchestration`
- Affected data paths: replace `data/raw/tlc` with `data/raw/hmda`
- Affected dbt assets: taxi staging/mart models will be replaced by HMDA loan staging/mart models
- Affected Dagster assets: `raw_taxi_data` and taxi-oriented metadata will be renamed or replaced with HMDA loan-oriented assets
- Affected docs: README, architecture, vision, and backlog references should describe the HMDA loan data product direction
