---
type: openspec-spec-driven-tdd-spec
category: spec
title: reliability-recovery-backfill
description: Freshness-specific temporal state를 exact approval, mutation gate, validation과 replay에 결합한다.
tags:
  - "domain:reliability"
  - "capability:reliability-recovery-backfill"
  - "freshness-delay"
---

## ADDED Requirements

### Requirement: Incident-typed recovery proposal

시스템은 recovery proposal에 `incident_type`을 포함해야 한다(SHALL). `freshness_delay` proposal은 measured approved-before observation, expected candidate `freshness_at`과 `max_age_minutes`를 포함하는 freshness binding을 반드시 가져야 한다(MUST). 다른 incident type의 proposal은 freshness binding을 포함해서는 안 된다(MUST NOT).

#### Scenario: Complete freshness recovery binding

- **GIVEN** approved-before measurement가 measured 상태이고 max age 이상 stale할 때
- **WHEN** expected candidate timestamp와 max age를 결합한 `freshness_delay` proposal을 생성할 때
- **THEN** proposal은 incident type, exact before observation과 expected after acceptance를 immutable하게 보존해야 한다.

#### Scenario: Missing freshness binding

- **WHEN** freshness binding이 없는 `freshness_delay` proposal을 생성할 때
- **THEN** contract validation은 proposal을 거부해야 한다.

#### Scenario: Freshness binding on content incident

- **WHEN** `volume_drop` 또는 `null_spike` proposal에 freshness binding을 포함할 때
- **THEN** contract validation은 proposal을 거부해야 한다.

### Requirement: Approved freshness candidate

시스템은 freshness recovery candidate를 target mutation 전에 immutable staged artifact로 만들고 candidate content identity와 `max(ingested_at)`이 proposal의 approved candidate/expected freshness state와 모두 일치하는지 확인해야 한다(SHALL). 검증한 staged artifact와 실제 mutation input은 동일해야 한다(MUST).

#### Scenario: Candidate temporal mismatch

- **GIVEN** candidate content identity는 approved state와 같지만 `max(ingested_at)`이 expected timestamp와 다를 때
- **WHEN** approved freshness recovery를 요청할 때
- **THEN** approval callback 또는 target mutation 전에 candidate를 거부해야 한다.

#### Scenario: Candidate changes during validation

- **GIVEN** candidate가 validation 전에 expected content identity와 freshness timestamp를 가질 때
- **WHEN** candidate validation이 content 또는 `max(ingested_at)`을 변경할 때
- **THEN** immutable staged artifact에서 state를 다시 측정하고 proposal 또는 approval callback 전에 mismatch를 거부해야 한다.

#### Scenario: Candidate measurement unavailable

- **WHEN** candidate에서 valid `ingested_at` freshness를 측정할 수 없을 때
- **THEN** target partition을 변경하지 않고 candidate validation failure로 종료해야 한다.

### Requirement: Freshness-bound target reconciliation

시스템은 freshness recovery의 current target을 content identity와 temporal state의 compound state로 비교해야 한다(SHALL). Current target이 approved before compound state와 같을 때만 overwrite를 허용하고, expected content/timestamp와 일치하며 current age가 max age 미만일 때만 overwrite 없이 verification을 재개해야 한다(SHALL). 어느 state에도 해당하지 않거나 expected timestamp가 다시 stale하면 기존 approval로 추가 mutation해서는 안 된다(MUST NOT).

#### Scenario: Stale before-state with equal content

- **GIVEN** approved before/after content identity가 같지만 current freshness가 approved stale before-state와 일치할 때
- **WHEN** approved freshness recovery를 실행할 때
- **THEN** `already_recovered`로 판정하지 않고 transaction 내부 content + temporal gate를 통과한 뒤 partition을 교체해야 한다.

#### Scenario: Freshness replay stability

- **GIVEN** current target이 expected content와 expected freshness timestamp를 보존하고 current age가 max age 미만일 때
- **WHEN** 같은 approved recovery를 재실행할 때
- **THEN** partition overwrite 없이 verification을 재개해야 한다.

#### Scenario: Replay freshness expired

- **GIVEN** current content와 timestamp는 expected state와 같지만 current observation에서 age가 max age 이상일 때
- **WHEN** 같은 approved recovery를 재실행할 때
- **THEN** overwrite를 반복하지 않고 새 candidate validation과 approval을 요구해야 한다.

#### Scenario: Temporal drift after approval

- **GIVEN** approval 뒤 target content는 같지만 `max(ingested_at)`이 변경되었을 때
- **WHEN** approved recovery가 첫 mutation을 시도할 때
- **THEN** transaction 내부 target gate에서 zero mutation으로 차단해야 한다.

### Requirement: Freshness validation evidence

시스템은 freshness-bound recovery result에 approved-before observation, expected timestamp, actual post-recovery observation과 freshness validation 결과를 포함해야 한다(SHALL). Existing `validation_passed`는 content identity oracle로 유지하고 freshness acceptance를 해당 field에 합쳐서는 안 된다(MUST NOT). Freshness recovery 전체 성공은 content validation, measured freshness age의 max-age 미만과 post-recovery incident 해소를 모두 요구해야 한다(SHALL).

#### Scenario: Independent content and freshness validation

- **WHEN** approved recovery 뒤 content identity와 expected timestamp가 복원되고 measured age가 max age 미만일 때
- **THEN** result는 content validation과 freshness validation을 각각 성공으로 반환해야 한다.

#### Scenario: Post-mutation profile failure

- **GIVEN** partition replacement는 완료됐지만 freshness profile validation이 실패할 때
- **WHEN** recovery failure를 반환할 때
- **THEN** completed mutation, actual content/temporal observation 가능 여부와 `resume_verification` action을 보존해야 한다.
- **AND** 성공한 recovery로 보고해서는 안 된다.
