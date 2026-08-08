---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: Data Operations dbt Runner Refactoring Tasks
description: runner.py의 dbt build 커맨드 생성과 실행 책임을 프라이빗 헬퍼 함수로 추출하고 검증한다.
tasks_completed: 4
tasks_total: 4
tags:
  - "domain:data-operations"
  - "capability:data-operations-dbt-runner"
  - "refactor"
---

> [!NOTE]
> `runner.py`의 `run_dbt_build` 함수를 `_build_dbt_command`와 `_run_dbt_command` 프라이빗 헬퍼 함수로 추출하고 테스트 및 정적 검사를 완료합니다.

## Tasks

### 1. Refactor runner.py Helpers

- [x] 1.1 Extract `_build_dbt_command` and `_run_dbt_command` helper functions from `run_dbt_build` in `src/project_pivot/data_operations/runner.py`.
  - **Covers:** Structured dbt Build Command Execution
  - **Done when:** `_build_dbt_command`와 `_run_dbt_command` 프라이빗 헬퍼 함수가 정의되고 `run_dbt_build`가 이를 호출하도록 작성된다.

### 2. Verify Behavior and Quality

- [x] 2.1 Run unit/component tests in `tests/data_operations/test_dbt_runner.py`.
  - **Done when:** `uv run pytest tests/data_operations/test_dbt_runner.py`가 오류 없이 6개 통과한다.

- [x] 2.2 Run static code analysis and formatting checks.
  - **Done when:** `uv run ruff check src/project_pivot/data_operations/runner.py` 및 `uv run ruff format src/project_pivot/data_operations/runner.py`가 오류 없이 통과한다.

## Self-Review

- [x] 모든 관련 Requirement와 Scenario가 구현 및 테스트에 반영되었는지 확인한다.
- [x] Design의 Decision과 Boundary를 지키면서 중복과 불필요한 복잡성을 제거한다.
- [x] 관련 테스트, 실패 경로와 정적 검사가 통과하는지 확인한다.
- [x] 필요한 문서, 설정과 운영 절차를 갱신한다.
- [x] 알려진 제약과 후속 작업을 명시한다.
