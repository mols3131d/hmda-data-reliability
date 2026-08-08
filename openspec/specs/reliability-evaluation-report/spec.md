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
