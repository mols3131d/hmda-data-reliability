---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: Orchestration Runtime Settings Consumption
description: Resource adapter의 runtime settings 소비를 TDD로 구현하고 검증한다.
tasks_completed: 5
tasks_total: 5
tags:
  - "domain:orchestration"
  - "capability:pipeline"
  - "configuration"
---

> [!NOTE]
> Resource-to-request behavior를 먼저 test로 고정한 뒤 canonical request factory 위에 minimal adapter를 구현한다.

## Tasks

### 1. Resource adapter

- [x] 1.1 **RED** — environment-backed default와 explicit resource override를 검증하는 component test를 추가한다.
  - **Covers:** `Environment-backed default resource`, `Explicit Dagster override`
  - **Done when:** 현재 literal default behavior로 test가 실패한다.

- [x] 1.2 **GREEN** — resource가 canonical request factory를 소비하고 explicit field만 override하도록 구현한다.
  - **Done when:** 두 scenario test가 통과한다.

- [x] 1.3 **REFACTOR** — resource가 operational default authority를 다시 갖지 않는지 정리한다.
  - **Done when:** literal pipeline default가 resource에 남지 않고 update mapping은 `None`을 제외하며 merged request가 재검증되고 invalid overridden environment key는 차단하지 않는다.

### 2. Verification

- [x] 2.1 orchestration 관련 test를 실행한다.
  - **Done when:** resource 및 pipeline materialization test가 통과한다.

- [x] 2.2 계획과 implementation review를 완료한다.
  - **Done when:** 모든 scenario와 validation evidence가 task에 연결된다.
