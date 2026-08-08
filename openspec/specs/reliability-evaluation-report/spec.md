# reliability-evaluation-report Specification

## Purpose

Synthetic reliability case의 expected/actual detection과 action 결과를 집계하고 사람이 검토 가능한 evaluation evidence로 제공하는 계약을 정의한다.

## Requirements

### Requirement: Synthetic case aggregation

시스템은 synthetic case 결과에서 detection 성공 여부, action 성공 여부와 전체 성공률을 계산해야 한다(SHALL).

#### Scenario: Case result aggregation

- **WHEN** case result 목록을 평가할 때
- **THEN** 각 case의 detection/action 성공 여부와 전체 요약을 제공해야 한다.

### Requirement: Normal case handling

시스템은 expected incident가 없는 normal case에서 실제 detection도 없으면 detection 성공으로 판정해야 한다(SHALL).

### Requirement: Markdown evaluation output

시스템은 evaluation result를 caller가 지정한 위치에 사람이 검토 가능한 Markdown으로 기록할 수 있어야 한다(SHALL).

#### Scenario: Report write

- **WHEN** 유효한 output path에 report를 쓸 때
- **THEN** 각 case의 expected/actual detection과 action 결과를 확인할 수 있어야 한다.

### Requirement: Evaluation remains outside incident lifecycle

Read-only incident lifecycle은 synthetic evaluation이나 report write를 자동 실행해서는 안 된다(MUST NOT).
