---
type: openspec-spec-driven-tdd-spec
category: spec
title: stage-execution
description: Data Operations가 환경 설정을 일관된 실행 request로 해석하도록 변경한다.
tags:
  - "domain:data-operations"
  - "capability:stage-execution"
  - "configuration"
---

## MODIFIED Requirements

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
