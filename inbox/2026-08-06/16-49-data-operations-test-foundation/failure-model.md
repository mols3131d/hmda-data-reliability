---
title: Data Operations Failure Model
description: public boundary에서 방지할 실패를 trigger, damage와 detection boundary로 정의한다.
tags:
  - data-operations
  - failure-model
  - testing
---

# Failure Model

## Purpose

Test case를 늘리기 전에 방지할 damage를 정의한다. 이 문서는 test 구현이 아니라 failure와 invariant의 source of truth다.

## Failure Classes

| ID | Failure | Trigger | Observable damage | Detection boundary |
| --- | --- | --- | --- | --- |
| FM-01 | Artifact location divergence | configured target과 dbt output이 다름 | 정상 build가 실패하거나 잘못된 artifact를 소비 | fake process + filesystem |
| FM-02 | Stale artifact acceptance | 새 build가 artifact를 만들지 않음 | 실패 실행이 성공으로 보고 | filesystem component |
| FM-03 | Unusable artifact accepted | malformed 또는 필수 구조 누락 | lifecycle에서 늦게 실패 | contract decision 후 component |
| FM-04 | Dependency error leakage | HMDA, reliability 또는 DuckDB failure | caller가 하위 taxonomy에 결합 | public stage component |
| FM-05 | Error context loss | translation에서 cause/context 폐기 | diagnosis와 retry 판단 저하 | exception chain assertion |
| FM-06 | Misleading file count | 일부 partition만 적재 | metadata가 실행 범위를 과장 | real files + DuckDB |
| FM-07 | False materialization | dbt 미실행 상태에서 result 반환 | stale asset이 새로 갱신된 것처럼 기록 | Dagster event stream |
| FM-08 | Orchestration control leakage | shared request에 skip control 포함 | reusable stage contract와 caller control 결합 | request/API contract |
| FM-09 | Nested result mutation | frozen model 내부 list 변경 | 실행 evidence가 사후 변경 | unit mutation |
| FM-10 | Baseline shape mismatch | profile column set이 다름 | false positive 또는 비교 누락 | decision 후 lifecycle component |
| FM-11 | Read-only boundary regression | lifecycle에 write path 연결 | 승인 없는 data/file 변경 | DuckDB + filesystem invariant |
| FM-12 | Partial analysis ambiguity | incident 하나의 분석 실패 | 부분 결과 또는 원인 불명확 | policy decision 후 component |

## Damage Types

| Type | Examples | Preferred oracle |
| --- | --- | --- |
| False success | stale artifact, false materialization | persisted state, event absence |
| False failure | artifact target divergence | actual process output |
| Contract leakage | dependency error, orchestration flag | public API observation |
| Evidence corruption | mutable result, misleading count | immutable value, provenance |

## Invariants

1. 성공한 dbt result는 이번 invocation이 생성한 artifact를 가리킨다.
1. 예상 가능한 operational failure는 안정적인 application error로 관찰된다.
1. Materialization event는 asset이 실제로 materialize된 경우에만 존재한다.
1. Result와 metadata는 같은 실행 범위를 설명한다.
1. Evidence result는 caller가 사후 변경할 수 없다.
1. Incident lifecycle은 target partition과 filesystem을 변경하지 않는다.
1. 여러 incident 요약은 detection order를 유지하며 중복만 제거한다.

## Testability

| State | Action |
| --- | --- |
| Contract confirmed, risk reachable | regression test |
| Contract unclear | decision or OpenSpec first |
| Lower domain already proves the same behavior | do not duplicate |
| High cost, low impact | targeted review or optional validation |
| Environment-specific | separate validation with stated limits |

## First Slice

첫 cycle은 `FM-01`, `04`, `05`, `06`, `07`, `09`에 집중한다. `FM-02`, `11`은 기존 test를 유지하고, `FM-03`, `10`, `12`는 contract 결정 전까지 보류한다.
