## Purpose

Dagster와 분리된 재사용 가능한 HMDA pipeline 단계의 입력, 결과와 핵심 실패 계약을 정의한다.

## Requirements

### Requirement: Reusable pipeline stage functions

시스템은 raw 적재, dbt build, incident lifecycle용 Dagster 비종속 Python stage를 제공해야 한다(SHALL).

#### Scenario: 단계 함수 직접 호출

- **WHEN** caller가 유효한 request로 pipeline stage를 호출할 때
- **THEN** stage는 해당 단계의 결과 contract를 반환해야 한다.
- **AND** 다른 단계의 실행 순서를 조율하지 않아야 한다.

### Requirement: dbt build stage execution

시스템은 request에 지정된 dbt project와 profile 설정으로 `dbt build`를 실행하고 성공한 실행만 dbt build 결과로 반환해야 한다(SHALL).

#### Scenario: Successful dbt build

- **WHEN** dbt process가 정상 종료되고 `manifest.json`과 `run_results.json`이 생성될 때
- **THEN** dbt stage는 성공 상태와 해당 artifact 경로를 포함한 결과를 반환해야 한다.

### Requirement: dbt build failure boundary

시스템은 dbt process 시작 실패, timeout, non-zero exit 또는 필수 artifact 누락을 성공으로 보고해서는 안 된다(MUST NOT). 이러한 실패는 caller가 처리할 수 있는 data-operations domain error로 노출해야 한다(SHALL).

#### Scenario: dbt process fails

- **WHEN** dbt process를 시작할 수 없거나 timeout 또는 non-zero exit가 발생할 때
- **THEN** dbt stage는 실패 원인을 식별할 수 있는 data-operations domain error를 반환해야 한다.

#### Scenario: Successful exit without artifacts

- **WHEN** dbt process가 zero exit로 종료되었지만 `manifest.json` 또는 `run_results.json`이 존재하지 않을 때
- **THEN** dbt stage는 성공 결과를 반환하지 않아야 한다.
- **AND** 누락된 artifact를 식별할 수 있는 data-operations domain error를 반환해야 한다.
