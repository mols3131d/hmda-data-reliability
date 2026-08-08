# foundation-baseline Specification

## Purpose

Foundation의 완료 범위와 검증 근거를 현재 repository 상태에 연결하고, 이후 MVP capability의 구현·검증 상태와 독립적인 phase completion boundary를 정의한다.

## Requirements

### Requirement: Foundation source alignment

시스템은 Foundation 목적, 원칙과 완료 범위를 repository의 공식 기준선과 연결해야 한다(SHALL). 공식 기준선은 Foundation 문서의 설명을 반복하지 않고 완료 판단에 필요한 핵심 요구와 근거를 제공해야 한다(MUST).

#### Scenario: Foundation 기준선 입력 확인

- **WHEN** 사용자가 Foundation 기준선을 확인할 때
- **THEN** repository 문서는 `docs/development/foundation/`의 Foundation 문서를 입력 근거로 참조해야 한다.

#### Scenario: 문서 역할 중복 방지

- **WHEN** 사용자가 Foundation 문서, architecture와 OpenSpec의 역할을 비교할 때
- **THEN** Foundation baseline은 phase 완료 계약과 검증 근거만 소유하고 비전, architecture와 상세 domain contract를 중복 정의해서는 안 된다.

### Requirement: Foundation evidence inventory

시스템은 Foundation 완료 근거를 OpenSpec archive, current specs와 검증 command로 추적 가능하게 제공해야 한다(SHALL). Foundation evidence에는 HMDA source ingestion, partition ingestion, dbt analytics, HMDA EDA와 reliability contracts가 포함되어야 한다(MUST).

#### Scenario: 완료된 Foundation capability 확인

- **WHEN** 사용자가 Foundation 완료 근거를 확인할 때
- **THEN** 각 Foundation capability의 current spec과 관련 archive 이력을 추적할 수 있어야 한다.
- **AND** 각 Foundation capability는 검증 가능한 test 또는 command 근거를 가져야 한다.

### Requirement: Foundational EDA readiness

Foundation 완료 전 HMDA EDA는 six-core schema/type compatibility, volume, null baseline, categorical distribution, numeric summary와 complete-key grain coverage를 read-only evidence로 제공해야 한다(SHALL). EDA의 상세 행동 계약은 `hmda-eda-baseline`이 소유하며 Foundation baseline은 이를 중복 정의해서는 안 된다(MUST NOT).

#### Scenario: HMDA 기초 EDA 완료 확인

- **WHEN** 사용자가 Foundation readiness를 검토할 때
- **THEN** current `hmda-eda-baseline` contract를 만족하는 controlled actual-source evidence를 확인할 수 있어야 한다.
- **AND** 이전 execution revision의 evidence를 사용하는 경우 `hmda-eda-baseline`의 evidence applicability 조건을 충족해야 한다.
- **AND** audited revision과 evidence execution revision이 다르면 readiness에서 둘을 구분해 기록해야 한다.

#### Scenario: Contract 기준 확인

- **WHEN** 사용자가 Foundation reliability contract 범위를 확인할 때
- **THEN** `Incident`, `Evidence`, `ProfileSnapshot`, `LineageEvidence`, `Approval`의 current contract가 Foundation evidence inventory에 포함되어야 한다.

### Requirement: Post-Foundation capability separation

시스템은 Foundation completion과 이후 capability의 구현 또는 검증 상태를 분리해야 한다(SHALL). Profile lifecycle, incident detection, impact analysis, remediation, approved recovery, evaluation, Dagster control-plane과 이후 MVP 기능은 Foundation baseline에 명시적으로 포함되지 않는 한 Foundation 완료의 선행조건이 되어서는 안 된다(MUST NOT).

#### Scenario: Non-gating capability 상태 확인

- **WHEN** Foundation 범위 밖 capability가 미구현, 미검증 또는 blocked 상태일 때
- **THEN** 해당 상태는 후속 작업 또는 risk로 기록할 수 있어야 한다.
- **AND** 그 상태만으로 Foundation completion을 미완료로 판정해서는 안 된다.

#### Scenario: 다음 phase 진입

- **WHEN** Foundation readiness가 current evidence에서 `GO`이고 blocker가 없을 때
- **THEN** 이후 OpenSpec Change는 자체 planning과 validation gate에 따라 진행할 수 있어야 한다.

### Requirement: Foundation readiness verification

시스템은 Foundation baseline을 현재 repository revision에서 검증할 수 있는 readiness view를 제공해야 한다(SHALL). readiness는 decision, audited revision, capability coverage, blocker와 재현 가능한 검증 command를 포함해야 하며(MUST), evidence execution revision이 audited revision과 다르면 별도로 기록해야 한다(MUST).

#### Scenario: Readiness 확인

- **WHEN** 사용자가 Foundation readiness를 확인할 때
- **THEN** 완료 decision, 근거 revision, capability별 검증 상태, blocker와 validation command를 확인할 수 있어야 한다.

#### Scenario: OpenSpec history 추적

- **WHEN** 사용자가 Foundation contract가 현재 형태가 된 이력을 확인할 때
- **THEN** original Foundation completion archive와 이후 Foundation 또는 EDA scope를 변경한 archive에서 current specs까지 추적할 수 있어야 한다.
