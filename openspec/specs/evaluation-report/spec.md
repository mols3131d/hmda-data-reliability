# evaluation-report Specification

## Purpose

TBD - created by archiving change add-evaluation-report. Update Purpose after archive.

## Requirements

### Requirement: Synthetic case aggregation

시스템은 synthetic incident case 결과를 받아 detection/action 성공 여부와 전체 성공률을 계산해야 한다(SHALL).

#### Scenario: case별 성공 여부 계산

- **WHEN** case result 목록을 evaluation report로 변환할 때
- **THEN** 각 case는 detection 성공 여부와 action 성공 여부를 가져야 한다.

### Requirement: Normal partition handling

시스템은 expected incident가 없는 normal case에서 detection 결과가 없을 때 성공으로 판정해야 한다(SHALL).

#### Scenario: normal partition 성공

- **WHEN** expected incident가 없고 detected incident도 없는 case를 평가할 때
- **THEN** detection 성공 여부는 true여야 한다.

### Requirement: Markdown report output

시스템은 evaluation 결과를 `evaluation_report.md` Markdown 파일로 내보내야 한다(SHALL).

#### Scenario: report 파일 생성

- **WHEN** evaluation report writer를 실행할 때
- **THEN** 출력 경로에 case별 기대/실제 detection과 action 성공 여부가 표시된 Markdown 파일이 생성되어야 한다.
