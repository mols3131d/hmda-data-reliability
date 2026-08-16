# reliability-incident-detection Specification

## Purpose

baseline과 current profile의 차이를 rule 기반 Data Reliability Incident와 연결 evidence로 변환하는 detection 계약을 정의한다.

## Requirements

### Requirement: Rule-based profile comparison

시스템은 비교 가능한 baseline `ProfileSnapshot`과 current `ProfileSnapshot`을 비교해 row count drop, null spike, schema drift와 freshness delay를 탐지해야 한다(SHALL).

#### Scenario: Normal comparison

- **WHEN** profile 차이가 configured threshold를 넘지 않을 때
- **THEN** incident를 생성하지 않아야 한다.

#### Scenario: Incompatible profile pair

- **WHEN** baseline과 current profile의 asset identity 또는 partition identity가 다를 때
- **THEN** 시스템은 두 profile을 detection 대상으로 받아들이지 않아야 한다.

### Requirement: Volume drop detection

시스템은 current row count가 baseline 대비 configured ratio 이상 감소하면 `volume_drop` incident를 생성해야 한다(SHALL).

#### Scenario: Material volume drop

- **WHEN** baseline row count가 100, current row count가 40이고 threshold가 0.5일 때
- **THEN** `volume_drop` incident와 baseline/current row count 및 drop ratio evidence를 생성해야 한다.

### Requirement: Null spike detection

시스템은 column null rate 증가량이 configured delta 이상이면 `null_spike` incident를 생성해야 한다(SHALL).

#### Scenario: Material null spike

- **WHEN** 한 column의 null rate가 threshold 이상 증가할 때
- **THEN** target column과 baseline/current null rate를 가진 evidence를 생성해야 한다.

### Requirement: Schema drift detection

시스템은 baseline과 current schema hash가 다르면 `schema_drift` incident를 생성해야 한다(SHALL).

#### Scenario: Schema hash change

- **WHEN** baseline과 current의 schema hash가 다를 때
- **THEN** `schema_drift` incident와 두 schema hash를 추적할 수 있는 evidence를 생성해야 한다.

### Requirement: Freshness delay detection

시스템은 current profile의 freshness measurement가 `measured`이면 `freshness_age = current.observed_at - current.freshness_at`을 계산하고 configured `freshness_max_age_minutes` 이상일 때 `freshness_delay` incident를 생성해야 한다(SHALL). 판정은 baseline freshness 차이가 아니라 current age를 사용해야 한다(MUST). Current measurement가 `unavailable`이면 freshness incident를 생성해서는 안 되지만 다른 detection rule의 실행을 막아서도 안 된다(MUST NOT). Evidence는 `observed_at`, `freshness_at`, `freshness_status`, `freshness_age_minutes`와 `max_age_minutes`를 포함해야 한다(SHALL).

#### Scenario: Age at exact max-age boundary

- **GIVEN** current freshness timestamp가 `observed_at`보다 configured max age만큼 과거일 때
- **WHEN** profile detection을 실행할 때
- **THEN** `freshness_delay` incident와 exact age/threshold evidence를 생성해야 한다.

#### Scenario: Age below max-age boundary

- **GIVEN** current freshness age가 configured max age보다 작을 때
- **WHEN** profile detection을 실행할 때
- **THEN** `freshness_delay` incident를 생성해서는 안 된다.

#### Scenario: Unchanged timestamp becomes stale

- **GIVEN** baseline과 current의 `freshness_at`이 같지만 current `observed_at` 기준 age가 max age 이상일 때
- **WHEN** profile detection을 실행할 때
- **THEN** baseline과의 timestamp 차이가 없어도 `freshness_delay` incident를 생성해야 한다.

#### Scenario: Unavailable freshness measurement

- **GIVEN** current profile의 freshness status가 `unavailable`일 때
- **WHEN** profile detection을 실행할 때
- **THEN** freshness measurement가 fresh하다고 보고하거나 `freshness_delay` incident를 생성해서는 안 된다.
- **AND** row count, null rate와 schema detection은 정상적으로 계속되어야 한다.

### Requirement: Incident and evidence linkage

탐지된 각 incident는 같은 detection result에서 생성된 최소 하나의 evidence를 참조해야 한다(SHALL).

#### Scenario: Evidence linkage

- **WHEN** detector가 incident를 생성할 때
- **THEN** incident evidence reference는 함께 반환된 evidence identity와 일치해야 한다.
