# reliability-impact-analysis Specification

## Purpose

analytics lineage에서 incident upstream의 downstream 영향을 계산하고 lineage evidence와 affected assets를 연결하는 계약을 정의한다.

## Requirements

### Requirement: Downstream lineage traversal

시스템은 analytics dependency metadata를 읽어 incident upstream asset의 downstream nodes를 계산해야 한다(SHALL).

#### Scenario: Bronze source impact

- **WHEN** HMDA Bronze source의 downstream을 분석할 때
- **THEN** 해당 source에 의존하는 staging과 mart node를 식별할 수 있어야 한다.

### Requirement: Lineage evidence

시스템은 upstream asset, downstream assets와 사용한 lineage artifact identity를 lineage evidence로 반환해야 한다(SHALL).

#### Scenario: Evidence generation

- **WHEN** impact analysis가 성공할 때
- **THEN** 결과는 upstream과 downstream 및 lineage 근거를 추적할 수 있어야 한다.

### Requirement: Lineage artifact validation

시스템은 downstream 영향 분석에 사용하는 lineage artifact를 읽을 수 있고 유효한 상태인지 확인해야 하며(SHALL), 필수 artifact가 없거나 해석할 수 없으면 성공한 impact analysis로 보고해서는 안 된다(MUST NOT).

#### Scenario: Invalid manifest

- **WHEN** lineage manifest를 정상적으로 해석할 수 없을 때
- **THEN** 시스템은 원인을 식별할 수 있는 reliability impact failure로 종료해야 한다.

#### Scenario: Missing run results

- **WHEN** required run-results artifact가 존재하지 않을 때
- **THEN** 시스템은 해당 artifact 없이 lineage evidence를 성공으로 생성해서는 안 된다.

### Requirement: Incident affected assets

시스템은 impact analysis 결과의 downstream assets를 incident의 affected assets에 반영해야 한다(SHALL).

#### Scenario: Affected asset linkage

- **WHEN** downstream nodes가 계산될 때
- **THEN** 반환된 incident의 affected assets는 계산된 영향 범위와 일치해야 한다.
