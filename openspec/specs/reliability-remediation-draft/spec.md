# reliability-remediation-draft Specification

## Purpose

Incident, evidence와 lineage context에서 RCA와 remediation 제안을 결정적으로 생성하되 recovery를 실행하지 않는 draft 계약을 정의한다.

## Requirements

### Requirement: Structured remediation draft

시스템은 Incident, Evidence와 optional lineage evidence를 입력으로 구조화된 remediation draft를 반환해야 한다(SHALL).

#### Scenario: Draft generation

- **WHEN** 유효한 incident와 evidence가 주어질 때
- **THEN** 결과는 RCA summary와 recommended actions를 가진 draft여야 한다.

### Requirement: Incident-specific actions

시스템은 incident type과 evidence payload를 바탕으로 검증 가능한 recommended action을 결정해야 한다(SHALL).

#### Scenario: Volume drop

- **WHEN** `volume_drop` incident의 draft를 만들 때
- **THEN** source partition validation과 partition backfill 준비 action을 제안해야 한다.

### Requirement: Test, backfill and validation suggestions

Draft는 필요한 경우 analytics test suggestion, backfill action과 validation action을 구분해 제공해야 한다(SHALL).

#### Scenario: Null spike

- **WHEN** `null_spike` incident의 draft를 만들 때
- **THEN** null 관련 quality test suggestion을 포함해야 한다.

### Requirement: Impact context preservation

Lineage evidence가 있으면 downstream assets를 draft의 affected assets에 보존해야 한다(SHALL).

### Requirement: Draft has no recovery side effect

Remediation draft 생성은 approval을 만들거나 data를 변경하거나 recovery를 실행해서는 안 된다(MUST NOT).
