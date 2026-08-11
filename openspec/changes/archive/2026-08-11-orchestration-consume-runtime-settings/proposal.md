---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Orchestration Runtime Settings Consumption
description: Dagster resource가 Data Operations의 canonical runtime request를 소비하도록 변경한다.
tags:
  - "domain:orchestration"
  - "capability:pipeline"
  - "configuration"
---

> [!NOTE]
> `DataOperationsResource`는 operational default를 직접 보유하지 않고 Data Operations의 environment-backed request를 시작점으로 사용한다. 명시적인 Dagster resource config만 그 request를 override한다.

## Overview

| Why | What | Capabilities |
| --- | --- | --- |
| Dagster resource의 중복 default가 pipeline configuration drift를 유발 | canonical request를 소비하는 adapter로 전환 | `orchestration-pipeline` |

## Why

기본 `Definitions`는 literal default를 가진 `DataOperationsResource()`를 등록한다. Data Operations의 환경 기반 request가 존재해도 이 resource가 직접 request를 생성하면 environment override는 pipeline에 반영되지 않는다.

## What Changes

- **Modify:** `DataOperationsResource`가 environment-derived request를 생성한 뒤 명시된 Dagster config만 적용하도록 변경

## Boundaries

| In Scope | Out of Scope |
| --- | --- |
| database path, source root, source year, source file, dbt flag의 adapter override | pipeline graph, asset 순서, dbt profile fallback, settings key 추가 |

## Capabilities

### Modified Capabilities

#### `orchestration-pipeline`

- 기본 pipeline은 Data Operations runtime settings를 소비해야 한다.

## Impact

| Area | Impact |
| --- | --- |
| Code / Systems | Dagster resource와 orchestration tests |
| Operations / Dependencies | 기본 resource가 `PROJECT_PIVOT_*` environment override를 반영 |
