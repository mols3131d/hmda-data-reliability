---
type: openspec-spec-driven-tdd-spec
category: spec
title: hmda-data-ingestion
description: Partition replacement가 content와 expected max ingested_at을 하나의 transaction에서 검증하도록 확장한다.
tags:
  - "domain:reliability"
  - "capability:hmda-data-ingestion"
  - "freshness-delay"
---

## ADDED Requirements

### Requirement: Serialized freshness-state replacement

시스템은 caller가 expected current content identity와 expected `max(ingested_at)`을 함께 제공하면 partition replacement transaction 안에서 mutation 전에 actual content와 temporal state를 모두 비교해야 한다(SHALL). 어느 하나라도 다르면 partition을 변경하지 않고 stale-state failure로 종료해야 한다(SHALL). Expected temporal state가 제공되지 않은 content-only caller의 기존 replacement semantics는 유지해야 한다(MUST).

#### Scenario: Matching content and temporal state

- **GIVEN** expected content identity와 expected `max(ingested_at)`이 actual target과 모두 일치할 때
- **WHEN** partition replacement를 실행할 때
- **THEN** 두 state 확인과 replacement는 local concurrent writer가 끼어들 수 없는 하나의 transaction에서 완료되어야 한다.

#### Scenario: Temporal-only target drift

- **GIVEN** target content identity는 expected state와 같지만 `max(ingested_at)`이 다를 때
- **WHEN** partition replacement를 실행할 때
- **THEN** target partition을 변경하지 않고 stale-state failure로 종료해야 한다.

#### Scenario: Content-only replacement compatibility

- **WHEN** caller가 expected content identity만 제공하고 temporal state는 제공하지 않을 때
- **THEN** 기존 content compare-and-replace 동작을 유지해야 한다.

### Requirement: Metadata-preserving partition candidate

시스템은 caller가 provenance 보존을 명시한 partition candidate를 적용할 때 candidate의 `source_file`, `source_file_name`, `source_year`와 `ingested_at`을 재계산하지 않고 보존해야 한다(SHALL). 필요한 Bronze provenance가 없거나 target schema와 호환되지 않는 candidate는 target mutation 전에 거부해야 한다(SHALL).

#### Scenario: Approved Bronze candidate metadata

- **GIVEN** 유효한 Bronze provenance와 expected freshness timestamp를 가진 staged candidate가 있을 때
- **WHEN** metadata-preserving partition replacement를 실행할 때
- **THEN** target의 `max(ingested_at)`은 staged candidate의 approved timestamp와 일치해야 한다.

#### Scenario: Missing candidate provenance

- **WHEN** metadata-preserving candidate에 필요한 Bronze provenance가 없을 때
- **THEN** target partition을 변경하지 않고 candidate validation failure로 종료해야 한다.
