---
type: openspec-spec-driven-tdd-spec
category: spec
title: ingestion
description: qualified target schema와 shared HMDA CSV reader contract를 정의한다.
tags:
  - "domain:hmda-data"
  - "capability:ingestion"
  - "parse-contract"
---

## MODIFIED Requirements

### Requirement: Bronze load with provenance

시스템은 유효한 원천 행을 configured qualified Bronze table에 적재하고 `source_file`, `source_file_name`, `source_year`, `ingested_at` provenance를 함께 보존해야 한다(SHALL). 시스템은 target table의 schema가 없으면 table name에서 schema를 도출하여 생성해야 한다(SHALL).

#### Scenario: Full source load

- **WHEN** 유효한 source set을 전체 적재할 때
- **THEN** Bronze dataset에는 원천 행과 provenance가 함께 저장되어야 한다.
- **AND** 같은 입력을 다시 전체 적재해도 행이 누적되어서는 안 된다.

#### Scenario: Custom schema full load

- **GIVEN** target schema가 없는 새 DuckDB database와 `bronze.hmda_loans` target이 주어졌을 때
- **WHEN** caller가 full load를 실행할 때
- **THEN** loader는 `bronze` schema와 configured table을 생성하고 적재 행 수를 반환해야 한다.

#### Scenario: Unsupported multipart target

- **GIVEN** three-part 이상의 target table identifier가 주어졌을 때
- **WHEN** caller가 full 또는 partition load를 실행할 때
- **THEN** loader는 schema를 생성하거나 적재하기 전에 HMDA data load failure로 종료해야 한다.

### Requirement: Partition replacement

시스템은 `source_year`와 optional `source_file`로 대상 partition을 선택해 해당 범위만 교체할 수 있어야 한다(SHALL). Partition 교체가 완료되지 못하면 기존 partition을 부분 삭제 또는 새 입력과 혼합된 상태로 남겨서는 안 된다(MUST NOT). 시스템은 target table의 schema가 없으면 table name에서 schema를 도출하여 생성해야 한다(SHALL).

#### Scenario: Year partition reload

- **WHEN** 같은 `source_year` partition을 동일 입력으로 반복 적재할 때
- **THEN** 대상 partition의 최종 행 집합과 행 수는 한 번 적재한 결과와 같아야 한다.

#### Scenario: Custom schema partition load

- **GIVEN** target schema가 없는 새 DuckDB database와 `bronze.hmda_loans` target이 주어졌을 때
- **WHEN** caller가 partition load를 실행할 때
- **THEN** loader는 `bronze` schema와 configured table을 생성하고 해당 partition 행 수를 반환해야 한다.

## ADDED Requirements

### Requirement: Shared HMDA CSV parse contract

시스템은 HMDA CSV reader의 header, null string, sample size option을 domain-owned contract 하나로 정의해야 한다(SHALL). ingestion과 EDA는 해당 contract를 사용해야 하며 서로 다른 CSV parse option을 독립적으로 정의해서는 안 된다(MUST NOT).

#### Scenario: Ingestion and EDA CSV semantics

- **WHEN** ingestion SQL과 EDA evidence가 HMDA CSV parse option을 사용하거나 보고할 때
- **THEN** header, null string, sample size 값은 같은 domain contract와 일치해야 한다.
