---
title: Data Operations Contract Test Matrix
description: data_operations의 requirement와 failure risk를 concrete scenario, independent oracle, test level과 현재 coverage로 매핑한다.
tags:
  - data-operations
  - contract-matrix
  - test-design
  - regression
---

# Contract Test Matrix

## Legend

| Coverage | Meaning |
| --- | --- |
| Protected | 현재 test가 핵심 risk와 oracle을 직접 보호한다. |
| Partial | 일부 path만 보호하거나 mock 때문에 연결 risk가 남는다. |
| Missing | 합의된 contract에 대응하는 test가 없다. |
| Decision | behavior 결정이 선행되어야 한다. |

## Matrix

| ID | Contract / Risk | Scenario | Independent oracle | Level | Coverage |
| --- | --- | --- | --- | --- | --- |
| DO-PUB-01 | Stage API만 공개 | package public API 검사 | `run_pipeline`, `PipelineRunResult`, CLI 부재 | unit | Protected |
| DO-REQ-01 | Unknown field 거부 | 잘못된 field로 request 생성 | Pydantic validation failure | unit | Missing |
| DO-REQ-02 | `profile_columns` normalize | string/list/tuple 입력 | immutable tuple과 빈 값 거부 | unit | Missing |
| DO-REQ-03 | Orchestration control 분리 | stage request public field 검사 | `run_dbt_build` 부재 또는 별도 config ownership | unit | Decision |
| DO-RAW-01 | Partition load result | 여러 year fixture에서 한 year 적재 | persisted partition rows와 result row count 일치 | component | Partial |
| DO-RAW-02 | File count semantics | 여러 file 중 일부만 선택 | 합의한 contributing/discovered count와 result 일치 | component | Decision |
| DO-RAW-03 | Idempotent partition rerun | 같은 request 두 번 실행 | 해당 partition row 중복 없음 | component | 하위 domain coverage 확인 필요 |
| DO-ERR-RAW-01 | HMDA failure translation | loader가 `HMDADataLoadError` 발생 | `DataOperationError`, cause 보존 | component | Missing |
| DO-ERR-RAW-02 | DuckDB open failure translation | database open 실패 | `DataOperationError`, cause 보존 | component | Missing |
| DO-DBT-01 | Artifact required | exit 0, artifact 없음 | `DataOperationError` | component | Protected |
| DO-DBT-02 | Stale artifact rejection | stale files + 새 artifact 미생성 | stale 제거, operation failure | component | Protected |
| DO-DBT-03 | Timeout translation | process timeout | `DataOperationError` with chained timeout | component | Protected |
| DO-DBT-04 | Startup failure translation | executable 없음/OS error | `DataOperationError` with cause | component | implementation protected, explicit test 보강 가능 |
| DO-DBT-05 | Non-zero exit context | multi-line stderr | 마지막 safe line과 return code | component | Protected |
| DO-DBT-06 | Custom output connection | non-default target config | fake executable이 그 위치에 artifact 생성, result path 일치 | component | Missing |
| DO-DBT-07 | This-invocation artifact | successful fake invocation | invocation marker가 있는 새 artifact | component | Partial |
| DO-DBT-08 | Artifact usability | malformed/minimal artifact | 합의한 minimum parse contract | component | Decision |
| DO-ERR-LIFE-01 | Reliability failure translation | impact/profile/draft failure | `DataOperationError`, cause 보존 | component | Missing |
| DO-ERR-LIFE-02 | DuckDB failure translation | read-only connection/query failure | `DataOperationError`, cause 보존 | component | Missing |
| DO-LIFE-01 | Actual current comparison | real DuckDB partition | measured row count와 detections | component | Protected |
| DO-LIFE-02 | All detections analyzed | 둘 이상 incident | ordered unique summaries | component | Protected |
| DO-LIFE-03 | No incident short circuit | threshold 미만 profile | 빈 result, impact 미실행 | component | Protected |
| DO-LIFE-04 | Baseline identity compatibility | asset 또는 partition mismatch | contextual `DataOperationError` | component | Protected |
| DO-LIFE-05 | Baseline shape compatibility | profile column set mismatch | reject 또는 defined comparison behavior | component | Decision |
| DO-LIFE-06 | Read-only lifecycle | incident 발생 | target rows와 filesystem 불변 | component | Protected |
| DO-RES-01 | Top-level frozen result | field 재할당 | mutation failure | unit | Partial |
| DO-RES-02 | Deep immutable collections | command/action list mutation | mutation 불가, tuple 유지 | unit | Missing |
| DO-ORCH-01 | Standard graph order | pipeline materialize | raw → dbt dependency와 event | integration | Partial |
| DO-ORCH-02 | Standard pipeline runs dbt | standard job 실행 | dbt stage가 실제 호출되고 materialization 존재 | integration | Partial |
| DO-ORCH-03 | No false materialization | raw-only 또는 dbt disabled path | dbt asset materialization event 없음 | integration | Missing / current behavior fails |
| DO-ORCH-04 | Raw metadata truth | filtered load | metadata와 result contract 일치 | integration | Decision dependent |
| DO-ORCH-05 | dbt metadata truth | successful build | succeeded, artifact path가 actual output과 일치 | integration | Partial |

## First Test Foundation Slice

첫 iteration은 다음 여섯 test contract로 제한한다.

1. `DO-DBT-06` — custom output connection
1. `DO-ERR-RAW-01` — HMDA error translation
1. `DO-ERR-LIFE-01` — reliability error translation
1. `DO-RES-02` — deep immutable result
1. `DO-ORCH-03` — false materialization 방지
1. `DO-RAW-02` — file count 의미 결정 후 구현

이 집합은 현재 리뷰의 주요 finding을 직접 regression barrier로 전환한다.

## Existing Test Adjustments

### `test_dbt_runner.py`

기존 subprocess monkeypatch test는 timeout, stderr와 artifact absence unit-adapter path로 유지할 수 있다. 단 custom target 연결을 검증하는 fake executable component test를 별도로 둔다.

### `test_incident_lifecycle.py`

현재 actual DuckDB, multiple detection, no-impact와 read-only test는 foundation에 적합하다. Error translation과 baseline shape decision만 추가 대상으로 본다.

### `test_dagster_definitions.py`

현재 skip materialization test는 기존 behavior characterization이다. Contract를 표준 pipeline always-run으로 결정하면 이 test는 삭제 또는 반전되어야 한다. 단순히 metadata expectation만 수정해서 false materialization을 남기면 안 된다.

## Exit Criteria

Test foundation의 첫 단계는 다음 조건을 모두 만족할 때 완료된다.

- P1 finding마다 실패를 재현하는 독립 oracle이 있다.
- fake harness가 production algorithm을 복제하지 않는다.
- focused domain suite가 일반 개발 loop에서 실행 가능한 비용이다.
- decision이 필요한 항목을 test가 임의로 확정하지 않는다.
- 새 test가 production defect, spec gap과 environment failure를 구분한다.
- deep review trigger가 contract change로 좁혀진다.
