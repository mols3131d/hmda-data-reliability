---
type: openspec-spec-driven-tdd-spec
category: spec
title: data-platform-duckdb-access
description: File-based DuckDB의 Project Pivot mutation API를 canonical database path별로 직렬화한다.
tags:
  - "domain:reliability"
  - "capability:data-platform-duckdb-access"
  - "schema-drift"
---

## ADDED Requirements

### Requirement: Local database mutation lock

시스템은 file-based DuckDB의 canonical resolved database path별 cooperative exclusive mutation lock을 제공해야 한다(SHALL). Project Pivot의 managed writer는 target state 확인과 first mutation 사이에 다른 managed writer가 끼어들지 못하도록 같은 lock을 사용해야 한다(SHALL). Lock I/O failure는 caller가 식별할 수 있는 typed Data Platform failure로 노출해야 하며(SHALL), lock release failure가 body의 원래 exception을 가려서는 안 된다(MUST NOT).

#### Scenario: Serialized file-database writers

- **GIVEN** 두 managed writer가 같은 physical DuckDB file을 변경하려 할 때
- **WHEN** 첫 writer가 mutation lock을 보유할 때
- **THEN** 두 번째 writer는 첫 writer의 mutation boundary가 성공 또는 실패로 종료되고 lock이 해제된 뒤에만 target state를 확인하고 mutation을 진행할 수 있어야 한다.

#### Scenario: Canonically equivalent database paths

- **GIVEN** relative, absolute 또는 symlink path가 canonical resolution 뒤 같은 DuckDB path를 식별할 때
- **WHEN** 두 managed writer가 mutation lock을 요청할 때
- **THEN** 두 요청은 같은 mutation lock을 사용해야 한다.

#### Scenario: In-memory database

- **WHEN** isolated in-memory DuckDB connection이 mutation boundary를 요청할 때
- **THEN** file lock을 생성하지 않고 해당 connection scope의 mutation을 진행할 수 있어야 한다.

#### Scenario: Lock acquisition failure

- **WHEN** file-based database의 mutation lock을 생성하거나 획득할 수 없을 때
- **THEN** target mutation 전에 typed Data Platform failure로 종료해야 한다.

#### Scenario: Body failure preservation

- **GIVEN** mutation body와 lock release가 모두 실패할 때
- **WHEN** lock context를 종료할 때
- **THEN** caller는 mutation body의 원래 failure를 관찰할 수 있어야 한다.
