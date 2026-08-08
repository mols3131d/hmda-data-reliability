# reliability-incident-detection Specification

## Purpose

baseline과 current profile의 차이를 rule 기반 Data Reliability Incident와 연결 evidence로 변환하는 detection 계약을 정의한다.

## Requirements

### Requirement: Rule-based profile comparison

시스템은 baseline `ProfileSnapshot`과 current `ProfileSnapshot`을 비교해 row count drop, null spike, schema drift와 freshness delay를 탐지해야 한다(SHALL).

#### Scenario: Normal comparison

- **WHEN** profile 차이가 configured threshold를 넘지 않을 때
- **THEN** incident를 생성하지 않아야 한다.

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

### Requirement: Freshness delay detection

시스템은 current freshness가 baseline보다 configured threshold 이상 지연되면 `freshness_delay` incident를 생성해야 한다(SHALL).

### Requirement: Incident and evidence linkage

탐지된 각 incident는 같은 detection result에서 생성된 최소 하나의 evidence를 참조해야 한다(SHALL).

#### Scenario: Evidence linkage

- **WHEN** detector가 incident를 생성할 때
- **THEN** incident evidence reference는 함께 반환된 evidence identity와 일치해야 한다.
