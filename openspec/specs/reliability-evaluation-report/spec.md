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
