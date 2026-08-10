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

시스템은 request의 dbt project와 profile 설정으로 isolated run을 실행하고 성공한 현재 실행의 `manifest.json`과 `run_results.json`을 확인한 뒤에만 성공 결과를 반환해야 한다(SHALL). Candidate run은 current target database와 shared current artifact를 변경해서는 안 된다(MUST NOT). Target run은 성공하고 caller validation을 통과한 artifact만 current projection으로 승격해야 한다(SHALL).

#### Scenario: Successful target artifact promotion

- **WHEN** target dbt process와 caller validation이 성공하고 현재 run artifact가 존재할 때
- **THEN** 해당 validated run의 artifact만 current projection으로 승격하고 성공 결과를 반환해야 한다.

#### Scenario: Candidate run isolation

- **WHEN** candidate dbt validation을 실행할 때
- **THEN** current target database와 shared current artifact는 실행 전 상태를 유지해야 한다.

#### Scenario: Stale artifacts are not current success

- **WHEN** 이전 실행 artifact가 존재하지만 현재 dbt 실행이 새 필수 artifact를 제공하지 못할 때
- **THEN** stage는 이전 artifact만으로 현재 실행을 성공으로 보고해서는 안 된다.

### Requirement: dbt failure boundary

시스템은 process 시작 실패, timeout, non-zero exit, 필수 artifact 누락 또는 caller validation 실패를 성공으로 보고해서는 안 된다(MUST NOT). 실패는 command, result 또는 error와 해당 run artifact를 식별할 수 있는 data-operations domain error로 노출해야 하며 prior last-known-good artifact를 제거하거나 current success로 교체해서는 안 된다(SHALL).

#### Scenario: Process or artifact failure

- **WHEN** dbt process가 실패하거나 필수 artifact를 제공하지 못할 때
- **THEN** stage는 실패 원인과 failed-run evidence를 식별할 수 있는 domain failure로 종료해야 한다.

#### Scenario: Candidate dbt failure

- **WHEN** candidate dbt process 또는 artifact validation이 실패할 때
- **THEN** current target과 shared current artifact는 변하지 않고 failed-run evidence가 식별 가능해야 한다.

#### Scenario: Recovery dbt failure

- **GIVEN** prior last-known-good target artifact가 있을 때
- **WHEN** recovery target dbt run이 실패할 때
- **THEN** prior artifact를 유지하고 failed-run evidence를 별도로 제공해야 한다.

## ADDED Requirements

### Requirement: Safe run workspace

시스템은 각 dbt run을 trusted run root 아래의 독립된 run directory에서 실행해야 한다(SHALL). dbt CLI에 전달하는 target path와 runner가 artifact를 준비·검사하는 path는 같은 canonical directory를 가리켜야 한다(SHALL). Project directory, profiles directory, current projection, run root 자체 또는 trusted run root 밖의 path를 cleanup 대상으로 허용해서는 안 된다(MUST NOT).

#### Scenario: Canonical target resolution

- **WHEN** 기본 request로 dbt run을 실행할 때
- **THEN** dbt process가 artifact를 생성하는 target directory와 runner가 검사하는 directory가 같아야 한다.

#### Scenario: Independent run directory

- **WHEN** 둘 이상의 dbt run을 순차 또는 독립적으로 실행할 때
- **THEN** 각 run은 다른 run directory를 사용하고 이전 failed-run evidence를 시작 시점에 삭제해서는 안 된다.

#### Scenario: Dangerous cleanup path

- **WHEN** caller 입력이 project, profiles, current projection, run root 또는 trusted run root 밖의 existing directory를 cleanup 대상으로 만들 수 있을 때
- **THEN** dbt process 시작 전에 요청을 거부하고 해당 directory를 변경해서는 안 된다.

### Requirement: Artifact promotion binding

시스템은 current projection으로 승격할 artifact를 validated dbt run과 그 run을 생성한 request에 결합해야 한다(SHALL). Validation 이후 source artifact bytes 또는 run/request identity가 달라졌으면 기존 validation으로 승격해서는 안 된다(MUST NOT).

#### Scenario: Cross-run promotion rejection

- **GIVEN** successful result와 서로 다른 run 또는 target request가 주어졌을 때
- **WHEN** artifact promotion을 요청할 때
- **THEN** current projection을 변경하지 않고 promotion을 거부해야 한다.

#### Scenario: Artifact changed after validation

- **GIVEN** successful validation 이후 run artifact bytes가 변경되었을 때
- **WHEN** 같은 result로 promotion을 요청할 때
- **THEN** projection identity mismatch로 거부하고 prior current projection을 유지해야 한다.

### Requirement: Projection-consistent publication and evidence

시스템은 `manifest.json`과 `run_results.json`을 하나의 projection으로 취급해야 하며 current consumer가 서로 다른 run의 mixed pair를 관찰하게 해서는 안 된다(MUST NOT). Evidence의 projection identity는 판단에 실제 사용한 immutable artifact bytes와 같아야 한다(SHALL). 새 projection 설치가 완료된 뒤 cleanup 실패만으로 이미 설치된 current projection과 prior last-known-good를 동시에 손상해서는 안 된다(MUST NOT).

#### Scenario: Consistent current projection

- **WHEN** current artifact promotion과 lifecycle evidence read가 겹칠 수 있을 때
- **THEN** consumer는 old 또는 new projection 하나만 관찰하고 mixed pair를 evidence로 사용해서는 안 된다.

#### Scenario: Post-commit cleanup failure

- **GIVEN** 새 current projection 설치가 완료되었을 때
- **WHEN** obsolete backup cleanup이 실패할 때
- **THEN** 설치된 current projection을 삭제하는 rollback을 수행해서는 안 되고 recoverable cleanup failure로 남겨야 한다.

### Requirement: Artifact projection identity

시스템은 impact, approval과 recovery evidence가 판단에 사용한 dbt artifact projection을 식별할 수 있게 해야 한다(SHALL).

#### Scenario: Evidence projection reference

- **WHEN** dbt artifact를 사용한 impact, approval 또는 recovery evidence를 생성할 때
- **THEN** evidence는 사용한 exact artifact projection identity를 포함해야 한다.
