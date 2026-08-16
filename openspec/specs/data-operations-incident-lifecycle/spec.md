# data-operations-incident-lifecycle Specification

## Purpose

caller-supplied baseline과 실제 current profile을 연결해 detection, impact와 remediation draft를 순서대로 조합하는 read-only application lifecycle 계약을 정의한다.

## Requirements

### Requirement: Actual profile comparison

시스템은 caller가 제공한 baseline `ProfileSnapshot`과 target partition에서 새로 측정한 current `ProfileSnapshot`을 비교해야 한다(SHALL). 운영 lifecycle에서 current snapshot 값을 합성해서는 안 된다(MUST NOT).

#### Scenario: Compatible baseline comparison

- **WHEN** 유효한 operation request와 baseline profile이 주어질 때
- **THEN** request target에서 current profile을 계산해 detector 입력으로 사용해야 한다.

#### Scenario: Incompatible baseline

- **WHEN** baseline과 current의 asset 또는 partition이 다를 때
- **THEN** lifecycle은 비교 대상을 식별할 수 있는 data-operations failure로 종료해야 한다.

### Requirement: Complete incident analysis

시스템은 탐지된 모든 incident에 대해 impact analysis와 remediation draft를 생성해야 한다(SHALL).

#### Scenario: Multiple detections

- **WHEN** 둘 이상의 incident가 탐지될 때
- **THEN** 각 incident의 evidence와 lineage evidence가 결과에 포함되어야 한다.
- **AND** affected assets와 remediation actions는 탐지 순서를 유지하며 중복 없이 요약되어야 한다.

#### Scenario: No detection

- **WHEN** detection threshold를 넘는 incident가 없을 때
- **THEN** incident, evidence, affected asset과 action 목록은 비어 있어야 한다.
- **AND** impact analysis를 실행하지 않아야 한다.

### Requirement: Read-only lifecycle boundary

Lifecycle은 approval 생성, partition backfill, post-backfill validation, synthetic evaluation 또는 report write를 실행해서는 안 된다(MUST NOT).

#### Scenario: Lifecycle with incident

- **WHEN** lifecycle이 incident와 remediation draft를 생성할 때
- **THEN** target data를 변경하거나 approval을 생성하거나 evaluation report를 쓰지 않아야 한다.

### Requirement: Lifecycle result

시스템은 실제 관측값과 detection, impact, remediation 요약을 하나의 lifecycle result로 반환해야 한다(SHALL). Detection이 있으면 각 incident의 target partition, observed target state, remediation candidate requirement와 판단에 사용한 dbt artifact projection을 recovery proposal 입력으로 식별할 수 있어야 한다(SHALL).

#### Scenario: Return summary

- **WHEN** lifecycle이 완료될 때
- **THEN** 결과는 metadata row count, baseline/current row count, incident types, evidence refs, affected assets와 remediation actions를 포함해야 한다.

#### Scenario: Volume-drop recovery inputs

- **WHEN** target partition에서 `volume_drop` incident와 remediation draft가 생성될 때
- **THEN** 결과는 incident, target partition, observed target state, candidate requirement와 dbt artifact projection identity를 포함해야 한다.

#### Scenario: Clean baseline result

- **WHEN** detection threshold를 넘는 incident가 없을 때
- **THEN** incident, remediation draft와 recovery proposal 입력은 비어 있어야 한다.

### Requirement: Configured detection thresholds

시스템은 caller가 incident lifecycle에 explicit detection thresholds를 제공할 수 있어야 하며 current profile detection에 같은 값을 전달해야 한다(SHALL). Caller가 thresholds를 제공하지 않으면 canonical default thresholds를 사용해야 한다(SHALL).

#### Scenario: Explicit freshness max age

- **GIVEN** caller가 `freshness_max_age_minutes`를 포함한 thresholds를 제공할 때
- **WHEN** read-only lifecycle이 current profile을 평가할 때
- **THEN** freshness detection evidence와 판정은 제공된 max age를 사용해야 한다.

#### Scenario: Default detection thresholds

- **WHEN** caller가 별도 thresholds 없이 lifecycle을 실행할 때
- **THEN** 기존 volume, null, schema와 freshness default threshold 동작을 유지해야 한다.
