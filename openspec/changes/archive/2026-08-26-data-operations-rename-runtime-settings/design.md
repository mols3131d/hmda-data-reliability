---
type: openspec-spec-driven-tdd-design
category: design
title: Runtime setting identity migration design
description: supported runtime setting을 하나의 current namespace로 정리하는 최소 설계다.
tags:
  - domain:data-operations
  - capability:data-operations-stage-execution
---

## Context

`DataOperationRequest`, orchestration runtime adapter와 dbt profile/subprocess가 하나의 DuckDB path setting을 공유한다. Retired prefix를 일부 boundary에만 남기면 동일한 runtime configuration을 여러 이름으로 번역해야 한다.

## Goals / Non-Goals

### Goals

- Data Operations와 orchestration이 동일한 `HMDA_RELIABILITY_*` setting을 사용한다.
- dbt subprocess와 profile도 같은 DuckDB setting을 사용한다.
- 새 default database filename을 current project identity와 일치시킨다.
- 기존 precedence와 validation behavior를 보존한다.

### Non-Goals

- Retired setting alias 유지
- 기존 local DuckDB file 자동 이동·복사·삭제
- Airflow task topology 또는 dbt model behavior 변경
- repository slug 변경

## Decisions

### D1. One supported environment namespace

Supported environment surface는 `HMDA_RELIABILITY_DUCKDB_PATH`, `HMDA_RELIABILITY_SOURCE_ROOT`, `HMDA_RELIABILITY_SOURCE_YEAR` 하나만 제공한다. Accessible consumer 조사에서 compatibility 근거가 확인되지 않았으므로 fallback alias를 만들지 않는다.

### D2. Explicit paths remain the migration escape hatch

Existing local database를 유지해야 하는 caller는 `HMDA_RELIABILITY_DUCKDB_PATH` 또는 explicit request path로 기존 파일을 계속 가리킬 수 있다. Application은 local state를 암묵적으로 move/copy하지 않는다.

### D3. Identity-only adjacent refactors stay outside the capability contract

Airflow DAG/Asset identity와 dbt project namespace는 execution semantics를 바꾸지 않는 adjacent refactor로 수행한다. Observable Data Operations behavior가 추가로 바뀌지 않는 한 이 delta spec에 넣지 않는다.

## Testability

- request builder가 current environment key를 읽는지 unit test로 검증한다.
- explicit runtime value가 environment보다 우선하는 기존 precedence를 유지하는지 검증한다.
- dbt profile과 subprocess가 동일한 current DuckDB key를 사용하는지 component/integration test로 검증한다.
- repository current source/config/test/docs에서 retired active identity가 historical area 밖에 남지 않았는지 search로 검증한다.
