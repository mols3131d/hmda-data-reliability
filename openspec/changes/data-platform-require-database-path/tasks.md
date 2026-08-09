---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: Data Platform Required dbt Database Path
description: dbt profile의 독립 database fallback을 제거하고 contract를 검증한다.
tasks_completed: 4
tasks_total: 4
tags:
  - "domain:data-platform"
  - "capability:dbt-analytics"
  - "configuration"
---

> [!NOTE]
> profile fallback 부재를 먼저 test로 고정하고 한 줄 설정 변경 후 기존 dbt integration test로 caller-provided target 동작을 확인한다.

## Tasks

### 1. Profile ownership

- [x] 1.1 **RED** — dbt profile이 hardcoded database fallback을 갖지 않는 configuration test를 추가한다.
  - **Covers:** `Missing database path`
  - **Done when:** 현재 fallback path 때문에 test가 실패한다.

- [x] 1.2 **GREEN** — profile의 `env_var` fallback argument를 제거한다.
  - **Done when:** configuration test가 통과한다.

### 2. Verification

- [x] 2.1 caller-provided temporary database path로 dbt analytics integration test를 실행한다.
  - **Covers:** `Caller-provided database path`
  - **Done when:** dbt build와 existing analytics oracle이 통과한다.

- [x] 2.2 implementation review와 strict OpenSpec validation을 완료한다.
  - **Done when:** finding이 없고 validation evidence가 기록된다.
