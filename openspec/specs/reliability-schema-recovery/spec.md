# reliability-schema-recovery Specification

## Purpose

Table-wide schema drift를 external approval과 검증된 complete-table state에 결합해 복구하고, invalid candidate와 stale target이 기존 data를 변경하지 못하도록 보장한다.

## Requirements

### Requirement: Composite table state

시스템은 recovery target table의 schema identity와 complete partition content identity set을 하나의 immutable table state로 표현해야 한다(SHALL). Content identity set은 target table의 전체 population을 식별하고 partition별 scope와 duplicate multiplicity를 보존해야 한다(SHALL). Row count나 source path만으로 complete content equality를 판정해서는 안 된다(MUST NOT).

#### Scenario: Equivalent complete table state

- **GIVEN** 두 table state가 같은 target table과 schema identity를 식별할 때
- **WHEN** 두 state의 complete partition content identity set을 비교할 때
- **THEN** 모든 partition identity와 population이 같을 때만 같은 table state로 판정해야 한다.

#### Scenario: Equal schema with missing partition

- **GIVEN** candidate와 target의 schema identity 및 포함된 partition content는 같지만 candidate population에서 한 partition이 누락됐을 때
- **WHEN** complete table state를 비교할 때
- **THEN** 두 state를 같다고 판정해서는 안 된다.

#### Scenario: Equal row count with different content

- **GIVEN** candidate와 expected after-state의 total row count는 같지만 한 partition의 stable content가 다를 때
- **WHEN** complete table state를 비교할 때
- **THEN** candidate validation을 성공으로 판정해서는 안 된다.

### Requirement: Complete candidate preflight

시스템은 target mutation 전에 isolated candidate가 exact target table, expected schema identity와 complete expected content state를 만족하는지 검증해야 한다(SHALL). Candidate downstream dbt validation이 요구된 request에서는 그 evidence도 approval 전에 성공해야 한다(SHALL). Candidate가 invalid하거나 incomplete하면 target mutation과 approval callback 전에 차단해야 한다(SHALL).

#### Scenario: Valid complete candidate

- **WHEN** isolated candidate가 expected schema identity, complete content state와 required dbt validation을 모두 만족할 때
- **THEN** 시스템은 candidate state와 validation evidence를 recovery proposal에 사용할 수 있어야 한다.

#### Scenario: Candidate schema mismatch

- **GIVEN** candidate content는 complete하지만 schema identity가 expected after-state와 다를 때
- **WHEN** candidate preflight를 수행할 때
- **THEN** approval과 target mutation 전에 candidate를 거부해야 한다.

#### Scenario: Incomplete candidate population

- **GIVEN** candidate schema는 유효하지만 target table의 expected partition population 일부가 누락됐을 때
- **WHEN** candidate preflight를 수행할 때
- **THEN** approval과 target mutation 전에 candidate를 거부하고 누락된 population evidence를 제공해야 한다.

#### Scenario: Candidate dbt failure

- **GIVEN** candidate schema와 content state가 유효하지만 required downstream dbt validation이 실패할 때
- **WHEN** candidate preflight를 수행할 때
- **THEN** target mutation 없이 failure evidence를 반환해야 한다.

### Requirement: Exact table-recovery approval

시스템은 recovery 실행 전에 approval이 exact incident, target table, observed before-state, validated candidate state, expected after-state, validation evidence와 모든 table mutation action에 결합되어 있는지 확인해야 한다(SHALL). 실행 request 또는 immutable staged candidate가 approved proposal과 다르면 target state 확인과 mutation 전에 차단해야 한다(SHALL).

#### Scenario: Complete approval

- **WHEN** approval이 exact proposal의 target, before/candidate/after state, evidence와 required actions에 결합되어 있을 때
- **THEN** 시스템은 approved recovery의 target-state reconciliation을 진행할 수 있어야 한다.

#### Scenario: Incomplete approval

- **WHEN** approval에 required table replacement action 또는 before/candidate/after state binding이 없을 때
- **THEN** target state 확인과 mutation 전에 recovery를 차단해야 한다.

#### Scenario: Mismatched staged candidate

- **GIVEN** approval 이후 execution에 사용되는 staged candidate state가 approved candidate state와 다를 때
- **WHEN** recovery를 요청할 때
- **THEN** 기존 approval로 target을 변경해서는 안 된다.

### Requirement: Observation and mutation scope separation

시스템은 partition-scoped incident observation과 table-wide recovery target을 명시적으로 구분해야 한다(SHALL). Incident partition을 table mutation의 partition scope로 해석하거나 partial schema recovery에 사용해서는 안 된다(MUST NOT).

#### Scenario: Partition-observed schema drift

- **GIVEN** 한 partition profile 비교에서 table-wide schema hash mismatch가 탐지됐을 때
- **WHEN** table recovery proposal을 생성할 때
- **THEN** proposal은 incident partition을 observation evidence로 보존하고 별도의 exact target table을 mutation scope로 식별해야 한다.

### Requirement: Transactional exact table restoration

시스템은 approved before-state를 first mutation 직전에 다시 확인하고, local concurrent writer가 그 확인과 first mutation 사이에 끼어들 수 없는 serialization boundary 안에서 validated complete candidate로 target table을 exact restoration해야 한다(SHALL). Replacement, in-transaction final table-state verification 또는 aligned profile validation 중 하나라도 실패하면 transaction을 rollback하고 exact before-state를 보존해야 한다(SHALL).

#### Scenario: Approved before-state restoration

- **GIVEN** current target이 approved before-state와 같을 때
- **WHEN** approved schema recovery를 실행할 때
- **THEN** target을 validated candidate의 exact schema/content state로 교체하고 expected after-state와 aligned profile을 검증한 뒤 commit해야 한다.

#### Scenario: Stale target before mutation

- **GIVEN** approval 이후 target schema 또는 content state가 approved before-state와 달라졌을 때
- **WHEN** approved schema recovery를 실행할 때
- **THEN** first target mutation 전에 중단하고 새 validation과 approval을 요구해야 한다.

#### Scenario: Replacement failure rollback

- **GIVEN** current target이 approved before-state와 같을 때
- **WHEN** table replacement, in-transaction final state 또는 aligned profile validation이 실패할 때
- **THEN** transaction을 rollback하고 target의 exact before-state를 보존해야 한다.
- **AND** committed target mutation이 없고 같은 approval로 recovery를 다시 시도할 수 있어야 한다.

#### Scenario: Sentinel partition preservation

- **GIVEN** candidate가 drift observation partition과 별도의 sentinel partition을 포함하는 complete expected population일 때
- **WHEN** approved restoration이 성공할 때
- **THEN** sentinel partition content identity는 expected candidate identity와 같아야 한다.

### Requirement: Post-restoration validation result

시스템은 commit 전에 actual schema identity와 complete content state를 expected after-state와 비교하고 aligned profile snapshot을 생성해 mutation-aware result를 제공해야 한다(SHALL). Schema, complete content 또는 aligned profile validation이 실패하면 recovery를 commit하거나 검증 성공으로 보고해서는 안 된다(MUST NOT).

#### Scenario: Verified restoration

- **WHEN** target schema/content state가 expected after-state와 같고 aligned profile snapshot이 생성될 때
- **THEN** result는 mutation 완료, exact state validation과 profile evidence를 포함해야 한다.

#### Scenario: Schema-only restoration

- **GIVEN** target schema identity는 expected after-state와 같지만 complete content state가 다를 때
- **WHEN** in-transaction restoration verification을 수행할 때
- **THEN** recovery를 commit하거나 검증 성공으로 판정해서는 안 된다.

#### Scenario: In-transaction profile validation failure

- **GIVEN** target table replacement와 schema/content verification은 transaction 안에서 완료됐을 때
- **WHEN** commit 전에 aligned profile validation이 실패할 때
- **THEN** transaction을 rollback해 exact before-state를 보존해야 한다.
- **AND** 같은 approval로 recovery를 다시 시도할 수 있어야 한다.

#### Scenario: Staging cleanup failure after commit

- **GIVEN** exact table restoration과 aligned profile validation이 commit된 뒤 staging directory 종료가 `OSError`로 실패할 때
- **WHEN** recovery API가 failure를 반환할 때
- **THEN** `SchemaRecoveryValidationError`는 `after_target_mutation`, `table_replaced`, actual table state와 `resume_verification`을 보존해야 한다.
- **AND** 오류 원인을 보존하고 정상 완료나 rollback으로 보고하거나 table replacement를 자동 재실행해서는 안 된다.

#### Scenario: Staging cleanup failure during replay

- **GIVEN** target이 expected after-state와 같아 table replacement 없이 verification을 수행했을 때
- **WHEN** staging directory 종료가 `OSError`로 실패할 때
- **THEN** failure는 `replay_verification`, `already_restored`, actual table state와 `resume_verification`을 보존해야 한다.

### Requirement: Table-recovery reconciliation

시스템은 재실행 시 current target table state를 approved before-state와 expected after-state에 비교해야 한다(SHALL). Current state가 expected after-state와 같으면 table replacement를 반복하지 않고 downstream verification을 재개해야 한다(SHALL). 어느 state와도 다르면 기존 approval로 추가 mutation해서는 안 된다(MUST NOT).

#### Scenario: Already restored replay

- **GIVEN** current target이 expected after-state와 같을 때
- **WHEN** 같은 approved recovery를 재실행할 때
- **THEN** table replacement 없이 verification을 재개하고 `resume_verification`을 반환해야 한다.

#### Scenario: Diverged target replay

- **GIVEN** current target이 approved before-state와 expected after-state 어느 쪽과도 다를 때
- **WHEN** 같은 approved recovery를 재실행할 때
- **THEN** 추가 mutation을 차단하고 새 validation과 approval을 요구해야 한다.

### Requirement: Recovery remains outside read-only lifecycle

Read-only incident lifecycle은 table-schema recovery, approval, candidate materialization 또는 evaluation report write를 자동 실행해서는 안 된다(MUST NOT).

#### Scenario: Schema-drift lifecycle execution

- **WHEN** read-only lifecycle이 `schema_drift` incident와 remediation draft를 생성할 때
- **THEN** candidate validation, approval과 table mutation은 실행되어서는 안 된다.
