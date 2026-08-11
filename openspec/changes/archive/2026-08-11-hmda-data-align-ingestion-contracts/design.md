---
type: openspec-spec-driven-tdd-design
category: design
title: HMDA Data Ingestion Contract Alignment
description: HMDA-owned table schema parsing과 CSV option rendering을 shared private module로 둔다.
tags:
  - "domain:hmda-data"
  - "capability:ingestion"
  - "parse-contract"
---

> [!NOTE]
> ingestion package의 private contract module이 default `raw` 또는 qualified table의 schema component를 추출하고, CSV option mapping에서 ingestion reader SQL과 EDA relation SQL을 렌더링한다. EDA는 read-only query와 evidence shape를 유지한다.

## Context

- **Current State:** full/partition loader는 `ensure_schema()`의 `raw` default를 사용하고, ingestion과 EDA가 CSV option literal을 각각 유지한다.
- **Constraints:** table identifiers는 existing `qualify_table_name()`을 계속 사용하고, SQL values는 static domain constants로 렌더링한다.
- **Dependencies:** `ensure_schema()`는 generic schema creation, DuckDB parameter binding은 source path 전달을 담당한다.

## Goals / Non-Goals

| Goals | Non-Goals |
| --- | --- |
| configured qualified table을 새 DB에서 적재 가능하게 함 | unqualified table naming policy 변경 |
| ingestion과 EDA의 CSV semantics 단일화 | Parquet reader 또는 EDA aggregate 변경 |

## Architecture

`ingestion._source_query`가 `HMDA_CSV_OPTIONS`, `csv_reader_sql()` 및 `table_schema_name()`을 제공한다. 두 loader는 schema helper로 `ensure_schema()`를 호출한다. EDA는 같은 option mapping과 SQL helper를 provenance `filename` option 없이 사용해 reader relation을 만들고 evidence에는 mapping의 독립적인 JSON-safe copy를 반환한다.

### Boundaries

| Boundary | Owns | Does Not Own |
| --- | --- | --- |
| HMDA ingestion contract | table schema parsing, CSV reader semantics | generic DuckDB schema creation |
| EDA | read-only execution 및 evidence | 별도의 CSV option authority |

## Decisions

### D1. table schema는 첫 qualified component로 해석

- **Decision** - `schema.table` target은 schema component를 생성하고 unqualified target은 `raw`로 해석한다. three-part 이상의 identifier는 거부한다.
- **Rationale** - existing public default와 single-database DuckDB schema ownership을 유지한다.
- **Trade-off** - catalog-qualified target은 현재 loader contract 밖이며 별도 capability가 필요하다.

### D2. CSV options은 mapping과 SQL helper를 함께 소유

- **Decision** - JSON-safe mapping을 evidence source로 사용하고 두 reader SQL은 같은 mapping에서 생성한다.
- **Rationale** - evidence와 executable SQL이 같은 option authority를 공유한다.
- **Trade-off** - EDA가 ingestion private module에 의존하지만 동일 HMDA source contract ownership 안이다.

## Testability

| Boundary / Behavior | Test Strategy | Evidence |
| --- | --- | --- |
| custom schema full/partition load | component | configured schema/table exists and row count matches |
| shared CSV options | unit/component | ingestion SQL과 EDA evidence mapping equality |

- **TDD Boundary:** loader public API와 CSV reader helper.
- **Failure Signals:** missing custom schema, reader option drift.

## Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| unsupported multipart target | 잘못된 schema 생성 또는 unclear failure | table schema parser에서 명시적으로 거부 |
