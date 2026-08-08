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

### Requirement: Incident affected assets

시스템은 impact analysis 결과의 downstream assets를 incident의 affected assets에 반영해야 한다(SHALL).

#### Scenario: Affected asset linkage

- **WHEN** downstream nodes가 계산될 때
- **THEN** 반환된 incident의 affected assets는 계산된 영향 범위와 일치해야 한다.
