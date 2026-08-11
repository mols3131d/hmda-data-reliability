---
type: openspec-spec-driven-tdd-design
category: design
title: Orchestration Runtime Settings Consumption
description: Dagster config의 명시 여부를 보존하면서 canonical request를 adapter input으로 사용한다.
tags:
  - "domain:orchestration"
  - "capability:pipeline"
  - "configuration"
---

> [!NOTE]
> Resource field의 literal default를 `None`으로 바꾸어 값이 지정되지 않았음을 표현한다. `to_request()`는 Data Operations factory 결과와 명시 field를 병합한 새 request를 생성해 validation을 다시 적용한다.

## Context

- **Current State:** resource는 database path, source root, source year의 default를 Data Operations request와 중복해 정의한다.
- **Constraints:** asset body에는 business logic을 추가하지 않고 resource만 config-to-request adapter로 유지한다.
- **Dependencies:** `data_operation_request_from_environment()`가 canonical default와 validation을 제공한다.

## Goals / Non-Goals

| Goals | Non-Goals |
| --- | --- |
| 기본 pipeline에 environment runtime settings 반영 | Dagster graph 또는 asset dependency 변경 |
| explicit resource config의 우선권 보존 | dbt profile 또는 environment key ownership 변경 |

## Architecture

Resource의 override 가능한 field는 optional로 선언한다. `to_request()`는 factory로 request를 만들고, `None`이 아닌 resource 값만 update mapping으로 만든다. `source_file`과 `run_dbt_build`도 기존 명시 config semantics를 유지하기 위해 같은 mapping에 포함한다.

### Boundaries

| Boundary | Owns | Does Not Own |
| --- | --- | --- |
| Data Operations | environment parsing, default, request validation | Dagster resource serialization |
| Orchestration resource | explicit Dagster config를 request override로 변환 | 별도 operational default |

## Decisions

### D1. Optional resource fields로 override presence 표현

- **Decision** - 기본값이 있는 pipeline setting은 `None`을 default로 한다.
- **Rationale** - Dagster가 지정하지 않은 값과 literal default를 구분할 수 있다.
- **Trade-off** - resource schema의 optional field가 늘어나지만 configuration authority가 단일화된다.

## Testability

| Boundary / Behavior | Test Strategy | Evidence |
| --- | --- | --- |
| default resource | component | environment-derived request field |
| explicit config | component | resource field가 environment value를 대체 |

- **TDD Boundary:** `DataOperationsResource.to_request()`.
- **Failure Signals:** environment value 미반영 또는 explicit config 우선순위 역전.

## Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| `None`을 Pydantic request로 전달 | invalid request 생성 | `None` field를 update mapping에서 제외 |
