## Purpose

Dagster project layout이 표준 definitions entrypoint와 현재 HMDA asset contract를 일관되게 노출하는 기준을 정의한다.

## Requirements

### Requirement: Dagster project root uses orchestration package

시스템은 `project_pivot.orchestration`을 Dagster project root module로 사용해야(SHALL) 합니다.

#### Scenario: Loading definitions through dg

- **WHEN** 사용자가 `env UV_CACHE_DIR=/tmp/uv-cache DAGSTER_HOME=/tmp/project-pivot-dagster-home PYTHONPATH=src uv run dg list defs --json` 명령어를 실행할 때
- **THEN** 시스템은 `project_pivot.orchestration.definitions`에서 Dagster definitions를 로드해야 합니다.
- **AND** `raw_hmda_loans`, `dbt_loan_analytics`, `incident_lifecycle`, `pipeline_job`을 표시해야 합니다.

### Requirement: Dagster definitions live under defs directory

시스템은 Dagster asset/resource 구현을 `src/project_pivot/orchestration/defs/` 하위에 배치해야(SHALL) 합니다.

#### Scenario: Inspecting project layout

- **WHEN** 개발자가 `src/project_pivot/orchestration/defs/` 폴더를 확인할 때
- **THEN** Dagster asset 정의와 resource 정의가 해당 폴더 하위 Python 모듈에 있어야 합니다.
- **AND** 이전 Dagster 중첩 패키지는 없어야 합니다.

### Requirement: Dagster entrypoint remains definitions module

시스템은 `project_pivot.orchestration.definitions` 모듈에서 `defs` 객체를 노출해야(SHALL) 합니다.

#### Scenario: Importing Dagster definitions

- **WHEN** 코드가 `from project_pivot.orchestration.definitions import defs`를 실행할 때
- **THEN** 시스템은 Dagster `Definitions` 객체를 반환해야 합니다.
- **AND** 해당 객체는 기존 asset, job, resource를 포함해야 합니다.

### Requirement: Existing asset behavior is preserved

시스템은 폴더 구조 변경 후에도 기존 Dagster asset behavior를 유지해야(SHALL) 합니다.

#### Scenario: Materializing pipeline

- **WHEN** 사용자가 `pipeline_job`을 실행할 때
- **THEN** 시스템은 `raw_hmda_loans`, `dbt_loan_analytics`, `incident_lifecycle` 순서로 실행해야 합니다.
- **AND** 각 asset의 group, dependency, materialization metadata는 유지되어야 합니다.
