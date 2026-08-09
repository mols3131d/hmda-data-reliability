---
type: openspec-spec-driven-tdd-design
category: design
title: Data Operations Runtime Settings Centralization
description: Data Operations request module에 environment 해석 경계를 추가한다.
tags:
  - "domain:data-operations"
  - "capability:stage-execution"
  - "configuration"
---

> [!NOTE]
> `DataOperationRequest`의 기존 literal default와 검증을 보존하고, 같은 module의 factory가 지원되는 environment key만 request override로 변환한다. 실행 stage와 dbt subprocess는 변경하지 않는다.

## Context

- **Current State:** request가 모든 execution default를 갖지만 `.env.example`의 pipeline key는 request로 해석되지 않는다.
- **Constraints:** 직접 `DataOperationRequest`를 생성하는 caller의 동작을 변경하지 않으며, orchestration과 dbt profile은 각자의 Change에서 처리한다.
- **Dependencies:** Pydantic field validation과 현재 `PROJECT_PIVOT_DUCKDB_PATH`, `PROJECT_PIVOT_SOURCE_ROOT` environment 이름을 재사용한다.

## Goals / Non-Goals

| Goals | Non-Goals |
| --- | --- |
| environment override를 typed request로 변환 | 모든 `.env.example` key를 application config로 승격 |
| single request owner를 제공 | dbt profile fallback 또는 Dagster resource 변경 |

## Architecture

request module에 `data_operation_request_from_environment()`를 추가한다. 이 function은 optional mapping을 받아 test에서 process environment를 직접 변경하지 않고 검증할 수 있게 하며, 알려진 설정만 override dictionary로 구성한 뒤 `DataOperationRequest` validation에 위임한다.

### Boundaries

| Boundary | Owns | Does Not Own |
| --- | --- | --- |
| `data_operations.request` | 환경 key 해석, local default, typed request validation | subprocess environment 주입, Dagster config, dbt profile fallback |
| caller | factory 호출 여부와 추가 explicit override | settings parsing 재구현 |

## Decisions

### D1. Pydantic을 validation authority로 유지

- **Decision** - 환경에서 읽은 값은 `DataOperationRequest` 생성자로 전달한다.
- **Rationale** - source year range 등 기존 validation을 단일 위치에서 유지한다.
- **Trade-off** - 환경 변수 오류가 factory 호출 시점에 validation error로 노출된다.

### D2. 지원 key를 최소화

- **Decision** - database path, source root, source year만 해석한다.
- **Rationale** - review finding의 operational defaults만 해결하고 artifact/API/EDA 설정 의미를 추측하지 않는다.
- **Trade-off** - 다른 `.env.example` key는 별도 owner가 생길 때까지 request에 반영되지 않는다.

## Testability

| Boundary / Behavior | Test Strategy | Evidence |
| --- | --- | --- |
| override 해석 | component | 생성 request가 설정 값을 보유 |
| fallback 보존 | component | 기존 local default와 동일 |
| invalid year | component | Pydantic validation error |

- **TDD Boundary:** environment mapping에서 request를 만드는 공개 function.
- **Failure Signals:** 지원된 override 무시 또는 invalid year 허용.

## Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| `source_year` 문자열 변환 오류 | 잘못된 partition 대상 선택 | Pydantic validation을 통한 명시적 실패 test |
