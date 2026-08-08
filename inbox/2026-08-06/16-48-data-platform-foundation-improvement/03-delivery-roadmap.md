---
title: Data Platform Foundation Delivery Roadmap
description: foundation 개선을 독립적인 결정, test, 구현과 검증 단위로 나눈다.
tags:
  - data-platform
  - roadmap
  - openspec
---

# Delivery Roadmap

## Strategy

“Test 강화”를 하나의 큰 change로 만들지 않는다. 안전성 계약과 분석 의미를 분리해야 review와 rollback이 작아진다.

| Change | Owns | Excludes |
| --- | --- | --- |
| `data-platform-database-resource-contracts` | path identity, connection lifecycle, cleanup ownership | mart semantics |
| `dbt-analytics-contract-hardening` | staging preservation, metric semantics, dbt tests | generic runner refactor |

Test는 사후 보강이 아니라 각 change의 acceptance evidence다.

## Workstream A: Database Resource Contracts

### Decide

- 상대 path의 기준점과 resolution owner
- result model에 resolved path를 반환할지
- cleanup 제거, 제한 또는 explicit ownership API
- cleanup failure와 body exception의 우선순위

### Protect

현재 위험을 재현하는 red test를 만든다.

- default flow는 하나의 DB 사용
- CWD가 바뀌어도 identity 유지
- 기존 DB는 cleanup으로 삭제되지 않음
- read-only + cleanup은 생성 전에 거부
- body exception 후 lock과 error 의미 보존

### Implement And Validate

예상 범위:

- `data_operations/request.py`, `runner.py`
- `data_platform/duckdb.py`
- 관련 domain 문서와 OpenSpec
- `tests/data_platform/`, `tests/data_operations/`, DB identity integration

완료 조건:

- subprocess 전에 absolute identity가 확정된다.
- default flow가 동일 DB를 증명한다.
- persistent DB deletion path가 차단된다.
- focused와 관련 domain suite 결과가 기록된다.

## Workstream B: Analytics Contracts

### Decide And Specify

- `application_count` population
- approval, denial, preapproval, purchased-loan mapping
- approval-rate denominator와 zero policy
- 기존 mart column 호환성

결정은 구현 전에 `dbt-analytics-foundation` spec에 반영한다. SQL을 읽지 않고 expected output을 계산할 수 있어야 한다.

### Protect

- action codes 1–8 exact-output dbt unit test
- malformed numeric staging unit test
- raw/staging row conservation
- Null grain의 staging 보존과 mart 제외
- metric bounds data tests

### Implement And Validate

완료 조건:

- dbt unit test가 SQL 의미를 판정한다.
- data test가 materialized invariant를 판정한다.
- integration이 wiring, artifact, lineage와 idempotency를 판정한다.
- fixture와 test 책임이 필요할 때 design 문서에 연결된다.

## Adoption

두 workstream이 완료된 뒤 review policy를 적용한다.

1. 기존 F1–F4 obligation을 spec과 test로 이전한다.
1. 다음 세 routine 변경에서 focused review를 dogfood한다.
1. 놓친 defect와 불필요한 deep trigger를 기록한다.
1. 반복 가능성이 확인되면 source review와 inbox bundle을 정리한다.

## Delivery Gate

각 workstream은 자체 completion condition과 실제 validation evidence를 충족해야 한다. Bundle 전체 완료 여부는 [`README.md`](README.md)의 exit criteria로 판정한다.
