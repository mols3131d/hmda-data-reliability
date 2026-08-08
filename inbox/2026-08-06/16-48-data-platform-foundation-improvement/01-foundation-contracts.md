---
title: Data Platform Foundation Contracts
description: data_platform foundation이 보장해야 할 resource, transformation, analytics와 evidence 계약을 정의한다.
tags:
  - data-platform
  - foundation
  - invariants
---

# Foundation Contracts

## Principle

Foundation contract는 구현 방식이 아니라 상위 기능이 의존할 수 있는 관찰 가능한 성질이다. 이 번들은 직접 연결된 실행 경계까지 다루지만, contract의 canonical owner는 기존 domain boundary를 유지한다. 재현 가능한 review finding은 다음 경로로 종료한다.

```text
finding → decision → contract → test → owning artifact
```

Decision이 없는 의미를 test가 임의로 확정해서는 안 된다.

## Contract Catalog

### Resource

| ID | Owner | Contract | Oracle | State |
| --- | --- | --- | --- | --- |
| DP-R1 | `data_operations` | 모든 execution boundary는 하나의 resolved DuckDB path를 사용한다. | 같은 absolute file에 raw, staging, mart 존재 | Missing |
| DP-R2 | `data_platform` | Read-only 연결은 persistent state를 만들거나 변경하지 않는다. | 사전·사후 file과 table state 동일 | Partial |
| DP-R3 | `data_platform` | Cleanup은 명시적으로 소유한 temporary DB만 삭제한다. | 기존 DB 보존, owned temp 삭제 | Missing |
| DP-R4 | `data_platform` | 정상·예외 종료 모두 connection을 닫고 원래 error 의미를 보존한다. | 재연결 성공과 original exception | Missing |

### Transformation

| ID | Owner | Contract | Oracle | State |
| --- | --- | --- | --- | --- |
| DP-S1 | `data_platform` | Staging row count는 raw row count와 같다. | `count(raw) == count(staging)` | Missing |
| DP-S2 | `data_platform` | 허용된 regional Null은 staging에 남고 mart grain에서만 제외된다. | staging 존재, mart 부재 | Partial |
| DP-S3 | `data_platform` | Invalid `loan_amount`, `income`은 row 삭제가 아니라 Null cast로 나타난다. | malformed fixture의 field만 Null | Missing |
| DP-S4 | `data_platform` | Invalid required code는 build failure로 관찰된다. | dbt command 또는 unit test failure | Missing |

### Analytics And Evidence

| ID | Owner | Contract | Oracle | State |
| --- | --- | --- | --- | --- |
| DP-M1 | `data_platform` | Mart grain은 `activity_year + state_code + loan_purpose`로 유일하다. | `not_null`, `unique` data tests | Covered |
| DP-M2 | `data_platform` | Metric population과 action mapping은 canonical spec과 일치한다. | action codes 1–8 exact output | Blocked |
| DP-M3 | `data_platform` | `approval_rate`는 정의된 numerator, denominator와 zero policy를 따른다. | hand-calculated fixture | Blocked |
| DP-E1 | `data_platform` | 동일 raw와 command의 반복 build는 동일 mart state를 만든다. | first/second exact rows | Covered |
| DP-E2 | `data_platform` | Lineage는 raw → staging → mart를 유지한다. | manifest dependency graph | Covered |
| DP-E3 | `data_operations` | Artifact는 현재 실행에서 새로 생성되고 성공 상태를 나타낸다. | stale 제거, existence, run result status | Partial |

`Blocked`는 구현 부족이 아니라 인간 결정이 필요함을 뜻한다.

## Review Finding Handoff

| Finding | Contract | Required handoff |
| --- | --- | --- |
| F1: split database path | DP-R1 | path owner 결정, default-flow integration test |
| F2: unsafe cleanup | DP-R2–R4 | ownership API 결정, component regression tests |
| F3: undefined metrics | DP-M2–M3 | canonical metric spec, dbt unit tests |
| F4: staging false green | DP-S1–S4 | direct staging assertions |

## Priority

| Priority | Contracts | Reason |
| --- | --- | --- |
| P0 | DP-R1, DP-R3 | 잘못된 DB 또는 data deletion은 다른 검증도 무효화한다. |
| P1 | DP-S1–S4 | Staging은 downstream 보존 경계다. |
| P1 | DP-M2–M3 | 의미가 없으면 mart correctness를 판정할 수 없다. |
| P2 | DP-R2, DP-R4, DP-E3 | lifecycle과 evidence 신뢰성을 강화한다. |

## Completion Rule

Contract는 owner와 decision이 명확하고, independent oracle을 가진 executable check가 있을 때 완료된다. `Blocked` contract는 test가 아니라 canonical decision으로 먼저 해소한다. 전체 exit criteria는 [`README.md`](README.md)가 소유한다.
