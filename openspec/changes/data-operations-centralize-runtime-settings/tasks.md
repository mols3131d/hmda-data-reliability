---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: Data Operations Runtime Settings Centralization
description: Environment-to-request contract와 focused component 검증을 구현한다.
tasks_completed: 5
tasks_total: 5
tags:
  - "domain:data-operations"
  - "capability:stage-execution"
  - "configuration"
---

> [!NOTE]
> request factory의 observable behavior를 먼저 component test로 고정한 뒤 최소 구현과 public export를 추가한다. 완료 기준은 focused test와 data operations suite 통과다.

## Tasks

### 1. Environment request contract

- [x] 1.1 **RED** — environment override, absent key fallback, invalid source year를 검증하는 component test를 추가한다.
  - **Covers:** `Environment-backed execution request`, `Absent environment settings`, `Invalid source year setting`
  - **Done when:** factory 부재 또는 동작 불일치로 test가 실패한다.

- [x] 1.2 **GREEN** — 지원 key를 `DataOperationRequest`로 해석하는 factory를 구현하고 공개 export한다.
  - **Done when:** package public surface에서 factory를 import할 수 있고 직접 request 생성 동작이 유지된다.

- [x] 1.3 **REFACTOR** — request default 또는 validation authority를 중복하지 않도록 구현을 정리한다.
  - **Done when:** parsing logic이 최소이고 Pydantic validation이 유일한 validation authority다.

### 2. Verification

- [x] 2.1 data operations focused 및 domain test를 실행한다.
  - **Done when:** `tests/data_operations`가 통과한다.

- [x] 2.2 계획, 구현 범위와 validation evidence를 self-review한다.
  - **Done when:** 모든 scenario가 test에 연결되고 남은 scope가 명시된다.
