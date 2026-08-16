---
type: openspec-spec-driven-tdd-spec
category: spec
title: data-operations-stage-execution
description: dbt build가 raw ingestion 및 reliability recovery와 같은 DuckDB mutation lock에 참여하도록 실행 경계를 보강한다.
tags:
  - "domain:reliability"
  - "capability:data-operations-stage-execution"
  - "schema-drift"
---

## ADDED Requirements

### Requirement: Serialized dbt database mutation

시스템은 file-based target DuckDB에서 dbt build subprocess를 시작하기 전에 공통 database mutation lock을 획득하고 subprocess 종료까지 유지해야 한다(SHALL). Lock을 획득할 수 없으면 dbt process를 시작해서는 안 되며(MUST NOT), caller가 식별할 수 있는 Data Operations failure로 종료해야 한다(SHALL).

#### Scenario: Recovery holds database mutation lock

- **GIVEN** approved recovery가 target DuckDB mutation lock을 보유할 때
- **WHEN** 같은 target에 dbt build stage를 요청할 때
- **THEN** dbt process는 recovery가 commit 또는 rollback하고 lock을 해제한 뒤에만 시작할 수 있어야 한다.

#### Scenario: dbt build holds database mutation lock

- **GIVEN** dbt build subprocess가 target DuckDB mutation lock 안에서 실행 중일 때
- **WHEN** HMDA ingestion 또는 recovery가 같은 target을 변경하려 할 때
- **THEN** 해당 mutation은 dbt process 종료와 lock release 뒤에 target state를 확인해야 한다.

#### Scenario: dbt mutation lock failure

- **WHEN** target DuckDB mutation lock을 준비하거나 획득할 수 없을 때
- **THEN** dbt process 시작 전에 Data Operations failure로 종료해야 한다.
