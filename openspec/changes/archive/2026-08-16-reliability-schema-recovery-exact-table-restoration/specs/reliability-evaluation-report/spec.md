---
type: openspec-spec-driven-tdd-spec
category: spec
title: reliability-evaluation-report
description: Controlled schema drift의 exact table restoration과 safety evidence를 deterministic evaluation으로 확장한다.
tags:
  - "domain:reliability"
  - "capability:reliability-evaluation-report"
  - "schema-drift"
---

## ADDED Requirements

### Requirement: Schema-drift recovery vertical-slice evaluation

시스템은 deterministic complete HMDA fixture로 clean baseline과 controlled `loan_amount` type drift target을 isolated disposable database에서 실행하고 detection, complete candidate validation, approval, table restoration, replay와 downstream verification 결과를 case evidence로 집계할 수 있어야 한다(SHALL). Evaluation은 schema identity와 complete content state를 독립 acceptance oracle로 사용해야 한다(SHALL).

#### Scenario: Existing or aliased evaluation database

- **GIVEN** target, clean 또는 candidate database path가 이미 존재하거나 둘 이상이 같은 physical path를 식별할 때
- **WHEN** schema-drift evaluation을 요청할 때
- **THEN** workspace 생성, source load, synthetic defect, callback과 recovery 전에 요청을 거부해야 한다.
- **AND** 기존 database content를 변경해서는 안 된다.

#### Scenario: Clean baseline

- **WHEN** deterministic clean fixture를 평가할 때
- **THEN** `schema_drift` incident가 없어야 하고 baseline schema identity와 complete content state를 evidence로 제공해야 한다.

#### Scenario: Controlled table schema drift

- **GIVEN** clean fixture의 `loan_amount`가 numeric type일 때
- **WHEN** controlled target을 `loan_amount: VARCHAR` schema로 materialize해 평가할 때
- **THEN** target table schema identity가 baseline과 달라야 하고 expected `schema_drift` incident를 식별해야 한다.
- **AND** defect proof를 existing clean table에 partition insert한 결과로 대체해서는 안 된다.

#### Scenario: Approved schema-drift restoration

- **WHEN** controlled drift target이 valid complete candidate와 complete approval로 실행될 때
- **THEN** target schema identity와 complete content state가 clean expected state와 정확히 같아야 한다.
- **AND** post-recovery lifecycle에서 `schema_drift`가 해소되고 target dbt validation이 성공해야 한다.

#### Scenario: Incomplete candidate false-green guard

- **GIVEN** candidate가 expected schema를 가지지만 sentinel partition을 포함한 complete population 일부가 누락됐을 때
- **WHEN** schema-drift evaluation을 실행할 때
- **THEN** approval과 target mutation 전에 실패해야 한다.
- **AND** schema equality만으로 candidate 또는 recovery를 성공으로 판정해서는 안 된다.

#### Scenario: Stale schema or content evidence

- **WHEN** approval 이후 target schema 또는 content가 approved before-state에서 달라진 case를 평가할 때
- **THEN** target mutation이 없어야 하고 changed state와 새 validation 및 approval 필요성을 evidence로 포함해야 한다.

#### Scenario: Replacement rollback evidence

- **GIVEN** approved before-state에서 replacement transaction failure가 주입됐을 때
- **WHEN** schema recovery case를 평가할 때
- **THEN** exact before schema/content state가 보존되고 rollback 및 no committed mutation evidence를 포함해야 한다.

#### Scenario: Schema-drift replay stability

- **GIVEN** 첫 approved recovery가 expected after-state를 복원했을 때
- **WHEN** 같은 approval과 fixture identity로 recovery를 반복 평가할 때
- **THEN** table replacement를 반복하지 않고 verification을 재개해야 한다.
- **AND** schema/content state, lifecycle resolution과 evidence projection에 semantic drift가 없어야 한다.

#### Scenario: Schema-drift safety failure evidence

- **WHEN** candidate schema/content/dbt validation, approval, stale/diverged target state, replacement 또는 post-restoration verification 중 하나가 실패할 때
- **THEN** evaluation은 failure stage, committed target mutation 여부와 reconciliation action을 구조화해야 한다.
- **AND** schema recovery failure를 partition-specific mutation state로 표현해서는 안 된다.

#### Scenario: Read-only lifecycle preservation

- **WHEN** controlled schema-drift target에 read-only incident lifecycle만 실행할 때
- **THEN** incident와 remediation draft를 반환하되 approval, complete candidate materialization, table replacement와 evaluation report write를 실행해서는 안 된다.
