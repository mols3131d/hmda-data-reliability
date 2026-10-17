# reliability-incident-detection Specification

## Purpose

baseline과 current profile의 차이를 rule 기반 Data Reliability Incident와 연결 evidence로 변환하는 detection 계약을 정의한다.

## Requirements

### Requirement: Rule-based profile comparison

시스템은 비교 가능한 baseline `ProfileSnapshot`과 current `ProfileSnapshot`을 비교해 row count drop, null spike, schema drift와 freshness delay를 각 규칙의 탐지 조건에 따라 독립적으로 평가해야 한다(SHALL). Volume/null의 변화가 없다는 이유로 schema나 freshness 탐지를 생략해서는 안 된다(MUST NOT).

#### Scenario: Normal comparison

- **GIVEN** 행 수와 null rate 및 schema가 같고 current freshness age가 설정한 최대 나이 미만일 때
- **WHEN** volume/null threshold를 각각 0으로 설정해 탐지할 때
- **THEN** incident를 생성하지 않아야 한다.

#### Scenario: Incompatible profile pair

- **WHEN** baseline과 current profile의 asset identity 또는 partition identity가 다를 때
- **THEN** 시스템은 두 profile을 detection 대상으로 받아들이지 않아야 한다.

#### Scenario: Independent freshness and schema rules

- **GIVEN** 행 수와 null rate는 같고 volume/null threshold는 각각 0일 때
- **WHEN** schema hash가 바뀌거나 측정된 current freshness age가 최대 나이 이상일 때
- **THEN** 해당 schema/freshness incident를 생성하고 volume/null incident는 생성하지 않아야 한다.

### Requirement: Volume drop detection

시스템은 baseline row count가 양수이고 current row count가 실제로 감소했으며 감소율이 configured ratio 이상일 때만 `volume_drop` incident를 생성해야 한다(SHALL). Ratio 0을 유효한 설정으로 허용하고 어떤 양의 감소도 탐지해야 한다(SHALL). Baseline row count가 0이면 분모가 없으므로 volume 비교를 제외하고 다른 규칙의 실행은 유지해야 한다(SHALL).

#### Scenario: Material volume drop

- **WHEN** baseline row count가 100, current row count가 40이고 threshold가 0.5일 때
- **THEN** `volume_drop` incident와 baseline/current row count 및 drop ratio evidence를 생성해야 한다.

#### Scenario: Zero threshold without decrease

- **WHEN** baseline row count가 100이고 current row count가 100 이상이며 threshold가 0일 때
- **THEN** `volume_drop` incident를 생성하지 않아야 한다.

#### Scenario: Zero threshold with positive decrease

- **WHEN** baseline row count가 100, current row count가 99이고 threshold가 0일 때
- **THEN** `volume_drop` incident와 drop ratio 0.01 evidence를 생성해야 한다.

#### Scenario: Positive ratio equality

- **WHEN** baseline row count가 100, current row count가 50이고 threshold가 0.5일 때
- **THEN** `volume_drop` incident를 생성해야 한다.

#### Scenario: Zero-row baseline

- **WHEN** baseline row count가 0일 때
- **THEN** `volume_drop` incident를 생성하지 않고 다른 규칙은 독립적으로 평가해야 한다.

### Requirement: Null spike detection

시스템은 column null rate가 비교 기준보다 실제로 증가하고 그 증가량이 configured delta 이상일 때만 `null_spike` incident를 생성해야 한다(SHALL). Delta 0을 유효한 설정으로 허용하고 어떤 양의 증가도 탐지해야 한다(SHALL). Null rate가 같거나 감소한 경우에는 해당 column의 `null_spike` incident를 생성해서는 안 된다(MUST NOT).

#### Scenario: Material null spike

- **WHEN** 한 column의 null rate가 양의 threshold 이상 증가할 때
- **THEN** target column과 baseline/current null rate를 가진 evidence를 생성해야 한다.

#### Scenario: Zero threshold without increase

- **WHEN** 한 column의 null rate가 비교 기준과 같거나 낮고 threshold가 0일 때
- **THEN** 해당 column의 `null_spike` incident를 생성하지 않아야 한다.

#### Scenario: Zero threshold with positive increase

- **WHEN** 한 column의 null rate가 0.125에서 0.25로 증가하고 threshold가 0일 때
- **THEN** 해당 column의 `null_spike` incident와 delta 0.125 evidence를 생성해야 한다.

#### Scenario: Positive delta equality

- **WHEN** 한 column의 null rate가 0.125에서 0.25로 증가하고 threshold가 0.125일 때
- **THEN** 해당 column의 `null_spike` incident를 생성해야 한다.

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
