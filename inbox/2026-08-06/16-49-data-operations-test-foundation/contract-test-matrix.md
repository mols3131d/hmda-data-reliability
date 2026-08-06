---
title: Data Operations Contract Test Matrix
description: load-bearing contract를 scenario, independent oracle, level과 current coverage로 매핑한다.
tags:
  - data-operations
  - contract-matrix
  - test-design
---

# Contract Test Matrix

## Coverage

| State | Meaning |
| --- | --- |
| Protected | 현재 test가 실제 risk와 oracle을 직접 보호 |
| Partial | 일부 path만 보호하거나 boundary replacement가 있음 |
| Missing | contract는 합의됐지만 test가 없음 |
| Decision | behavior 결정이 먼저 필요 |

## Matrix

| ID | Contract | Scenario / Oracle | Level | Coverage |
| --- | --- | --- | --- | --- |
| DO-PUB-01 | Stage API only | coordinator와 CLI 부재 | unit | Protected |
| DO-RAW-01 | Partition result truth | persisted rows와 result count 일치 | component | Partial |
| DO-RAW-02 | File count semantics | selected fixture의 합의된 provenance | component | Decision |
| DO-ERR-RAW | Raw error boundary | public error, cause와 safe context | component | Missing |
| DO-DBT-01 | Artifact required | exit 0 + artifact 없음은 failure | component | Protected |
| DO-DBT-02 | Stale artifact rejected | stale 제거 후 새 artifact 없으면 failure | component | Protected |
| DO-DBT-03 | Process failures translated | timeout, startup, non-zero exit | component | Partial |
| DO-DBT-04 | Configured output connected | fake executable output과 result path 일치 | component | Missing |
| DO-DBT-05 | This-invocation artifact | invocation marker가 있는 새 artifact | component | Partial |
| DO-DBT-06 | Artifact usable | 합의한 minimum structure 검증 | component | Decision |
| DO-ERR-LIFE | Lifecycle error boundary | public error, cause와 safe context | component | Missing |
| DO-LIFE-01 | Actual current comparison | real DuckDB measurement와 detection | component | Protected |
| DO-LIFE-02 | Complete ordered analysis | 모든 detection 요약, 순서 보존, dedupe | component | Protected |
| DO-LIFE-03 | No-incident short circuit | 빈 result와 impact 미실행 | component | Protected |
| DO-LIFE-04 | Baseline identity | asset/partition mismatch rejection | component | Protected |
| DO-LIFE-05 | Baseline shape | reject 또는 defined comparison | component | Decision |
| DO-LIFE-06 | Read-only lifecycle | rows와 filesystem 불변 | component | Protected |
| DO-RES-01 | Deep immutable results | nested collection mutation 불가 | unit | Missing |
| DO-ORCH-01 | Standard graph and order | raw → dbt dependency와 execution | integration | Partial |
| DO-ORCH-02 | No false materialization | raw-only selection에는 dbt event 없음 | integration | Decision |
| DO-ORCH-03 | Metadata truth | result, actual output과 event metadata 일치 | integration | Decision |

## First Foundation Slice

| Order | Contract | Why |
| ---: | --- | --- |
| 1 | `DO-DBT-04` | reachable false failure이며 현재 mock이 숨긴다. |
| 2 | `DO-ERR-RAW`, `DO-ERR-LIFE` | public boundary를 하위 taxonomy에서 분리한다. |
| 3 | `DO-ORCH-02` | D2 결정 후 false success와 stale-state 오해를 막는다. |
| 4 | `DO-RES-01` | evidence mutation을 저비용으로 차단한다. |
| 5 | `DO-RAW-02` | 의미 결정 후 metadata truth를 고정한다. |

## Existing Test Treatment

- `test_dbt_runner.py`: timeout, stderr, stale artifact test는 유지하고 fake executable adapter test를 추가한다.
- `test_incident_lifecycle.py`: actual DuckDB, multiple detection, short circuit와 read-only test를 유지한다.
- `test_dagster_definitions.py`: 현재 skip materialization test는 characterization이다. D2 결정 후 standard job의 dbt 실행 또는 raw-only selection의 event absence를 검증한다.

## Exit Criteria

- P1 risk마다 독립적인 failure oracle이 있다.
- Harness가 production algorithm을 복제하지 않는다.
- Focused suite가 일반 개발 loop에서 실행 가능하다.
- Decision 항목을 test가 임의로 확정하지 않는다.
- Failure를 production defect, spec gap과 environment failure로 구분한다.
