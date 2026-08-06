---
type: review
category: review
title: Data Operations Domain Review
description: data_operations application boundary의 contract, runtime behavior와 caller 일관성을 검토한다.
status: completed
tags:
  - data-operations
  - domain-review
---

> [!NOTE]
> **Revise.** Stage API와 read-only lifecycle은 적절하다. 다만 dbt output, public error, Dagster materialization과 result metadata의 의미가 runtime에서 완전히 보장되지 않는다.

## Overview

| Target | Revision | Scope | Verdict |
| --- | --- | --- | --- |
| `src/project_pivot/data_operations/`와 직접 caller·spec·tests | `f08c2fb7a71aecd6659b77dcab5d0026e5d9ee93` | request, raw load, dbt build, lifecycle, result/error contract, Dagster 연계 | Revise |

## Findings

### F1. Configured artifact paths do not control dbt output

- **Severity** - Major
- **Location** - `request.py`, `runner.py`, `test_dbt_runner.py`
- **Evidence** - Request는 manifest와 run-results path를 받지만 `dbt build` command는 output location을 전달하지 않는다. Test stub은 request 경로에 artifact를 직접 생성해 이 연결을 검증하지 않는다.
- **Impact** - Non-default path에서는 build가 성공해도 runner가 다른 위치를 검사해 실패할 수 있다.
- **Required Change** - Output source of truth를 하나로 만들고 command와 result path가 같은 target을 사용하도록 한다. Fake executable과 real filesystem으로 adapter contract를 검증한다.

### F2. Public stages expose lower-domain errors

- **Severity** - Major
- **Location** - `docs/domains/data-operations.md`, `runner.py`, `incident_lifecycle.py`
- **Evidence** - Domain contract는 operational error를 `DataOperationError`로 통일한다. `load_raw_data()`와 `run_incident_lifecycle()`는 예상 가능한 HMDA, Reliability 또는 DuckDB error를 그대로 노출할 수 있다.
- **Impact** - Caller가 stage마다 다른 dependency taxonomy와 handling policy를 알아야 한다.
- **Required Change** - 예상 가능한 application failure만 `DataOperationError`로 변환하고 cause와 필요한 safe context를 보존한다. Programming error는 broad wrapping하지 않는다.

### F3. dbt can be skipped while Silver/Gold is materialized

- **Severity** - Major
- **Location** - `request.py`, `orchestration/defs/resource.py`, `orchestration/defs/assets.py`, standard orchestration spec
- **Evidence** - `run_dbt_build=False`이면 dbt를 실행하지 않고 `MaterializeResult`를 반환한다. Standard pipeline spec은 raw 다음 dbt build 실행을 요구한다.
- **Impact** - Stale Silver/Gold가 새로 materialize된 것처럼 기록될 수 있다.
- **Required Change** - Standard pipeline의 skip policy를 명시한다. Raw-only는 asset selection 또는 별도 job으로 표현하고, 미실행 asset에는 materialization event를 기록하지 않는다. Orchestration control은 shared stage request에서 분리한다.

### F4. `source_file_count` does not have one stable meaning

- **Severity** - Minor
- **Location** - domain guide, `runner.py`, partition loader, Dagster metadata
- **Evidence** - 문서는 processed file count를 설명하지만 runner는 discovered path 전체 수를 반환한다. 실제 load는 year와 선택적 file로 row를 필터링한다.
- **Impact** - Result와 metadata가 실제 적재 범위를 과장할 수 있다.
- **Required Change** - Discovered 또는 contributing 중 의미를 결정해 이름과 계산을 맞춘다. 둘 다 필요하면 field를 분리한다.

### F5. Frozen results contain mutable collections

- **Severity** - Minor
- **Location** - domain guide, `dbt_result.py`, `lifecycle_result.py`
- **Evidence** - Result는 변경 불가로 문서화됐지만 `command`와 summary fields는 `list[str]`다. `frozen=True`는 list mutation을 막지 않는다.
- **Impact** - 반환 후 실행 evidence가 바뀔 수 있다.
- **Required Change** - Deep immutability가 contract라면 tuple을 사용하고 nested mutation test를 둔다. 아니라면 문서 contract를 완화한다.

## Validation

| Check | Result |
| --- | --- |
| Public API가 stage function만 노출 | Pass |
| Lifecycle read-only invariant | Pass |
| Timeout, stale artifact와 artifact absence 처리 | Pass |
| Custom output end-to-end connection | Fail |
| Public error taxonomy | Fail |
| Standard pipeline materialization semantics | Fail |
| Runtime suite execution | Not Verified |

## Remaining Risks

- Baseline profile column set 호환성은 아직 정의되지 않았다.
- Artifact는 존재 여부만 검증하며 최소 usable structure는 정의되지 않았다.
- Test suite와 실제 dbt process는 실행하지 않았다.

## Verdict

| Decision | Rationale | Route |
| --- | --- | --- |
| Revise | 세 가지 Major boundary defect와 두 가지 contract gap이 남아 있다. | owning contracts, focused tests와 분리된 implementation changes |
