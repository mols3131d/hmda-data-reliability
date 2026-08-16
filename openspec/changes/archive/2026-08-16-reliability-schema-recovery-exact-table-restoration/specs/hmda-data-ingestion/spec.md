---
type: openspec-spec-driven-tdd-spec
category: spec
title: hmda-data-ingestion
description: HMDA full-load와 partition replacement가 공통 DuckDB mutation lock에 참여하도록 직렬화 계약을 보강한다.
tags:
  - "domain:reliability"
  - "capability:hmda-data-ingestion"
  - "schema-drift"
---

## ADDED Requirements

### Requirement: Serialized managed Bronze mutation

시스템은 file-based DuckDB target에 대한 HMDA full-load와 partition replacement를 공통 database mutation lock 안에서 실행해야 한다(SHALL). Lock은 target을 처음 생성하거나 변경하기 전에 획득하고 full-load call 종료 또는 partition transaction의 commit/rollback까지 유지해야 한다(SHALL). Expected current identity가 있는 partition replacement는 lock 획득 후 actual identity를 다시 계산해야 한다(SHALL). 이 serialization은 full-load의 기존 validation-after-replacement failure semantics를 변경하지 않아야 한다(MUST NOT).

#### Scenario: Concurrent full-load writers

- **GIVEN** 두 full-load request가 같은 physical DuckDB file을 대상으로 할 때
- **WHEN** 첫 request가 target replacement를 실행 중일 때
- **THEN** 두 번째 request는 첫 full-load call이 성공 또는 실패로 종료되고 mutation lock이 해제될 때까지 target mutation을 시작해서는 안 된다.

#### Scenario: Concurrent expected-state partition replacement

- **GIVEN** 두 partition replacement가 같은 approved before identity를 사용하고 첫 request가 target을 변경했을 때
- **WHEN** 두 번째 request가 mutation lock을 획득할 때
- **THEN** 두 번째 request는 current identity를 다시 계산하고 stale-state failure로 target mutation 없이 종료해야 한다.

#### Scenario: Concurrent unrelated partition writer

- **GIVEN** 두 managed writer가 같은 database의 서로 다른 partition을 변경하려 할 때
- **WHEN** 한 writer가 mutation lock을 보유할 때
- **THEN** 다른 writer는 database-level lock이 해제된 뒤에 mutation을 진행해야 한다.

#### Scenario: Mutation lock failure

- **WHEN** HMDA ingestion이 target database mutation lock을 획득하지 못할 때
- **THEN** target table 또는 partition을 변경하지 않고 domain failure로 종료해야 한다.
