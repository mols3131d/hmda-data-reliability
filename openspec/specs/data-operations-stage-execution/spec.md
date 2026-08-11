# data-operations-stage-execution Specification

## Purpose

HMDA raw load와 dbt build를 orchestration과 분리된 application stage로 실행하고 caller가 처리할 수 있는 결과와 실패 경계를 제공하는 계약을 정의한다.

## Requirements

### Requirement: Independent stage execution

시스템은 raw load와 dbt build를 서로 독립적으로 호출할 수 있는 stage로 제공해야 한다(SHALL). 각 stage는 전체 pipeline 순서를 자체적으로 조율해서는 안 된다(MUST NOT). 시스템은 environment override를 해석한 공통 request를 제공해야 한다(SHALL).

#### Scenario: Direct stage call

- **WHEN** caller가 유효한 request로 하나의 stage를 호출할 때
- **THEN** 해당 stage의 결과만 반환되어야 한다.

#### Scenario: Stage isolation

- **WHEN** caller가 raw load 또는 dbt build stage 하나만 직접 호출할 때
- **THEN** 다른 pipeline stage가 암묵적으로 실행되어서는 안 된다.

#### Scenario: Environment-backed execution request

- **GIVEN** `PROJECT_PIVOT_DUCKDB_PATH` 또는 `PROJECT_PIVOT_SOURCE_ROOT`가 설정되어 있을 때
- **WHEN** caller가 환경 기반 Data Operations request를 생성할 때
- **THEN** request는 설정된 값을 database path와 source root에 사용해야 한다.

#### Scenario: Absent environment settings

- **GIVEN** 지원되는 pipeline environment key가 설정되지 않았을 때
- **WHEN** caller가 환경 기반 Data Operations request를 생성할 때
- **THEN** request는 기존 로컬 기본값을 사용해야 한다.

#### Scenario: Invalid source year setting

- **GIVEN** `PROJECT_PIVOT_SOURCE_YEAR`가 정수가 아닐 때
- **WHEN** caller가 환경 기반 Data Operations request를 생성할 때
- **THEN** 시스템은 invalid environment setting을 식별하는 validation error를 발생시켜야 한다.

### Requirement: Raw load delegation

Raw load stage는 HMDA source discovery와 ingestion behavior를 `hmda-data` domain에 위임하고 처리 파일 수와 적재 행 수를 결과로 제공해야 한다(SHALL).

#### Scenario: Successful raw load

- **WHEN** 유효한 HMDA load request를 실행할 때
- **THEN** stage는 configured target에 대한 ingestion을 호출하고 처리 범위와 row count를 반환해야 한다.

### Requirement: dbt build execution

시스템은 request의 dbt project와 profile 설정으로 build를 실행하고 성공한 현재 실행의 `manifest.json`과 `run_results.json`을 확인한 뒤에만 성공 결과를 반환해야 한다(SHALL).

#### Scenario: Successful dbt build

- **WHEN** dbt process가 정상 종료되고 현재 실행 artifact가 존재할 때
- **THEN** stage는 성공 상태와 두 artifact 위치를 반환해야 한다.

#### Scenario: Stale artifacts are not current success

- **WHEN** 이전 실행 artifact가 존재하지만 현재 dbt 실행이 새 필수 artifact를 제공하지 못할 때
- **THEN** stage는 이전 artifact만으로 현재 실행을 성공으로 보고해서는 안 된다.

### Requirement: dbt failure boundary

시스템은 process 시작 실패, timeout, non-zero exit 또는 필수 artifact 누락을 성공으로 보고해서는 안 된다(MUST NOT). 실패는 caller가 처리할 수 있는 data-operations domain error로 노출해야 한다(SHALL).

#### Scenario: Process or artifact failure

- **WHEN** dbt process가 실패하거나 필수 artifact를 제공하지 못할 때
- **THEN** stage는 실패 원인을 식별할 수 있는 domain failure로 종료해야 한다.
