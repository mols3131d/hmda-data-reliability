---
type: openspec-spec-driven-tdd-spec
category: spec
title: reliability-recovery-backfill
description: Exact approved clean partition candidate로 null-spike content를 복원하는 기존 backfill 적용 범위를 정의한다.
tags:
  - "domain:reliability"
  - "capability:reliability-recovery-backfill"
  - "null-spike"
---

## MODIFIED Requirements

### Requirement: Partition backfill

시스템은 승인된 request의 `source_year`와 optional `source_file`이 식별하는 HMDA target partition을 overwrite 방식으로 재처리해야 한다(SHALL). Recovery mutation은 incident type별 별도 mutation API를 요구하지 않고 exact approved candidate와 target partition scope에 따라 실행되어야 한다(SHALL).

#### Scenario: Approved backfill

- **WHEN** 유효한 approval, source input과 target partition이 주어질 때
- **THEN** 대상 partition을 재적재하고 적재 row count를 반환해야 한다.

#### Scenario: Approved null-spike content recovery

- **GIVEN** target partition에서 단일 column의 `null_spike`가 탐지되고 clean partition candidate가 exact recovery proposal에 결합되어 있을 때
- **WHEN** approved backfill을 실행할 때
- **THEN** 별도 column mutation 없이 approved candidate content로 대상 partition을 교체해야 한다.

### Requirement: Post-backfill validation

시스템은 backfill 이후 aligned profile snapshot을 생성하고 expected recovered state와 actual target partition의 stable content identity를 비교한 validation 결과를 제공해야 한다(SHALL). Content identity는 target scope와 duplicate row semantics를 보존해야 한다(SHALL). Row-count comparison은 보조 evidence로 제공할 수 있지만 recovery correctness의 최종 oracle로 사용해서는 안 된다(MUST NOT). Incident-specific metric recovery는 profile evidence로 제공하되 content-identity validation의 의미를 변경해서는 안 된다(MUST NOT).

#### Scenario: Content-aligned recovery

- **WHEN** approved backfill이 성공하고 actual target content가 expected recovered state와 같을 때
- **THEN** 결과는 content validation 성공, 새 profile snapshot과 row-count evidence를 포함해야 한다.

#### Scenario: Null-rate profile evidence

- **GIVEN** approved candidate가 target column의 null rate를 복원할 것으로 기대될 때
- **WHEN** approved backfill 이후 profile validation이 완료될 때
- **THEN** result의 profile snapshot은 target column null rate를 포함해야 한다.
- **AND** recovery executor는 null-rate threshold를 content-identity validation 결과에 결합해서는 안 된다.

#### Scenario: File-scoped profile evidence

- **WHEN** `source_file` scoped approved backfill이 성공할 때
- **THEN** 결과는 새 profile snapshot과 row-count comparison을 포함해야 한다.
- **AND** row-count comparison을 file-level population equivalence로 해석해서는 안 된다.

#### Scenario: Equal count with different content

- **GIVEN** actual target과 expected recovered state의 row count는 같지만 stable content가 다를 때
- **WHEN** post-backfill validation을 수행할 때
- **THEN** recovery를 검증 성공으로 보고해서는 안 된다.
