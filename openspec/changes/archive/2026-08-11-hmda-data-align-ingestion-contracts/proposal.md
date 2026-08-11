---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: HMDA Data Ingestion Contract Alignment
description: qualified Bronze target schema 생성과 CSV parse policy ownership을 HMDA domain에 정렬한다.
tags:
  - "domain:hmda-data"
  - "capability:ingestion"
  - "parse-contract"
---

> [!NOTE]
> HMDA loader는 public `table_name`의 schema를 생성하고, ingestion과 EDA는 하나의 HMDA CSV parse option contract를 사용한다. generic DuckDB helper와 EDA의 read-only boundary는 유지한다.

## Overview

| Why | What | Capabilities |
| --- | --- | --- |
| custom schema target failure와 CSV parse policy drift | qualified table schema 보장 및 shared parse contract | `hmda-data-ingestion`, `hmda-data-eda-descriptive-evidence` |

## Why

현재 full/partition loader는 custom qualified `table_name`을 받지만 `raw` schema만 생성한다. 또한 CSV reader option이 ingestion SQL과 EDA evidence/SQL에 복제되어 한 경로의 parse semantics가 다른 경로와 drift할 수 있다.

## What Changes

- **Modify:** qualified HMDA target의 schema를 table name에서 파생해 생성
- **Modify:** ingestion과 EDA가 shared HMDA CSV parse option contract를 사용

## Boundaries

| In Scope | Out of Scope |
| --- | --- |
| full/partition custom schema target, CSV reader option contract | data platform generic schema helper, Parquet reader, EDA metric logic |

## Capabilities

### Modified Capabilities

#### `hmda-data-ingestion`

- public qualified Bronze target과 CSV source reader 계약을 정렬한다.

#### `hmda-data-eda-descriptive-evidence`

- EDA evidence가 실제 HMDA CSV reader option을 반영한다.

## Impact

| Area | Impact |
| --- | --- |
| Code / Systems | HMDA ingestion, EDA analysis, component tests |
| Data / Contracts | qualified target schema 생성과 shared CSV null/header/sample policy |
