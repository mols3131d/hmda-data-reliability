---
type: openspec-spec-driven-tdd-spec
category: spec
title: reliability-evaluation-report
description: Controlled Bronze ingestion freshness delay와 approved recovery/replay evidence를 추가한다.
tags:
  - "domain:reliability"
  - "capability:reliability-evaluation-report"
  - "freshness-delay"
---

## ADDED Requirements

### Requirement: Controlled Bronze ingestion freshness case

시스템은 required `observed_at`, explicit `max_age_minutes`와 controlled `delay_minutes`로 clean Bronze partition과 `ingested_at`만 지연된 freshness case를 서로 다른 disposable database에서 생성할 수 있어야 한다(SHALL). Delay injection은 source file, business columns, schema와 logical content identity를 변경해서는 안 된다(MUST NOT).

#### Scenario: Deterministic ingestion delay

- **GIVEN** `delay_minutes >= max_age_minutes`인 fixed observation과 valid HMDA source가 있을 때
- **WHEN** controlled freshness case를 생성할 때
- **THEN** clean과 delayed partition의 content identity와 schema hash는 같아야 한다.
- **AND** delayed partition의 `freshness_at`만 fixed delay만큼 과거여야 한다.

#### Scenario: Exact single freshness incident

- **WHEN** controlled delayed partition에 read-only lifecycle을 실행할 때
- **THEN** `freshness_delay` incident 하나만 탐지하고 age/max-age evidence를 반환해야 한다.
- **AND** approval, target recovery 또는 report write를 자동 실행해서는 안 된다.

#### Scenario: Existing or aliased evaluation database

- **GIVEN** target, clean 또는 candidate database가 존재하거나 둘 이상의 path가 같은 physical path를 식별할 때
- **WHEN** freshness evaluation entry를 요청할 때
- **THEN** directory/file/database 생성, source load와 external callback 전에 요청을 거부해야 한다.

### Requirement: Freshness recovery vertical-slice evaluation

시스템은 controlled freshness case에서 exact candidate content/timestamp, external approval, compound target gate, partition recovery, post-recovery lifecycle와 replay를 하나의 deterministic result로 집계할 수 있어야 한다(SHALL). Clean, delayed, recovery와 replay freshness observation을 구조화된 evidence로 보존해야 한다(SHALL).

#### Scenario: Approved freshness recovery

- **WHEN** controlled freshness delay가 complete proposal, exact candidate와 approval로 실행될 때
- **THEN** target content identity는 clean fixture와 같고 target freshness timestamp는 approved candidate와 같아야 한다.
- **AND** measured age는 max age 미만이고 post-recovery `freshness_delay` incident가 없어야 한다.
- **AND** downstream target validation이 성공해야 한다.

#### Scenario: Freshness replay

- **GIVEN** 첫 recovery가 expected content와 acceptable freshness를 복원했을 때
- **WHEN** 같은 approval로 replay를 실행할 때
- **THEN** overwrite 없이 verification을 재개하고 recovery/replay freshness evidence에 drift가 없어야 한다.

#### Scenario: Candidate freshness mismatch

- **WHEN** candidate content는 clean fixture와 같지만 candidate timestamp가 approved expected state와 다를 때
- **THEN** approval과 target mutation 전에 evaluation을 실패로 종료해야 한다.

### Requirement: Freshness evaluation failure evidence

시스템은 unavailable measurement, temporal target drift, expired replay와 downstream failure를 failure stage, target mutation 여부, reconciliation action과 preserved freshness observations로 구분해야 한다(SHALL). Recovery/replay freshness acceptance 뒤 downstream failure가 발생해도 이미 확정한 evidence를 손실해서는 안 된다(MUST NOT).

#### Scenario: Pre-mutation freshness failure

- **WHEN** candidate measurement가 unavailable이거나 target temporal state가 approval과 다를 때
- **THEN** target mutation 없이 failure를 반환하고 새 validation과 approval 필요성을 식별해야 한다.

#### Scenario: Expired replay observation

- **WHEN** replay 시 expected target timestamp의 age가 max age 이상일 때
- **THEN** 기존 approval의 overwrite를 차단하고 observed timestamp, age와 threshold를 evidence로 보존해야 한다.

#### Scenario: Failure after freshness acceptance

- **GIVEN** recovery와 replay의 content/freshness acceptance가 완료되었을 때
- **WHEN** post-recovery lifecycle 또는 target dbt validation이 실패할 때
- **THEN** clean, delayed, recovery와 replay freshness observation을 failure result에 보존해야 한다.
- **AND** reconciliation action은 completed mutation을 반복하지 않는 `resume_verification`이어야 한다.
