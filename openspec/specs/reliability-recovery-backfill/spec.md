# reliability-recovery-backfill Specification

## Purpose

명시적으로 승인된 HMDA partition recovery를 실행하고 backfill 이후 profile을 재측정해 validation 결과를 제공하는 계약을 정의한다.

## Requirements

### Requirement: Approval gate

시스템은 recovery 실행 전에 approval이 승인 상태이며 exact recovery proposal의 incident, target partition, validated candidate, validation evidence, approved target state와 모든 target mutation action에 결합되어 있는지 확인해야 한다(SHALL). 실행 source의 staged content identity가 validated candidate와 다르거나 결합 정보가 없거나 실제 실행 request와 다르면 source 처리와 target mutation 전에 차단해야 한다(SHALL). 검증된 staged candidate는 target mutation까지 immutable artifact로 유지해야 한다(SHALL).

#### Scenario: Missing approval

- **WHEN** 승인되지 않았거나 필수 action이 없는 recovery를 요청할 때
- **THEN** source 처리와 target 변경 전에 요청을 차단해야 한다.

#### Scenario: Incomplete approval

- **WHEN** approval이 target mutation action 또는 required proposal/evidence binding을 포함하지 않은 recovery를 요청할 때
- **THEN** source 처리와 target mutation 전에 요청을 차단해야 한다.

#### Scenario: Mismatched approved proposal

- **GIVEN** approval이 식별하는 candidate, target state 또는 action과 recovery request가 다를 때
- **WHEN** recovery 실행을 요청할 때
- **THEN** 기존 approval로 target을 변경해서는 안 된다.

#### Scenario: Mismatched approved source

- **GIVEN** approval 이후 실행 source content가 validated candidate와 달라졌을 때
- **WHEN** recovery 실행을 요청할 때
- **THEN** target partition을 변경하지 않고 recovery를 차단해야 한다.

#### Scenario: Source replacement after staging

- **GIVEN** staged candidate identity 검증 뒤 원본 source가 변경되었을 때
- **WHEN** approved recovery가 target mutation을 수행할 때
- **THEN** 검증된 staged candidate만 target에 적용해야 한다.

### Requirement: Partition backfill

시스템은 승인된 request의 `source_year`와 optional `source_file`이 식별하는 HMDA target partition을 overwrite 방식으로 재처리해야 한다(SHALL). Recovery mutation은 incident type별 별도 mutation API를 요구하지 않고 exact approved candidate와 target partition scope에 따라 실행되어야 한다(SHALL).

#### Scenario: Approved backfill

- **WHEN** 유효한 approval, source input과 target partition이 주어질 때
- **THEN** 대상 partition을 재적재하고 적재 row count를 반환해야 한다.

#### Scenario: Approved null-spike content recovery

- **GIVEN** target partition에서 단일 column의 `null_spike`가 탐지되고 clean partition candidate가 exact recovery proposal에 결합되어 있을 때
- **WHEN** approved backfill을 실행할 때
- **THEN** 별도 column mutation 없이 approved candidate content로 대상 partition을 교체해야 한다.

### Requirement: Profile alignment

Post-backfill profile request는 backfill target table과 같은 table을 가리키고 partition identity는 recovery target과 일치해야 한다(SHALL).

Recovery profile의 `partition_column`은 `source_year` 또는 year alias인 `activity_year`여야 하며, 실제 profile population은 승인된 `source_year`의 전체 observation으로 정렬해야 한다(SHALL). 다른 discriminator는 target mutation 전에 거부해야 한다(SHALL). Optional `source_file`은 mutation 범위만 제한하며 year observation을 file 범위로 축소해서는 안 된다(MUST NOT).

시스템은 target population 검사, mutation 또는 replay, profile과 actual state evidence 산출을 local managed writer와 직렬화해 같은 observation 상태에서 수행해야 한다(SHALL).

#### Scenario: Misaligned profile request

- **WHEN** profile target 또는 partition이 recovery target과 다를 때
- **THEN** 시스템은 backfill 실행 전에 요청을 거부해야 한다.

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

### Requirement: Target-state freshness

시스템은 candidate validation 당시 target state를 approval에 결합하고 첫 target mutation 직전에 같은 state인지 다시 확인해야 한다(SHALL). Target-state 확인과 첫 mutation 사이에는 local concurrent writer가 끼어들 수 없는 serialization 경계를 제공해야 한다(SHALL).

#### Scenario: Stale target

- **GIVEN** approval 이후 target partition content가 변경되었을 때
- **WHEN** approved recovery가 실행될 때
- **THEN** 첫 target mutation 전에 중단하고 새 candidate validation과 approval을 요구해야 한다.

### Requirement: Mutation-aware recovery result

시스템은 target mutation 전 실패, partition 변경 완료와 downstream verification 성공 또는 실패를 구분해 반환해야 한다(SHALL). Post-mutation failure를 recovery 성공으로 보고해서는 안 된다(MUST NOT).

#### Scenario: Downstream verification failure

- **GIVEN** partition replacement는 완료됐지만 profile 또는 dbt verification이 실패했을 때
- **WHEN** recovery result를 반환할 때
- **THEN** partition이 변경된 post-mutation failure임을 식별해야 한다.

### Requirement: Recovery reconciliation

시스템은 재실행 시 current target을 approved before state와 expected recovered state에 비교해야 한다(SHALL). Current target이 expected recovered state와 같으면 partition overwrite를 반복하지 않고 downstream verification을 재개해야 한다(SHALL). 어느 state와도 다르면 기존 approval로 추가 mutation해서는 안 된다(MUST NOT).

#### Scenario: Resume verification

- **GIVEN** current target이 expected recovered state와 같고 이전 실행이 post-mutation failure로 끝났을 때
- **WHEN** 같은 approved recovery를 재실행할 때
- **THEN** partition overwrite 없이 downstream verification을 재개해야 한다.

#### Scenario: Diverged target

- **GIVEN** current target이 approved before state와 expected recovered state 어느 쪽과도 다를 때
- **WHEN** 같은 approved recovery를 재실행할 때
- **THEN** 추가 mutation을 차단하고 새 validation과 approval을 요구해야 한다.

### Requirement: Recovery remains outside read-only lifecycle

시스템은 read-only incident lifecycle이 recovery를 자동으로 실행하게 해서는 안 된다(MUST NOT).

#### Scenario: Incident lifecycle execution

- **WHEN** read-only incident lifecycle이 incident와 remediation draft를 생성할 때
- **THEN** approved backfill은 자동으로 실행되어서는 안 된다.

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
