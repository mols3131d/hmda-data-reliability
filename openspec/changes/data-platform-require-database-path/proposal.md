---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Data Platform Required dbt Database Path
description: dbt profile이 application과 독립적인 DuckDB path fallback을 소유하지 않도록 변경한다.
tags:
  - "domain:data-platform"
  - "capability:dbt-analytics"
  - "configuration"
---

> [!NOTE]
> dbt profile은 `PROJECT_PIVOT_DUCKDB_PATH`를 필수 adapter input으로 소비한다. local database path의 default는 Data Operations request에만 남아 direct dbt caller는 database target을 명시해야 한다.

## Overview

| Why | What | Capabilities |
| --- | --- | --- |
| dbt profile의 DuckDB fallback이 application default와 별도 authority | profile fallback 제거 및 required input contract 검증 | `data-platform-dbt-analytics` |

## Why

`dbt/profiles.yml`의 `data/project_pivot.duckdb` fallback은 Data Operations와 Dagster가 소유하는 local operational default를 독립적으로 복제한다. direct dbt와 application path가 서로 다른 database로 drift할 수 있다.

## What Changes

- **Modify:** dbt DuckDB profile이 `PROJECT_PIVOT_DUCKDB_PATH` 없이 database target을 선택하지 않도록 변경

## Boundaries

| In Scope | Out of Scope |
| --- | --- |
| dbt profile database path input contract와 test | Data Operations local default, Dagster resource, dbt model semantics |

## Capabilities

### Modified Capabilities

#### `data-platform-dbt-analytics`

- dbt analytics 실행은 caller가 제공한 database path를 사용해야 한다.

## Impact

| Area | Impact |
| --- | --- |
| Code / Systems | `dbt/profiles.yml`, dbt integration test |
| Operations / Dependencies | direct dbt caller는 `PROJECT_PIVOT_DUCKDB_PATH`를 설정해야 함 |
