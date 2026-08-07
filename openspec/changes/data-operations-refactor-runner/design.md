---
type: openspec-spec-driven-tdd-design
category: design
title: Data Operations dbt Runner Refactoring Design
description: runner.py의 dbt build 커맨드 생성과 실행 책임을 프라이빗 헬퍼 함수로 추출하여 단일 책임 원칙 준수 및 모킹/테스트 용이성을 향상시킨다.
tags:
  - "domain:data-operations"
  - "capability:data-operations-dbt-runner"
  - "refactor"
---

> [!NOTE]
> `data_operations/runner.py` 모듈 내 `run_dbt_build` 함수를 커맨드 빌더(`_build_dbt_command`)와 커맨드 실행기(`_run_dbt_command`) 프라이빗 헬퍼 함수로 리팩토링합니다.

## Context

- **Current State:** `runner.py` 모듈의 `run_dbt_build` 함수에 커맨드 조립, 인코딩/환경변수 준비, subprocess 실행, 예외 처리, 아티팩트 검증 로직이 한곳에 통합되어 있음.
- **Constraints:** 기존 `DataOperationRequest` 및 `DbtBuildResult` 퍼블릭 인터페이스와 `tests/data_operations/test_dbt_runner.py` 테스트 동작 계약을 100% 유지해야 함.
- **Dependencies:** Standard library `subprocess`, `os`, `pathlib.Path`.

## Goals / Non-Goals

| Goals | Non-Goals |
| --- | --- |
| `run_dbt_build` 내부 책임을 프라이빗 헬퍼 함수로 깔끔하게 분리 | 신규 외부 모듈/파일 생성 |
| 기존 단위/컴포넌트 테스트 100% 통과 | `load_raw_data` 등 다른 데이터 작업 모듈 리팩토링 |

## Architecture

`run_dbt_build` 진입점에서 프라이빗 헬퍼 오케스트레이션을 수행합니다.

```mermaid
flowchart LR
    Request[DataOperationRequest] --> BuildCmd[_build_dbt_command]
    BuildCmd --> RemoveArt[_remove_dbt_artifacts]
    RemoveArt --> RunCmd[_run_dbt_command]
    RunCmd --> ValidateArt[_validate_dbt_artifacts]
    ValidateArt --> Result[DbtBuildResult]
```

### Components

| Component | Responsibility | Change |
| --- | --- | --- |
| `_build_dbt_command` | dbt CLI 매개변수 리스트 조립 | 신규 추출 |
| `_run_dbt_command` | `subprocess.run` 기반 dbt 명령 실행 및 타임아웃/예외 포장 | 신규 추출 |
| `run_dbt_build` | 아티팩트 정리, 실행기 호출, 에러 검증, 결과 조립 오케스트레이션 | 리팩토링 |

## Decisions

### D1. 모듈 내부 프라이빗 헬퍼 추출 vs 별도 모듈 파일 분리

- **Decision** - `runner.py` 파일 내 프라이빗 헬퍼 함수(`_build_dbt_command`, `_run_dbt_command`)로 추출.
- **Rationale** - 100줄 내외의 모듈 크기에서 불필요하게 얇은 별도 `.py` 파일을 추가하면 패키지 복잡도가 증가함.
- **Trade-off** - 단일 파일 내 함수 개수는 증가하지만 모듈 간 수입/수출 복잡도를 방지함.

## Testability

| Boundary / Behavior | Test Strategy | Evidence |
| --- | --- | --- |
| dbt build 실행 및 예외 포장 | `tests/data_operations/test_dbt_runner.py` component test | pytest 통과 및 monkeypatch 기반 CompletedProcess / TimeoutExpired 포착 |

- **TDD Boundary:** 기존 `test_dbt_runner.py`의 5개 경계 케이스.
- **Failure Signals:** `DataOperationError` 발생 메시지 및 returncode / stderr 텍스트 검증.

## Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| CompletedProcess 타입 힌트 누락으로 인한 ruff static check 에러 | CI/Lint 실패 | `from subprocess import CompletedProcess` 타입 힌트 추가 |
