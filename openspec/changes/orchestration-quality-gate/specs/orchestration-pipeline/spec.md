# orchestration-pipeline Delta Spec (orchestration-quality-gate)

## Delta Purpose

`hmda_data_plane` DAG의 기존 `orchestration-pipeline` spec에 quality gate requirement를 추가한다.

## ADDED Requirements

### Requirement: Data quality gate execution

시스템은 raw load 성공 후 analytics build 이전에 신뢰성 품질 게이트를 실행해야 한다(SHALL). 게이트는 현재 파티션의 프로파일 스냅샷을 생성하고 내장 baseline과 비교해 이상 유형을 탐지해야 한다(MUST).

#### Scenario: Quality gate passes – no anomaly detected

- **GIVEN** 적재된 파티션의 null rate, row count가 baseline 범위 내에 있을 때
- **WHEN** `evaluate_quality_gate` 태스크가 실행될 때
- **THEN** 태스크는 성공(정상 완료)해야 함
- **AND** 다운스트림 analytics build 태스크가 실행되어야 함

#### Scenario: Quality gate fails – anomaly detected

- **GIVEN** 적재된 파티션에서 이상(예: null spike)이 탐지될 때
- **WHEN** `evaluate_quality_gate` 태스크가 실행될 때
- **THEN** 태스크는 명시적으로 실패해야 함
- **AND** 탐지된 인시던트 유형이 실패 메시지에 포함되어야 함
- **AND** 다운스트림 analytics build 태스크는 실행되지 않아야 함

#### Scenario: Quality gate evidence

- **WHEN** quality gate 태스크가 성공 또는 실패로 완료될 때
- **THEN** `source_year`, `asset_name`, `detected_incident_types` 또는 `status: clean`이 로그에 기록되어야 함
