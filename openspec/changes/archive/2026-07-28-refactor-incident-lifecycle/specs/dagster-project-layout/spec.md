## MODIFIED Requirements

### Requirement: Dagster project root uses orchestration package

시스템은 `project_pivot.orchestration`을 Dagster project root module로 사용해야(SHALL) 합니다.

#### Scenario: Loading definitions through dg

- **WHEN** 사용자가 `env UV_CACHE_DIR=/tmp/uv-cache DAGSTER_HOME=/tmp/project-pivot-dagster-home PYTHONPATH=src uv run dg list defs --json` 명령어를 실행할 때
- **THEN** 시스템은 `project_pivot.orchestration.definitions`에서 Dagster definitions를 로드해야 합니다.
- **AND** `raw_hmda_loans`, `dbt_loan_analytics`, `pipeline_job`을 표시해야 합니다.

### Requirement: Dagster entrypoint remains definitions module

시스템은 `project_pivot.orchestration.definitions` 모듈에서 `defs` 객체를 노출해야(SHALL) 합니다.

#### Scenario: Importing Dagster definitions

- **WHEN** 코드가 `from project_pivot.orchestration.definitions import defs`를 실행할 때
- **THEN** 시스템은 Dagster `Definitions` 객체를 반환해야 합니다.
- **AND** 해당 객체는 `raw_hmda_loans`, `dbt_loan_analytics`, `pipeline_job`, data operations resource를 포함해야 합니다.

### Requirement: Existing asset behavior is preserved

시스템은 data-plane Dagster asset의 기존 group, dependency, materialization behavior를 유지해야(SHALL) 합니다.

#### Scenario: Materializing pipeline

- **WHEN** 사용자가 `pipeline_job`을 실행할 때
- **THEN** 시스템은 `raw_hmda_loans`, `dbt_loan_analytics` 순서로 실행해야 합니다.
- **AND** 두 asset의 group, dependency, materialization metadata는 유지되어야 합니다.
- **AND** `incident_lifecycle` asset은 definitions에 포함되지 않아야 합니다.
