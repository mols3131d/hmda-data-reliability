---
title: Data Operations Failure Model
description: data_operations의 public boundary와 caller 연결에서 발생 가능한 실패를 trigger, observable damage와 검증 방법으로 구조화한다.
tags:
  - data-operations
  - failure-model
  - risk-analysis
  - testing
---

# Failure Model

## Purpose

심층 리뷰를 줄이려면 test case 목록보다 먼저 **어떤 실패를 방지하는지**가 안정적으로 정의되어야 한다. 이 문서는 내부 구현이 아니라 외부에서 관찰되는 damage를 중심으로 정리한다.

## Failure Classes

| ID | Failure | Trigger | Observable damage | Detection boundary |
| --- | --- | --- | --- | --- |
| FM-01 | Artifact location divergence | custom artifact path와 dbt default target이 다름 | dbt success 뒤 `DataOperationError`, 또는 잘못된 artifact 소비 | fake process + real filesystem |
| FM-02 | Stale artifact acceptance | 이전 artifact가 남은 상태에서 새 build가 artifact를 생성하지 않음 | 실패 실행이 성공으로 보고됨 | component filesystem test |
| FM-03 | Artifact existence without usability | 빈 파일·잘못된 JSON·필수 node 누락 | lifecycle impact analysis에서 늦게 실패 | contract decision 후 component test |
| FM-04 | Dependency error leakage | HMDA, reliability, DuckDB failure | caller가 하위 domain exception taxonomy에 결합 | public entry point component test |
| FM-05 | Error context loss | exception translation 중 원인과 context 폐기 | 원인 분석과 retry policy가 어려움 | `__cause__`와 safe context assertion |
| FM-06 | Discovery count reported as processed count | 여러 연도·파일 중 일부 partition만 적재 | Dagster metadata가 실제 작업 범위를 과장 | real fixture + result metadata |
| FM-07 | False materialization | `run_dbt_build=False`에서 `MaterializeResult` 반환 | stale Silver/Gold가 새 materialization처럼 보임 | Dagster event stream |
| FM-08 | Orchestration control leaks into stage request | shared request에 `run_dbt_build` 포함 | 직접 caller contract와 Dagster control가 결합 | request/public API contract test |
| FM-09 | Nested result mutation | frozen model의 list를 append/clear | logging과 이후 검증에서 실행 evidence 변경 | unit mutation test |
| FM-10 | Baseline shape mismatch | asset·partition은 같지만 profile column set이 다름 | null spike false positive 또는 비교 누락 | decision 후 lifecycle component test |
| FM-11 | Read-only boundary regression | lifecycle에 write/recovery/evaluation 연결 | 승인 없는 데이터 변경 또는 report 생성 | real DuckDB and filesystem invariant |
| FM-12 | Partial analysis loss | 여러 incident 중 하나의 impact/remediation 실패 | 일부 결과만 반환하거나 실패 원인 불명확 | explicit all-or-fail policy test |
| FM-13 | Custom table/path injection regression | request의 table/path 조합 변경 | 잘못된 table 접근, path confusion | validation + existing SQL boundary tests |
| FM-14 | Test false green by boundary replacement | mock이 artifact 생성·domain result까지 대신함 | 실제 adapter 연결 defect가 test에서 숨음 | harness design review |

## Damage Categories

### False success

가장 위험하다. 실패나 미실행 상태가 성공 또는 materialization으로 기록된다.

- stale artifact acceptance
- skipped dbt materialization
- metadata가 실제 처리 범위를 과장

이 부류의 oracle은 log나 call count가 아니라 persisted state와 event semantics여야 한다.

### False failure

정상 실행이 잘못된 configuration 연결 때문에 실패한다.

- custom artifact path와 실제 output divergence
- 유효한 dependency error가 잘못 번역되어 generic failure로 손실

### Contract leakage

Application boundary가 하위 domain 세부사항을 caller에게 노출한다.

- stage별 exception taxonomy 차이
- orchestration 전용 flag가 shared request에 포함

### Evidence corruption

한 번 생성된 실행 결과가 나중에 달라지거나 의미가 실제 상태와 다르다.

- nested list mutation
- discovery count를 processed count로 보고
- false materialization

## Invariants

다음 invariant는 implementation choice와 무관하게 유지할 가치가 높다.

1. 성공한 dbt result가 가리키는 artifact는 이번 invocation이 생성한 위치에 존재한다.
1. public stage의 예상 가능한 operational failure는 안정적인 application error로 관찰된다.
1. materialization event는 해당 asset이 실제로 materialize된 경우에만 존재한다.
1. result metadata의 이름과 값은 같은 실행 범위를 설명한다.
1. 반환된 evidence result는 caller가 사후 변경할 수 없다.
1. incident lifecycle은 target partition과 filesystem에 recovery/evaluation side effect를 만들지 않는다.
1. 여러 incident의 요약은 detection order를 유지하고 중복만 제거한다.

## Testability Filter

Failure model의 모든 항목을 당장 test로 만들지 않는다.

| Classification | Action |
| --- | --- |
| Contract가 확정되고 risk가 reachable | regression test를 만든다. |
| Contract가 모호함 | decision 또는 OpenSpec change를 먼저 만든다. |
| 하위 domain suite가 이미 동일 behavior를 충분히 보호 | `data_operations`에서 중복하지 않는다. |
| 실행 비용이 크고 영향이 낮음 | targeted review 또는 optional test로 남긴다. |
| 실제 environment만 검증 가능 | 별도 validation command와 제한을 기록한다. |

## Highest-Value Failure Set

첫 foundation iteration에서는 FM-01, FM-04, FM-05, FM-06, FM-07, FM-09를 대상으로 한다. FM-02와 FM-11은 기존 test가 상당 부분 보호하므로 유지·보강만 검토한다. FM-03, FM-10, FM-12는 contract 결정이 선행되어야 한다.
