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
