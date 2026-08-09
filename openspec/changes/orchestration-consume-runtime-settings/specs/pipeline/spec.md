---
type: openspec-spec-driven-tdd-spec
category: spec
title: pipeline
description: Dagster pipeline resource가 canonical Data Operations runtime settings를 소비하도록 변경한다.
tags:
  - "domain:orchestration"
  - "capability:pipeline"
  - "configuration"
---

## MODIFIED Requirements

### Requirement: Configured pipeline execution

시스템은 pipeline graph의 Dagster resource 설정을 Data Operations request로 변환해야 한다(SHALL). 기본 resource는 environment에서 해석된 Data Operations runtime settings를 사용해야 한다(SHALL). 명시적인 Dagster resource field는 해당 runtime setting을 override해야 한다(SHALL).

#### Scenario: Environment-backed default resource

- **GIVEN** pipeline environment override가 설정되어 있을 때
- **WHEN** 기본 `DataOperationsResource`가 request를 생성할 때
- **THEN** request는 canonical Data Operations runtime settings를 사용해야 한다.

#### Scenario: Explicit Dagster override

- **GIVEN** environment override와 명시적인 Dagster resource field가 함께 주어졌을 때
- **WHEN** resource가 request를 생성할 때
- **THEN** 명시적인 Dagster field가 같은 request field를 override해야 한다.

#### Scenario: Explicit override of invalid environment setting

- **GIVEN** 같은 field에 invalid environment value와 유효한 명시 Dagster resource field가 함께 주어졌을 때
- **WHEN** resource가 request를 생성할 때
- **THEN** 명시 Dagster field가 우선 적용되고 다른 environment setting은 계속 검증되어야 한다.
