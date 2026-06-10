## ADDED Requirements

### Requirement: LangGraph remediation workflow

시스템은 Incident, Evidence, LineageEvidence를 입력으로 받아 remediation draft를 생성하는 LangGraph workflow를 제공해야 한다(SHALL).

#### Scenario: workflow 실행

- **WHEN** 사용자가 incident와 evidence를 전달해 remediation workflow를 실행할 때
- **THEN** workflow는 Pydantic `RemediationDraft`를 반환해야 한다.

### Requirement: RCA and action draft

시스템은 incident type과 evidence payload를 해석해 RCA summary와 recommended actions를 생성해야 한다(SHALL).

#### Scenario: volume drop remediation

- **WHEN** `volume_drop` incident의 remediation draft를 생성할 때
- **THEN** recommended actions에는 `validate_source_partition`과 `prepare_partition_backfill`이 포함되어야 한다.

### Requirement: Test, backfill, validation suggestions

시스템은 조치 초안에 dbt test suggestion, backfill action, validation action을 포함해야 한다(SHALL).

#### Scenario: null spike test suggestion

- **WHEN** `null_spike` incident의 remediation draft를 생성할 때
- **THEN** draft는 null 관련 dbt test suggestion을 포함해야 한다.

### Requirement: Impact context preservation

시스템은 LineageEvidence downstream assets를 remediation draft의 affected assets에 보존해야 한다(SHALL).

#### Scenario: affected assets 보존

- **WHEN** impact analysis 결과가 있는 incident의 draft를 생성할 때
- **THEN** draft affected assets는 LineageEvidence downstream assets와 일치해야 한다.
