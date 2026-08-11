---
type: openspec-spec-driven-tdd-spec
category: spec
title: data-operations-stage-execution
description: Candidate와 target dbt run의 artifact isolation, promotion과 failure evidence를 정의한다.
tags:
  - "domain:reliability"
  - "capability:data-operations-stage-execution"
  - "mvp"
  - "volume-drop"
---

## MODIFIED Requirements

### Requirement: dbt build execution

시스템은 request의 dbt project와 profile 설정으로 unique run directory에서 isolated run을 실행하고 성공한 현재 실행의 `manifest.json`과 `run_results.json`을 확인한 뒤에만 성공 결과를 반환해야 한다(SHALL). Candidate run은 current target database와 shared current artifact를 변경해서는 안 된다(MUST NOT). Target run은 성공하고 caller validation을 통과했으며 promotion 직전 projection identity가 재확인된 artifact만 current projection으로 승격해야 한다(SHALL).

#### Scenario: Successful target artifact promotion

- **WHEN** target dbt process와 caller validation이 성공하고 현재 run artifact가 존재할 때
- **THEN** 해당 artifact만 current projection으로 승격하고 성공 결과를 반환해야 한다.

#### Scenario: Candidate run isolation

- **WHEN** candidate dbt validation을 실행할 때
- **THEN** current target database와 shared current artifact는 실행 전 상태를 유지해야 한다.

#### Scenario: Stale artifacts are not current success

- **WHEN** 이전 실행 artifact가 존재하지만 현재 dbt 실행이 새 필수 artifact를 제공하지 못할 때
- **THEN** stage는 이전 artifact만으로 현재 실행을 성공으로 보고해서는 안 된다.

#### Scenario: Earlier verified run promotion

- **GIVEN** run A가 검증된 뒤 run B가 완료되었을 때
- **WHEN** caller가 run A를 current projection으로 승격할 때
- **THEN** run A의 artifact bytes만 승격해야 한다.

#### Scenario: Changed verified artifact

- **GIVEN** 검증된 run artifact가 promotion 전에 변경되었을 때
- **WHEN** caller가 해당 run을 승격할 때
- **THEN** current projection을 변경하지 않고 promotion을 거부해야 한다.

#### Scenario: Concurrent promotion

- **GIVEN** 둘 이상의 verified run이 같은 current projection으로 승격을 요청할 때
- **WHEN** promotion을 실행할 때
- **THEN** current artifact pair는 하나의 verified run에 속하는 manifest와 run-results로만 구성되어야 한다.

#### Scenario: Locked projection read

- **WHEN** current artifact pair를 사용하는 impact 또는 projection identity를 읽을 때
- **THEN** promotion과 같은 local lock protocol으로 complete artifact pair만 읽어야 한다.

#### Scenario: Artifact mutation while waiting

- **GIVEN** promotion이 current projection lock을 기다리는 동안 verified run artifact가 변경되었을 때
- **WHEN** promotion lock을 획득할 때
- **THEN** 변경된 artifact를 current projection으로 승격하지 않고 promotion을 거부해야 한다.

### Requirement: dbt failure boundary

시스템은 process 시작 실패, timeout, non-zero exit, 필수 artifact 누락 또는 caller validation 실패를 성공으로 보고해서는 안 된다(MUST NOT). 실패는 command, result 또는 error와 해당 run artifact를 식별할 수 있는 data-operations domain error로 노출해야 하며 prior last-known-good artifact를 제거하거나 current success로 교체해서는 안 된다(SHALL).

#### Scenario: Process or artifact failure

- **WHEN** dbt process가 실패하거나 필수 artifact를 제공하지 못할 때
- **THEN** stage는 실패 원인과 failed-run evidence를 식별할 수 있는 domain failure로 종료해야 한다.

#### Scenario: Artifact projection read failure

- **WHEN** dbt build 결과 또는 promotion 대상의 artifact bytes를 읽지 못할 때
- **THEN** public Data Operations boundary는 run target과 실패한 artifact를 식별할 수 있는 domain failure로 종료해야 한다.
- **AND** raw filesystem exception을 외부 caller에 노출하거나 current projection을 변경해서는 안 된다.

#### Scenario: Candidate dbt failure

- **WHEN** candidate dbt process 또는 artifact validation이 실패할 때
- **THEN** current target과 shared current artifact는 변하지 않고 failed-run evidence가 식별 가능해야 한다.

#### Scenario: Recovery dbt failure

- **GIVEN** prior last-known-good target artifact가 있을 때
- **WHEN** recovery target dbt run이 실패할 때
- **THEN** prior artifact를 유지하고 failed-run evidence를 별도로 제공해야 한다.

#### Scenario: Backup cleanup failure

- **GIVEN** artifact pair가 current projection으로 성공적으로 교체되었을 때
- **WHEN** 이전 artifact backup의 cleanup이 실패할 때
- **THEN** committed current artifact pair를 rollback하거나 손상시켜서는 안 된다.

## ADDED Requirements

### Requirement: Artifact projection identity

시스템은 impact, approval과 recovery evidence가 판단에 사용한 dbt artifact projection을 식별할 수 있게 해야 한다(SHALL).

#### Scenario: Evidence projection reference

- **WHEN** dbt artifact를 사용한 impact, approval 또는 recovery evidence를 생성할 때
- **THEN** evidence는 사용한 artifact projection identity를 포함해야 한다.
