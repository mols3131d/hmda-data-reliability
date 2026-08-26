# orchestration-pipeline Specification

## Purpose

Apache Airflow data-plane workflow가 HMDA Bronze raw load와 dbt analytics build를 연결하고, Data Operations 결과와 task/data-update evidence의 경계를 보존하는 orchestration 계약을 정의한다.

## Requirements

### Requirement: Data-plane workflow graph

시스템은 하나의 loadable data-plane workflow에서 raw load stage와 analytics build stage를 제공해야 한다(SHALL). Analytics stage는 raw load stage에 의존해야 한다(MUST).

#### Scenario: Workflow inspection

- **WHEN** active Airflow workflow definitions를 로드할 때
- **THEN** 정확히 하나의 full data-plane DAG와 raw load → analytics build 실행 경로를 식별할 수 있어야 함
- **AND** 별도의 active full-pipeline orchestrator가 없어야 함

### Requirement: Ordered stage execution

시스템은 raw load가 성공한 뒤 analytics stage를 실행해야 한다(SHALL). `run_dbt_build=true`인 경우 analytics stage는 성공한 dbt candidate를 promotion한 뒤에만 완료로 판정해야 한다(MUST).

#### Scenario: Successful ordered execution

- **WHEN** 유효한 request로 data-plane workflow를 실행하고 raw load와 dbt build가 성공할 때
- **THEN** raw load → dbt build → artifact promotion 순서가 관찰되어야 함
- **AND** current artifact projection은 검증된 candidate만 반영해야 함

#### Scenario: Raw stage failure

- **WHEN** raw load가 실패할 때
- **THEN** analytics stage는 실행되지 않아야 함
- **AND** workflow는 실패 상태를 관찰 가능하게 전달해야 함

#### Scenario: Analytics stage failure

- **WHEN** dbt build 또는 artifact promotion이 실패할 때
- **THEN** analytics stage는 실패해야 함
- **AND** artifact promotion 또는 current projection 성공으로 오인되어서는 안 됨

### Requirement: Execution and data update evidence

각 stage는 caller가 실행 결과와 데이터 update 여부를 구분할 수 있는 evidence를 제공해야 한다(SHALL).

#### Scenario: Raw stage evidence

- **WHEN** raw load stage가 성공할 때
- **THEN** `database_path`, `source_root`, `source_file_count`, `source_year`, `hmda_loans_row_count`를 확인할 수 있어야 함

#### Scenario: Analytics stage evidence

- **WHEN** analytics stage가 dbt build와 promotion까지 성공할 때
- **THEN** `return_code`, `manifest_path`, `run_results_path`, `projection_id`를 확인할 수 있어야 함
- **AND** task execution success와 analytics data update evidence는 별도로 식별할 수 있어야 함

#### Scenario: Failed or skipped analytics evidence

- **WHEN** analytics stage가 실패하거나 실행되지 않을 때
- **THEN** analytics data update evidence를 성공 update로 기록해서는 안 됨

### Requirement: Domain delegation

Orchestration은 source parsing, ingestion, analytics build, artifact promotion 또는 reliability business rule을 중복 구현하지 않고 Data Operations와 Reliability public boundary에 위임해야 한다(SHALL).

#### Scenario: Delegated workflow execution

- **WHEN** data-plane task가 domain 작업을 실행할 때
- **THEN** orchestration은 dependency, config conversion, task state와 execution evidence만 조율해야 함
- **AND** ingestion, dbt build, promotion 또는 reliability lifecycle 구현을 직접 포함해서는 안 됨

### Requirement: Runtime configuration boundary

Orchestration은 지원되는 runtime override를 최종 `DataOperationRequest`로 변환해야 하며(SHALL), 최종 request validation은 `DataOperationRequest`가 소유해야 한다(MUST).

#### Scenario: Configuration precedence and validation

- **WHEN** explicit override, supported environment value와 request default가 함께 존재할 때
- **THEN** precedence는 explicit override > environment > request default여야 함
- **AND** valid explicit value가 같은 field의 invalid environment value를 가릴 수 있어야 함
- **AND** invalid explicit value와 empty path 또는 empty `source_file`은 request validation error로 거부되어야 함

### Requirement: Single pipeline orchestration owner

시스템은 Airflow data-plane workflow가 전체 실행 순서를 유일하게 소유하게 해야 하며(SHALL), 다른 domain 또는 active vendor runtime이 별도의 full-pipeline coordinator를 공개해서는 안 된다(MUST NOT).

#### Scenario: Single full-pipeline execution surface

- **WHEN** active project runtime과 configuration에서 full-pipeline 실행 surface를 확인할 때
- **THEN** Airflow data-plane workflow만 raw-to-analytics 순서를 소유해야 함
- **AND** Dagster dependency, import, definitions, asset 또는 job configuration이 active surface에 남아서는 안 됨

### Requirement: Control-plane exclusion

Data-plane workflow는 read-only incident lifecycle, approval, recovery, evaluation 또는 LLMOps orchestration을 자동으로 포함하거나 실행해서는 안 된다(MUST NOT). Workflow는 schedule 없이 실행되고 automatic retry를 사용하지 않아야 한다(SHALL).

#### Scenario: Data-plane boundary and runtime policy

- **WHEN** data-plane workflow를 로드하거나 실행할 때
- **THEN** incident lifecycle, approval, recovery, evaluation과 LLMOps task가 실행되지 않아야 함
- **AND** schedule은 비활성화되고 automatic retry는 0이어야 함

### Requirement: Disabled analytics skip semantics

시스템은 `run_dbt_build=false`를 analytics stage의 명시적 skip으로 표현해야 한다(SHALL).

#### Scenario: dbt build disabled

- **WHEN** valid request의 `run_dbt_build`가 `false`일 때
- **THEN** raw load stage는 성공할 수 있어야 함
- **AND** analytics stage는 `SKIPPED` 상태여야 함
- **AND** analytics data update evidence가 없어야 함
- **AND** workflow run은 raw stage 성공을 보존하며 성공으로 완료할 수 있어야 함

### Requirement: Task data boundary

Task 간 실행 순서는 workflow dependency로 표현해야 하며(SHALL), domain request, result, DataFrame 또는 Arrow table을 task transport payload로 전달해서는 안 된다(MUST NOT).

#### Scenario: Non-transported domain results

- **WHEN** workflow task definitions를 검사할 때
- **THEN** `DataOperationRequest`, `RawLoadResult`, `DbtBuildResult`, DataFrame 또는 Arrow table이 task transport payload에 포함되어서는 안 됨
- **AND** raw → analytics 순서는 task dependency로 확인할 수 있어야 함
