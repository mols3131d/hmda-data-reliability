---
type: openspec-spec-driven-tdd-spec
category: spec
title: dbt-analytics
description: dbt analytics profile의 database target ownership을 변경한다.
tags:
  - "domain:data-platform"
  - "capability:dbt-analytics"
  - "configuration"
---

## ADDED Requirements

### Requirement: Explicit analytics database target

시스템은 dbt analytics profile의 DuckDB path를 `PROJECT_PIVOT_DUCKDB_PATH`에서 받아야 한다(SHALL). profile은 independent fallback database path를 가져서는 안 된다(MUST NOT).

#### Scenario: Caller-provided database path

- **GIVEN** caller가 `PROJECT_PIVOT_DUCKDB_PATH`를 설정했을 때
- **WHEN** dbt analytics profile을 해석할 때
- **THEN** profile은 제공된 path를 database target으로 사용해야 한다.

#### Scenario: Missing database path

- **GIVEN** `PROJECT_PIVOT_DUCKDB_PATH`가 설정되지 않았을 때
- **WHEN** caller가 dbt analytics profile을 해석할 때
- **THEN** profile은 local database path를 독립적으로 선택해서는 안 된다.
