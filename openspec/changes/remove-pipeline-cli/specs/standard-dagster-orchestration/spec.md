## ADDED Requirements

### Requirement: Single pipeline orchestration owner

시스템은 Dagster asset graph만 전체 HMDA pipeline의 실행 순서를 소유하도록 해야 한다(SHALL).

#### Scenario: 전체 pipeline 실행

- **WHEN** 사용자가 전체 HMDA pipeline을 실행할 때
- **THEN** Dagster asset dependency가 단계 순서를 결정해야 한다.
- **AND** `pipeline_job`은 해당 graph의 named 실행 경로로 제공되어야 한다.

#### Scenario: 중복 조율 API 부재

- **WHEN** `project_pivot.data_operations`의 공개 API를 확인할 때
- **THEN** `run_pipeline`, `PipelineRunResult`, 독립 pipeline CLI가 없어야 한다.
