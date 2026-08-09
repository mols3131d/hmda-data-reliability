---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Data Operations Runtime Settings Centralization
description: Data Operations의 실행 기본값과 environment override를 하나의 request contract로 정리한다.
tags:
  - "domain:data-operations"
  - "capability:stage-execution"
  - "configuration"
---

> [!NOTE]
> `DataOperationRequest`가 로컬 pipeline 실행 설정의 canonical owner가 되도록 environment 입력을 해석한다. 이 Change는 domain caller가 재사용할 typed request factory를 제공하며, Dagster의 factory 소비는 orchestration Change에서 처리한다.

## Overview

| Why | What | Capabilities |
| --- | --- | --- |
| 환경 설정과 실행 request의 단절 및 중복 기본값 drift 위험 | environment 기반 request factory 추가 | `data-operations-stage-execution` |

## Why

현재 `.env.example`은 pipeline의 DuckDB path와 HMDA source root를 노출하지만, `DataOperationRequest`는 해당 값을 읽지 않는다. 이로 인해 운영자가 environment를 수정해도 application 실행이 반영하지 않을 수 있다.

## What Changes

- **Add:** environment에서 database path와 source root를 읽어 `DataOperationRequest`를 만드는 공개 factory
- **Modify:** `DataOperationRequest`의 기본 실행 설정을 factory와 orchestration adapter가 공유하도록 contract 확장

## Boundaries

| In Scope | Out of Scope |
| --- | --- |
| database path, source root, source year의 environment-to-request 변환 | dbt profile의 fallback 제거, HMDA ingestion table schema, Dagster resource 변경 |
| 유효하지 않은 source year의 명시적 실패 | artifact/report/API 설정의 새 소비 경로 |

## Capabilities

### Modified Capabilities

#### `data-operations-stage-execution`

- 실행 caller는 environment override를 반영한 공통 request를 얻을 수 있어야 한다.

## Impact

| Area | Impact |
| --- | --- |
| Code / Systems | request module과 public export, unit tests |
| Interfaces / APIs | `DataOperationRequest` 생성 factory 추가 |
| Operations / Dependencies | `PROJECT_PIVOT_DUCKDB_PATH`, `PROJECT_PIVOT_SOURCE_ROOT`, 선택적 source year contract 명확화 |
