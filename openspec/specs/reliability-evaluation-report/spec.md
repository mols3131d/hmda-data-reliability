# reliability-evaluation-report Specification

## Purpose

Synthetic reliability case의 expected/actual detection과 action 결과를 집계하고 사람이 검토 가능한 evaluation evidence로 제공하는 계약을 정의한다.

## Requirements

### Requirement: Synthetic case aggregation

시스템은 synthetic case별 detection과 action 성공 여부를 판정하고 전체 성공률을 계산해야 한다(SHALL). Expected incident가 있는 case는 모든 expected incident type이 detected incident에 포함될 때 detection 성공이어야 한다(MUST). 모든 required action이 remediation action에 포함될 때 action 성공이어야 한다(MUST).

#### Scenario: Case result aggregation

- **WHEN** expected incident와 required action이 있는 case result 목록을 평가할 때
- **THEN** 각 case의 expected incident가 모두 detected되고 required action이 모두 remediation action에 포함된 경우 해당 결과를 성공으로 판정해야 한다.
- **AND** 전체 detection/action 성공률은 각 성공 case 수를 전체 case 수로 나눈 값이어야 한다.

#### Scenario: Empty case list

- **WHEN** 평가할 synthetic case가 없을 때
- **THEN** detection success rate와 action success rate는 0.0이어야 한다.

### Requirement: Normal case handling

시스템은 expected incident가 없는 normal case에서 실제 detection도 없으면 detection 성공으로 판정해야 한다(SHALL).

#### Scenario: Normal case without detection

- **WHEN** expected incident가 없는 case에서 실제 detected incident도 없을 때
- **THEN** 해당 case의 detection 결과는 성공으로 집계되어야 한다.

### Requirement: Markdown evaluation output

시스템은 evaluation result를 caller가 지정한 위치에 사람이 검토 가능한 Markdown으로 기록할 수 있어야 한다(SHALL).

#### Scenario: Report write

- **WHEN** 유효한 output path에 report를 쓸 때
- **THEN** 각 case의 expected/actual detection과 action 결과를 확인할 수 있어야 한다.

### Requirement: Evaluation remains outside incident lifecycle

Read-only incident lifecycle은 synthetic evaluation이나 report write를 자동 실행해서는 안 된다(MUST NOT).

#### Scenario: Read-only lifecycle execution

- **WHEN** read-only incident lifecycle이 완료될 때
- **THEN** synthetic evaluation과 evaluation report write는 자동으로 실행되어서는 안 된다.

### Requirement: Recovery vertical-slice evaluation

시스템은 deterministic fixture identity와 defect parameters로 clean baseline과 controlled `volume_drop` case를 실행하고 detection, candidate validation, approval, recovery와 downstream verification 결과를 case evidence로 집계할 수 있어야 한다(SHALL).

#### Scenario: Deterministic fixture state

- **GIVEN** 같은 fixture identity와 defect parameters가 주어질 때
- **WHEN** expected recovery state를 반복 생성할 때
- **THEN** 같은 partition content identity와 expected recovery evidence를 생성해야 한다.

#### Scenario: Clean baseline

- **WHEN** defect가 없는 deterministic fixture를 평가할 때
- **THEN** incident와 remediation draft가 생성되지 않아야 한다.

#### Scenario: Approved volume-drop recovery

- **WHEN** controlled `volume_drop` case가 valid candidate와 complete approval로 실행될 때
- **THEN** expected incident와 impact가 관찰되고 target content, incident resolution과 downstream dbt verification이 모두 성공해야 한다.

#### Scenario: Replay stability

- **WHEN** 같은 approved recovery와 fixture identity를 반복 평가할 때
- **THEN** duplicate 또는 semantic drift가 생기지 않고 stable evidence projection을 재현해야 한다.

#### Scenario: Replay verification failure after recovery

- **GIVEN** 첫 approved recovery가 target을 expected recovered state로 변경한 뒤 replay를 시작했을 때
- **WHEN** replay의 downstream verification이 실패할 때
- **THEN** evaluation은 완료된 첫 recovery와 target mutation을 보존하고 replay failure를 별도로 식별해야 한다.
- **AND** 다음 조치는 partition overwrite가 아니라 `resume_verification`이어야 한다.

### Requirement: Recovery safety case evaluation

시스템은 invalid candidate, stale target, incomplete approval, candidate dbt failure, recovery dbt failure와 diverged reconciliation을 각각 target mutation 여부와 preserved evidence로 판정해야 한다(SHALL).

#### Scenario: Pre-mutation safety failures

- **WHEN** invalid candidate, stale target 또는 incomplete approval case를 평가할 때
- **THEN** target mutation이 없고 차단 이유가 case evidence에 포함되어야 한다.
- **AND** stale target의 reconciliation action은 `request_new_validation_and_approval`이어야 한다.

#### Scenario: Post-mutation recovery failure

- **WHEN** partition 변경 이후 dbt verification이 실패하는 case를 평가할 때
- **THEN** post-mutation failure, expected current partition과 prior last-known-good artifact가 evidence에 포함되어야 한다.
- **AND** 다음 조치는 partition overwrite가 아니라 `resume_verification`이어야 한다.

#### Scenario: Artifact state after post-promotion domain failure

- **GIVEN** target artifact promotion이 current projection을 변경했을 때
- **WHEN** 이후 artifact observation이 data-operations domain failure로 종료될 때
- **THEN** evaluation은 prior projection이 유지됐다고 보고해서는 안 된다.
- **AND** locked re-observation으로 확인한 actual current projection 또는 관찰 실패를 evidence에 명시해야 한다.

#### Scenario: Diverged reconciliation case

- **WHEN** current target이 approved before/after state 어느 쪽과도 다른 case를 평가할 때
- **THEN** 기존 approval의 추가 mutation이 차단되고 새 validation과 approval 필요성이 evidence에 포함되어야 한다.
- **AND** reconciliation action은 `request_new_validation_and_approval`이어야 한다.

### Requirement: Null-spike recovery vertical-slice evaluation

시스템은 deterministic fixture identity, target column과 defect parameters로 clean baseline과 controlled single-column `null_spike` case를 서로 다른 isolated disposable target, clean과 candidate database에서 실행하고 detection, candidate validation, approval, recovery, replay와 downstream verification 결과를 case evidence로 집계할 수 있어야 한다(SHALL). Expected recovery identity와 target column null rate는 clean fixture baseline에서 직접 유도해야 한다(SHALL). Evaluation은 recovery executor의 stable content validation과 별도로 baseline target column null-rate의 exact restoration 및 post-recovery incident 해소를 판정해야 한다(SHALL).

#### Scenario: Existing evaluation database

- **GIVEN** evaluation target, workspace clean 또는 candidate database path 중 하나가 이미 존재할 때
- **WHEN** controlled `null_spike` evaluation을 요청할 때
- **THEN** workspace directory 또는 file 생성, source load, synthetic defect 적용, candidate validation과 approval 전에 요청을 거부해야 한다.
- **AND** 기존 database content를 변경해서는 안 된다.

#### Scenario: Aliased evaluation database paths

- **GIVEN** target, workspace clean과 candidate database path 중 둘 이상이 같은 physical path를 식별할 때
- **WHEN** controlled `null_spike` evaluation을 요청할 때
- **THEN** workspace directory 또는 file 생성, source load와 external callback 전에 요청을 거부해야 한다.
- **AND** target mutation 또는 recovery evidence를 생성해서는 안 된다.

#### Scenario: Evaluation path preflight

- **GIVEN** target, workspace clean과 candidate database path가 모두 존재하지 않을 때
- **WHEN** controlled `null_spike` evaluation entry가 path를 검증할 때
- **THEN** 세 path가 pairwise distinct physical path인지 하나의 preflight에서 확인해야 한다.
- **AND** preflight가 성공한 뒤에만 workspace directory, synthetic artifact와 evaluation database를 생성할 수 있다.

#### Scenario: Controlled single-column null spike

- **GIVEN** profiled target column과 고정된 null fraction이 주어질 때
- **WHEN** controlled `null_spike` case를 생성해 평가할 때
- **THEN** row count를 감소시키지 않고 해당 target column의 `null_spike` incident 하나를 식별해야 한다.

#### Scenario: Ambiguous incident set

- **GIVEN** controlled target lifecycle에서 target-column `null_spike`가 없거나 다른 incident를 포함해 둘 이상의 incident가 탐지될 때
- **WHEN** recovery proposal을 생성하려 할 때
- **THEN** candidate validation, approval과 target mutation 전에 evaluation을 실패로 종료해야 한다.
- **AND** detected incident types와 cardinality를 evidence로 포함해야 한다.

#### Scenario: Approved null-spike recovery

- **WHEN** controlled `null_spike` case가 valid clean candidate와 complete approval로 실행될 때
- **THEN** expected incident와 impact가 관찰되고 target content identity와 target column null rate가 clean fixture baseline과 정확히 일치해야 한다.
- **AND** incident resolution과 downstream dbt verification이 모두 성공해야 한다.

#### Scenario: Independent null-rate acceptance evidence

- **WHEN** approved recovery와 replay가 expected content identity를 복원할 때
- **THEN** evaluation case evidence는 baseline, recovery와 replay target-column null rate를 포함해야 한다.
- **AND** recovery 또는 replay의 content validation이 실패하거나 null rate가 baseline과 다르면 downstream success로 판정해서는 안 된다.
- **AND** content validation은 성공하고 null rate만 baseline과 다르면 `resume_verification`을, content validation이 실패하면 새 validation과 approval 필요성을 evidence에 포함해야 한다.
- **AND** recovery와 replay quality acceptance가 완료된 뒤 post-recovery lifecycle 또는 target validation이 실패해도 이미 확정한 baseline/recovery/replay null-rate evidence를 case result에 보존해야 한다.

#### Scenario: Residual-null candidate rejection

- **GIVEN** candidate target column null rate가 detection threshold 아래이지만 clean fixture baseline과 다르고 candidate identity도 clean expected identity와 다를 때
- **WHEN** recovery proposal을 생성하려 할 때
- **THEN** approval과 target mutation 전에 candidate를 거부해야 한다.
- **AND** candidate/expected identity와 candidate/baseline null-rate evidence를 case result에 포함해야 한다.

#### Scenario: Null-spike replay stability

- **GIVEN** 첫 approved recovery가 clean expected state와 null-rate를 복원했을 때
- **WHEN** 같은 approval과 fixture identity로 recovery를 반복 평가할 때
- **THEN** partition overwrite를 반복하지 않고 verification을 재개해야 한다.
- **AND** duplicate, semantic drift 또는 null-rate drift 없이 stable evidence를 재현해야 한다.

#### Scenario: Null-spike safety failure evidence

- **WHEN** candidate validation, approval, target freshness 또는 downstream verification 중 하나가 실패할 때
- **THEN** evaluation은 failure stage, target mutation 여부와 reconciliation action을 기존 recovery safety evidence 형식으로 식별해야 한다.
- **AND** candidate 또는 target validation callback의 `ValueError`를 raw exception으로 노출해서는 안 된다.

#### Scenario: Read-only lifecycle preservation

- **WHEN** controlled `null_spike` target에 read-only incident lifecycle만 실행할 때
- **THEN** incident와 remediation draft를 반환하되 approval, partition overwrite, evaluation report write를 실행해서는 안 된다.

### Requirement: Schema-drift recovery vertical-slice evaluation

시스템은 deterministic complete HMDA fixture로 clean baseline과 controlled `loan_amount` type drift target을 isolated disposable database에서 실행하고 detection, complete candidate validation, approval, table restoration, replay와 downstream verification 결과를 case evidence로 집계할 수 있어야 한다(SHALL). Evaluation은 schema identity와 complete content state를 독립 acceptance oracle로 사용해야 한다(SHALL).

#### Scenario: Existing or aliased evaluation database

- **GIVEN** target, clean 또는 candidate database path가 이미 존재하거나 둘 이상이 같은 physical path를 식별할 때
- **WHEN** schema-drift evaluation을 요청할 때

#### Scenario: Clean baseline (schema drift)

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

#### Scenario: Read-only lifecycle preservation (schema drift)

- **WHEN** controlled schema-drift target에 read-only incident lifecycle만 실행할 때
- **THEN** incident와 remediation draft를 반환하되 approval, complete candidate materialization, table replacement와 evaluation report write를 실행해서는 안 된다.

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

#### Scenario: Existing or aliased freshness evaluation database

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
