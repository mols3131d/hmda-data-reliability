---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: "Reconcile HMDA EDA core contract"
description: "Align six-core EDA behavior, Python/YAML exploration, static visualizations, evidence, and readiness after the deep review."
tags:
  - "domain:hmda-data"
  - "subdomain:eda"
  - "capability:hmda-eda-baseline"
  - "contract-reconciliation"
---

> [!NOTE]
> HMDA ingestion의 7-column source contract와 6-core EDA contract를 분리해 정렬하고, Marimo 노트북 대신 에이전트 친화적인 Python/YAML 탐색과 정적 이미지/HTML 시각화 자료를 제공하여 Foundation EDA gate의 근거를 복구한다.

## Overview

| Why | What | Capabilities |
| --- | --- | --- |
| Deep review에서 runtime, evidence, readiness 불일치가 확인됨 및 에이전트 환경에 둔중한 Marimo 노트북 교체 필요성 발생 | 6-core EDA contract, complete-key grain, end-to-end duration, Python/YAML EDA 탐색 및 정적 시각화(PNG/HTML), evidence 및 readiness를 정렬 | `hmda-eda-baseline` |

> [!IMPORTANT]
> `county_code`는 HMDA ingestion source contract에는 계속 필요하지만 EDA의 type compatibility·null baseline 대상은 아니다.

## Why

현재 EDA runtime은 `county_code`까지 포함한 7개 컬럼을 직접 검증하는 반면, scope-reduction change는 6-core EDA contract를 정의한다. 또한 actual-source Markdown과 JSON의 값이 달라 Foundation readiness 근거가 될 수 없다.
아울러 에이전트 기반 개발/탐색 환경에서는 반응형 UI 노트북(Marimo)보다 유연한 일반 Python API, 구조화된 YAML(`yml`) 에비던스 반환, 정적 이미지(PNG/SVG) 또는 독립 HTML 시각화 자료가 훨씬 효율적이다.

## What Changes

- **Modify:** runtime과 tests를 6-core EDA type/null contract 및 complete-key grain contract에 맞춘다.
- **Modify:** duration을 전체 EDA 실행 시간으로 측정하고 freshness 잔여 query를 제거한다.
- **Remove:** Marimo 노트북(`notebooks/eda_mo.py`) 및 마리모 관련 테스트(`test_eda_notebook.py`)를 완전 제거한다.
- **Add:** 일반 Python 환경에서 EDA 결과를 에이전트 친화적인 YAML(`yml`) 형식으로 반환하는 탐색 인터페이스를 추가하고, 필요시 정적 이미지 파일(PNG) 또는 독립 실행형 HTML 파일 형태의 시각화 자료를 생성하는 기능을 추가한다.
- **Modify:** controlled actual-source run에서 JSON과 Markdown evidence를 함께 생성하고 readiness가 생성된 evidence 상태를 정확히 표현하게 한다.

## Boundaries

| In Scope | Out of Scope |
| --- | --- |
| EDA runtime, tests, Python/YAML exploration, static image/HTML charts, reference evidence, readiness, canonical EDA spec | HMDA ingestion의 source required-column contract 변경 |
| 6-core descriptive evidence와 complete-key grain observation | 대용량 OOM budget 또는 memory workload 복구 |
| Marimo 노트북 및 Marimo 관련 의존성 제거 | 지속적 performance SLO 또는 production monitoring |

## Capabilities

### Modified Capabilities

#### `hmda-eda-baseline`

- 6-core schema and null metrics, complete-key grain, duration, Python/YAML exploration, static image/HTML visualization, actual-source evidence 및 readiness-gate behavior를 같은 contract로 정렬한다.

## Impact

| Area | Impact |
| --- | --- |
| Code / Systems | DuckDB aggregate behavior, python EDA exploration, YAML exporter, chart renderer 및 targeted test assertions가 바뀐다. `notebooks/eda_mo.py` 및 관련 테스트는 삭제된다. |
| Data / Contracts | EDA required evidence에서 `county_code`가 제외되고 complete-key grain의 분모가 명시되며 탐색 결과가 YAML 형식으로 표현될 수 있다. |
| Interfaces / APIs | `analyze_hmda_csv` evidence의 schema와 null metrics가 6-core contract로 바뀐다. Python EDA 탐색 결과를 YAML 또는 정적 시각화 파일(PNG/HTML)로 내보내는 인터페이스가 추가된다. |
| Operations / Dependencies | Actual-source evidence는 explicit script 실행으로 갱신하며, readiness는 이 실행 전 blocked를 유지한다. Marimo 의존성은 제외되거나 무력화된다. |
