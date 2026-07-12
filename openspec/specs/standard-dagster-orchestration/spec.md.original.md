## Purpose

표준 Dagster 실행 경로에서 HMDA 기반 MVP pipeline asset을 로드하고, Bronze/Silver/Gold/Control 책임과 실행 순서를 명확히 표현하는 orchestration 동작을 정의한다.

## Requirements

### Requirement: Standard Dagster dev execution

시스템은 `dagster-webserver`가 설치된 환경에서 표준 모듈 경로로 Dagster 웹 서버를 기동할 수 있어야(SHALL) 합니다.

#### Scenario: Running Dagster dev server

- **WHEN** 사용자가 `PYTHONPATH=src uv run dagster dev -m project_pivot.orchestration.definitions` 명령어를 실행할 때
- **THEN** 시스템은 로컬 Dagster 웹 UI를 기동해야 합니다.
- **AND** `raw_hmda_loans`, `dbt_loan_analytics`, `mvp_incident_lifecycle` asset과 `mvp_pipeline_job`을 로드해야 합니다.

### Requirement: Medallion-aligned Dagster assets

시스템은 Dagster asset을 Bronze, Silver/Gold, Control 책임에 맞게 표현해야(SHALL) 합니다.

#### Scenario: Inspecting assets in Dagster UI

- **WHEN** 사용자가 Dagster UI에서 asset graph를 확인할 때
- **THEN** `raw_hmda_loans`는 Bronze 적재 asset으로 표시되어야 합니다.
- **AND** `dbt_loan_analytics`는 Silver/Gold dbt build asset으로 표시되어야 합니다.
- **AND** `mvp_incident_lifecycle`는 Control plane incident lifecycle asset으로 표시되어야 합니다.

### Requirement: Ordered MVP materialization

시스템은 사용자가 Dagster UI 또는 CLI에서 MVP pipeline을 materialize할 때 지정된 의존성 순서대로 실행해야(SHALL) 합니다.

#### Scenario: Materializing the MVP pipeline

- **WHEN** 사용자가 `mvp_pipeline_job`을 실행할 때
- **THEN** 시스템은 `raw_hmda_loans`, `dbt_loan_analytics`, `mvp_incident_lifecycle` 순서로 실행해야 합니다.
- **AND** raw DuckDB 적재, dbt build, reliability lifecycle을 에러 없이 차례로 호출해야 합니다.

### Requirement: Asset metadata visibility

시스템은 materialization 결과를 Dagster UI에서 확인할 수 있도록 핵심 metadata를 기록해야(SHALL) 합니다.

#### Scenario: Reviewing materialization metadata

- **WHEN** `raw_hmda_loans` asset materialization이 완료될 때
- **THEN** source file count, source year, 적재 row count metadata가 기록되어야 합니다.
- **WHEN** `dbt_loan_analytics` asset materialization이 완료될 때
- **THEN** dbt 실행 상태와 artifact path metadata가 기록되어야 합니다.
- **WHEN** `mvp_incident_lifecycle` asset materialization이 완료될 때
- **THEN** detected incident types, affected assets, evaluation report path metadata가 기록되어야 합니다.

### Requirement: Domain logic boundary

시스템은 Dagster asset 내부에 적재, dbt 실행, incident lifecycle의 핵심 비즈니스 로직을 중복 구현하지 않아야(SHALL) 합니다.

#### Scenario: Maintaining orchestration boundaries

- **WHEN** Dagster asset이 실행될 때
- **THEN** asset은 `project_pivot.pipeline` 또는 `project_pivot.reliability`의 기존 실행 함수를 호출해야 합니다.
- **AND** asset은 Dagster 의존성, config, logging, metadata 기록만 담당해야 합니다.
