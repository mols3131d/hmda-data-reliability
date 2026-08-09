---
type: openspec-spec-driven-tdd-design
category: design
title: Data Platform Required dbt Database Path
description: dbt profile의 database path fallback을 제거하고 caller-provided environment만 사용한다.
tags:
  - "domain:data-platform"
  - "capability:dbt-analytics"
  - "configuration"
---

> [!NOTE]
> `env_var`의 default argument를 제거한다. Data Operations runner는 이미 request database path를 subprocess environment에 넣고 integration test도 path를 명시하므로 dbt profile은 adapter 역할만 남는다.

## Context

- **Current State:** profile의 `env_var`가 `data/project_pivot.duckdb` fallback을 보유한다.
- **Constraints:** dbt model, schema와 transformation behavior는 바꾸지 않는다.
- **Dependencies:** Data Operations runner와 direct dbt caller가 `PROJECT_PIVOT_DUCKDB_PATH`를 제공한다.

## Goals / Non-Goals

| Goals | Non-Goals |
| --- | --- |
| 하나의 DuckDB local default authority 유지 | direct dbt 실행을 위한 새 CLI 또는 settings loader 추가 |

## Decisions

### D1. profile fallback을 제거

- **Decision** - `env_var('PROJECT_PIVOT_DUCKDB_PATH')`만 사용한다.
- **Rationale** - dbt adapter가 application default를 재정의하지 않는다.
- **Trade-off** - environment 없는 direct dbt invocation은 configuration error로 종료한다.

## Testability

| Boundary / Behavior | Test Strategy | Evidence |
| --- | --- | --- |
| caller path 전달 | integration | temporary DuckDB path로 dbt build 성공 |
| fallback 부재 | configuration | profile source에 path default 없음 |

- **TDD Boundary:** profile rendering input.
- **Failure Signals:** hardcoded fallback path가 profile에 남음.

## Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| local direct dbt command failure | user-visible config error | `.env.example` key와 existing dbt test helper로 required input을 명확히 함 |
