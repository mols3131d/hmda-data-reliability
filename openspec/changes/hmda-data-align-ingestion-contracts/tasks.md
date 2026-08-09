---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: HMDA Data Ingestion Contract Alignment
description: Custom target schema와 shared CSV reader semantics를 TDD로 구현한다.
tasks_completed: 6
tasks_total: 6
tags:
  - "domain:hmda-data"
  - "capability:ingestion"
  - "parse-contract"
---

> [!NOTE]
> custom schema load와 reader option equality를 먼저 test로 고정한다. 다음으로 table schema helper와 shared CSV option renderer를 도입하고 HMDA component suites로 검증한다.

## Tasks

### 1. Qualified target schema

- [x] 1.1 **RED** — full 및 partition load의 custom schema target component test를 추가한다.
  - **Covers:** `Custom schema full load`, `Custom schema partition load`
  - **Done when:** 새 DB에서 target schema missing failure가 재현된다.

- [x] 1.2 **GREEN** — target table name에서 schema를 해석해 full/partition loader가 생성하도록 구현한다.
  - **Done when:** 두 component test가 통과한다.

### 2. CSV parse contract

- [x] 2.1 **RED** — ingestion reader SQL과 EDA evidence가 같은 CSV options를 보고하는 test를 추가한다.
  - **Covers:** `Ingestion and EDA CSV semantics`
  - **Done when:** 현재 독립 literal 때문에 shared contract import가 실패한다.

- [x] 2.2 **GREEN** — shared option mapping과 reader SQL helper를 구현하고 ingestion·EDA에 적용한다.
  - **Done when:** reader semantics test와 기존 EDA test가 통과한다.

### 3. Verification

- [x] 3.1 관련 ingestion 및 EDA test suites를 실행한다.
  - **Done when:** custom schema와 existing HMDA behavior가 함께 통과한다.

- [x] 3.2 strict OpenSpec validation과 independent implementation review를 완료한다.
  - **Done when:** finding이 없고 validation evidence가 기록된다.
