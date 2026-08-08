---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Refactor Data Operations dbt Runner
description: Extract command building and subprocess execution helpers from data_operations runner.py to separate concerns and improve testability
tags:
  - "domain:data-operations"
  - "capability:data-operations-dbt-runner"
  - "refactor"
---

> [!NOTE]
> `data_operations/runner.py`의 `run_dbt_build` 함수에서 dbt CLI 인자 구성 및 프로세스 실행 로직을 전용 헬퍼 함수로 분리하여 단일 책임 원칙(SRP)을 준수하고 단위 테스트 용이성을 개선합니다.

> [!IMPORTANT]
> Archive reconciliation에서 이 변경은 observable behavior나 public contract를 바꾸지 않은 내부 refactor로 재분류했다. 아래 `data-operations-dbt-runner` delta는 당시 planning 기록으로만 보존하며 `openspec/specs/`에는 sync하지 않는다. Reusable dbt stage behavior의 canonical owner는 기존 `pipeline-stage-runtime`이다.

## Overview

| Why | What | Capabilities |
| --- | --- | --- |
| `run_dbt_build` 내에 CLI 커맨드 구성, subprocess 실행, 아티팩트 관리가 결합되어 있어 가독성과 모킹/테스트 용이성이 떨어짐 | `_build_dbt_command` 및 `_run_dbt_command` 헬퍼 함수 추출 | historical `data-operations-dbt-runner` planning only |

## Why

- `runner.py` 모듈에서 `run_dbt_build`가 dbt build 커맨드 파라미터 구성, 환경 변수 설정, subprocess 타임아웃/예외 처리, 아티팩트 검증 등의 다중 책임을 수행하고 있습니다.
- 책임 단위를 함수 수준으로 분리함으로써 코드 가독성을 확보하고 커맨드 생성과 실행 단계를 독립적으로 검증할 수 있도록 개선합니다.

## What Changes

- **Modify:** `run_dbt_build` 내 커맨드 리스트 생성 로직을 `_build_dbt_command` 헬퍼 함수로 추출
- **Modify:** `run_dbt_build` 내 `subprocess.run` 커맨드 실행 및 타임아웃/예외 처리 로직을 `_run_dbt_command` 헬퍼 함수로 추출

## Boundaries

| In Scope | Out of Scope |
| --- | --- |
| `src/project_pivot/data_operations/runner.py` 내부 헬퍼 함수 추출 및 구조화 | `load_raw_data` 및 `run_incident_lifecycle` 구조 변경 |
| 기존 `tests/data_operations/test_dbt_runner.py` 테스트 검증 및 유지 | 외부 dbt CLI 커맨드 변경 또는 새로운 dbt 빌드 옵션 추가 |

## Capabilities

### New Capabilities

#### `data-operations-dbt-runner`

- 당시 planning에서는 `run_dbt_build`의 내부 helper 구조를 별도 Capability로 분류했으나, archive 시점에는 canonical capability로 승격하지 않는다.

## Impact

| Area | Impact |
| --- | --- |
| Code / Systems | `src/project_pivot/data_operations/runner.py` 내부 헬퍼 함수 2개 추가 및 호출부 연동 |
| Data / Contracts | 없음 (기존 DataOperationRequest / DbtBuildResult 계약 동일 유지) |
| Interfaces / APIs | 없음 (`run_dbt_build` 함수 시그니처 동일) |
| Operations / Dependencies | 없음 |

## Appendix

### Alternatives

| Alternative | Why Rejected |
| --- | --- |
| 별도 `dbt_executor.py` 신규 파일 생성 | 모듈당 파일 분리가 과도하여 `runner.py` 내부 프라이빗 헬퍼 함수로 해결 가능 |

### Trade-offs

| Choice | Gain | Cost |
| --- | --- | --- |
| `runner.py` 내부 프라이빗 헬퍼 함수 추출 | 새로운 파일 추가 없이 가독성과 분리성 확보 | `runner.py` 함수 개수 증가 |
