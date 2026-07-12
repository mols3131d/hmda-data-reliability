# pipeline-runtime Specification

## Purpose

로컬 HMDA pipeline을 Python runner와 Dagster에서 동일 계약으로 실행한다.

## Requirements

### Requirement: Shared pipeline runner

시스템은 ingestion, dbt build, incident lifecycle을 하나의 공용 runner로 실행해야 한다(SHALL).

#### Scenario: runner 실행

- **WHEN** 사용자가 HMDA pipeline request를 전달할 때
- **THEN** 시스템은 raw load, dbt build, lifecycle summary를 포함한 Pydantic result를 반환해야 한다.

### Requirement: Dagster orchestration entrypoint

시스템은 pipeline 실행 함수를 호출하는 Dagster asset/job을 제공해야 한다(SHALL).

#### Scenario: Dagster definitions 로딩

- **WHEN** Dagster definitions를 import할 때
- **THEN** `raw_hmda_loans`, `dbt_loan_analytics`, `incident_lifecycle` asset과 `pipeline_job`이 제공되어야 한다.
