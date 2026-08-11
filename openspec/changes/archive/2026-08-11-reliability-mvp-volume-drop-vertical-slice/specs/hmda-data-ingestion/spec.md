---
type: openspec-spec-driven-tdd-spec
category: spec
title: hmda-data-ingestion
description: Partition content identity와 serialized replacement 경계를 정의한다.
tags:
  - "domain:reliability"
  - "capability:hmda-data-ingestion"
  - "mvp"
  - "volume-drop"
---

## MODIFIED Requirements

### Requirement: Partition replacement

시스템은 `source_year`와 optional `source_file`로 대상 partition을 선택해 해당 범위만 교체할 수 있어야 한다(SHALL). Partition 교체가 완료되지 못하면 기존 partition을 부분 삭제 또는 새 입력과 혼합된 상태로 남겨서는 안 된다(MUST NOT). 시스템은 target table의 schema가 없으면 table name에서 schema를 도출하여 생성해야 한다(SHALL). Caller가 expected current content identity를 제공하면 시스템은 replacement transaction 안에서 mutation 전에 actual identity와 비교해야 하며 다르면 교체해서는 안 된다(SHALL).

#### Scenario: Year partition reload

- **WHEN** 같은 `source_year` partition을 동일 입력으로 반복 적재할 때
- **THEN** 대상 partition의 최종 행 집합과 행 수는 한 번 적재한 결과와 같아야 한다.

#### Scenario: File-scoped reload

- **WHEN** `source_file`이 지정된 partition 적재를 실행할 때
- **THEN** 지정된 파일 범위만 교체 대상이 되어야 한다.

#### Scenario: Failed partition replacement

- **WHEN** 기존 partition을 새 입력으로 교체하는 작업이 완료되기 전에 실패할 때
- **THEN** 기존 partition은 부분적으로 삭제되거나 새 입력과 혼합된 상태로 남아서는 안 된다.

#### Scenario: Custom schema partition load

- **GIVEN** target schema가 없는 새 DuckDB database와 `bronze.hmda_loans` target이 주어졌을 때
- **WHEN** caller가 partition load를 실행할 때
- **THEN** loader는 `bronze` schema와 configured table을 생성하고 해당 partition 행 수를 반환해야 한다.

#### Scenario: Serialized expected-state replacement

- **GIVEN** caller가 actual target과 일치하는 expected current content identity를 제공할 때
- **WHEN** partition replacement를 실행할 때
- **THEN** identity 확인과 replacement는 local concurrent writer가 끼어들 수 없는 경계에서 완료되어야 한다.

#### Scenario: Stale expected state

- **GIVEN** caller의 expected current content identity와 actual target이 다를 때
- **WHEN** partition replacement를 요청할 때
- **THEN** target partition을 변경하지 않고 stale-state failure로 종료해야 한다.

## ADDED Requirements

### Requirement: Stable partition content identity

시스템은 `table + source_year + optional source_file` 범위의 stable content identity를 계산할 수 있어야 한다(SHALL). Identity는 row order와 실행마다 달라지는 ingestion metadata에 독립적이어야 하고 duplicate row multiplicity를 보존해야 한다(SHALL).

#### Scenario: Equivalent partition content

- **GIVEN** 같은 logical row multiset이 다른 순서와 다른 volatile ingestion metadata로 저장되어 있을 때
- **WHEN** 같은 partition scope의 content identity를 계산할 때
- **THEN** 두 identity는 같아야 한다.

#### Scenario: Duplicate or value drift

- **WHEN** row value 또는 duplicate multiplicity가 다른 두 partition의 content identity를 계산할 때
- **THEN** 두 identity는 달라야 한다.
