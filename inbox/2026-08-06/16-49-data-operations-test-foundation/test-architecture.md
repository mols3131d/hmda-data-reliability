---
title: Data Operations Test Architecture
description: data_operations contract를 저비용으로 보호할 test layer, harness와 oracle을 설계한다.
tags:
  - data-operations
  - test-architecture
  - pytest
---

# Test Architecture

## Objective

Known contract를 가장 싼 신뢰 가능한 boundary에서 검증한다. Production architecture가 아니라 public behavior와 persisted evidence를 보호한다.

## Layers

| Level | Protects | Real boundary |
| --- | --- | --- |
| Unit | request validation, public surface, deep immutability | none |
| Component | raw/dbt/lifecycle public stage와 error translation | file, DuckDB, process |
| Integration | Dagster graph, execution order와 event semantics | Dagster event stream |

Integration으로만 검증해야 하는 위험을 unit mock으로 낮추지 않는다. 반대로 pure invariant를 integration test로 올리지 않는다.

## Harnesses

### Fake dbt executable

Temporary `PATH`에 platform-compatible `dbt` wrapper를 둔다. Wrapper는 argument를 기록하고, 전달받은 target에 최소 artifact를 생성하며, exit code·delay·artifact omission만 제어한다.

이 harness는 다음 adapter contract만 검증한다.

- output location 전달
- stale artifact 제거
- timeout과 non-zero exit 처리
- result path와 이번 invocation artifact의 일치

실제 dbt model semantics는 흉내 내지 않는다.

### HMDA fixture factory

작은 source fixture가 여러 year, file name, row contribution과 rerun을 표현한다. Oracle은 합의한 provenance와 persisted partition rows다.

### Exception matrix

| Stage | Dependency failure | Public observation |
| --- | --- | --- |
| raw | HMDA / DuckDB operational error | `DataOperationError`, cause, safe context |
| dbt | timeout / startup / exit / artifact error | `DataOperationError` |
| lifecycle | Reliability / DuckDB operational error | `DataOperationError`, cause, safe context |

Unexpected programming error는 wrapping하지 않는 negative scenario를 둔다.

### Dagster event oracle

`materialize()` 결과에서 asset key, event count와 metadata를 직접 확인한다. Raw-only 경로는 dbt asset을 실행한 뒤 event를 억제하는 방식이 아니라 asset selection 또는 별도 job으로 제외한다. Log text는 oracle이 아니다.

## Contract Test Acceptance

새 regression test는 다음 조건을 충족한다.

1. Fix 전 baseline 또는 controlled negative fixture에서 contract assertion으로 실패한다.
1. Import, fixture 또는 environment 오류를 defect 재현으로 계산하지 않는다.
1. Fix 후 같은 oracle로 통과한다.
1. Production behavior를 우회하는 mock이나 test-only branch를 만들지 않는다.

## Module Ownership

| Module | Level | Owns |
| --- | --- | --- |
| `tests/data_operations/test_request_and_results.py` | unit | validation, public model semantics |
| `tests/data_operations/test_raw_runner.py` | component | raw result, provenance, error translation |
| `tests/data_operations/test_dbt_runner.py` | component | process adapter, artifacts, failures |
| `tests/data_operations/test_incident_lifecycle.py` | component | comparison, translation, read-only invariant |
| `tests/data_operations/test_public_contract.py` | unit | exports, coordinator absence |
| `tests/orchestration/test_dagster_definitions.py` | integration | graph, events, metadata |

복잡한 scenario matrix가 실제 test로 도입될 때만 대응 `test_*.design.md`를 추가한다.

## Feedback Commands

```bash
# focused
uv run pytest tests/data_operations/test_dbt_runner.py

# domain
uv run pytest tests/data_operations

# orchestration affected
uv run pytest tests/data_operations \
  tests/orchestration/test_dagster_definitions.py
```

전체 suite는 shared fixture, public import 또는 project configuration이 바뀔 때 확장한다.

## Anti-Patterns

- helper call 횟수를 public contract로 고정
- mock이 artifact나 domain result를 대신 생성
- 미결정 architecture를 test 이름으로 확정
- broad wrapping으로 programming error 은폐
- focused run마다 full dbt integration 실행
- 하나의 test가 raw, dbt, lifecycle과 Dagster를 모두 검증
- coverage 수치로 failure-model 누락을 정당화

## Review Boundary

Test는 자동 승인 장치가 아니다. 합의된 판단의 반복 비용을 줄이는 장치다. 변경 분류와 review depth는 [`change-gates-and-delivery.md`](change-gates-and-delivery.md)가 소유한다.
