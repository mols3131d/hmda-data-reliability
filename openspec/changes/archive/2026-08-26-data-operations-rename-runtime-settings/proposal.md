---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Rename Data Operations runtime settings
description: HMDA Data Reliability identity에 맞게 pipeline runtime setting을 정리하고 unsupported legacy alias를 남기지 않는다.
tags:
  - domain:data-operations
  - capability:data-operations-stage-execution
---

## Why

Public project와 Python package identity는 HMDA Data Reliability로 정리됐지만 Data Operations의 supported environment setting은 retired identity prefix를 계속 노출한다. Repository와 접근 가능한 cross-repository search에서 이 이름을 요구하는 external consumer 근거를 찾지 못했으므로 dual naming을 유지하는 것보다 current identity로 contract를 닫는 편이 단순하다.

## What Changes

- Supported pipeline environment key를 `HMDA_RELIABILITY_DUCKDB_PATH`, `HMDA_RELIABILITY_SOURCE_ROOT`, `HMDA_RELIABILITY_SOURCE_YEAR`로 변경한다.
- 새 request의 local default DuckDB filename을 `data/hmda_reliability.duckdb`로 맞춘다.
- Existing precedence와 request validation semantics는 유지한다.
- Retired environment name을 위한 compatibility alias는 제공하지 않는다.

## Boundaries

- In scope: Data Operations environment-backed request contract, orchestration adapter의 environment consumption, dbt subprocess/profile DuckDB path injection, current example configuration.
- Out of scope: Airflow scheduling/task topology behavior, dbt model behavior, Reliability decision logic, local database file 자동 migration, GitHub repository slug.

## Capabilities

### Modified Capabilities

#### `data-operations-stage-execution`

Environment-backed execution request가 HMDA Data Reliability runtime setting을 사용하도록 변경하되 기존 precedence, default fallback과 validation behavior는 유지한다.
