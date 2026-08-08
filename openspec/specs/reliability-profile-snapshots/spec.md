# reliability-profile-snapshots Specification

## Purpose

asset partition의 row count, null rate, schema와 freshness 지표를 계산해 incident detection 입력용 profile snapshot으로 제공하는 계약을 정의한다.

## Requirements

### Requirement: Partition profile snapshot

시스템은 지정된 asset partition의 row count, null rates, schema hash와 freshness를 계산한 profile snapshot을 반환해야 한다(SHALL). Partition identity는 대상 dataset contract에 맞는 date, integer 또는 string 값을 사용할 수 있어야 한다(MUST).

#### Scenario: HMDA year partition

- **WHEN** HMDA asset을 연도 partition identity로 profile할 때
- **THEN** 해당 partition의 row count와 metric만 snapshot에 포함되어야 한다.

### Requirement: Null rate metrics

시스템은 지정된 profile column별 null 비율을 0 이상 1 이하로 계산해야 한다(SHALL). partition row count가 0이면 null rate는 0.0이어야 한다(MUST).

#### Scenario: Empty partition null rate

- **WHEN** profile 대상 partition의 row count가 0일 때
- **THEN** 요청된 profile column의 null rate는 0.0이어야 한다.

### Requirement: Deterministic schema hash

시스템은 table schema의 column name과 physical type에서 결정적인 schema hash를 생성해야 한다(SHALL).

#### Scenario: Schema change

- **WHEN** column name 또는 type이 변경될 때
- **THEN** schema hash는 변경 전과 달라야 한다.

### Requirement: Freshness metric

시스템은 freshness column이 제공되면 partition의 최대 timestamp를 `freshness_at`으로 사용해야 한다(SHALL). freshness column이 없거나 측정값이 없으면 `observed_at`을 fallback으로 사용해야 한다(MUST).

#### Scenario: Missing freshness measurement

- **WHEN** partition에서 freshness 값을 측정할 수 없을 때
- **THEN** snapshot은 `observed_at`을 `freshness_at`으로 사용하고 fallback 사용 여부를 metric으로 식별할 수 있어야 한다.

### Requirement: Serializable snapshot

Profile snapshot은 detector가 사용할 row count, null rates, schema hash, freshness와 추가 metric을 보존하며 JSON으로 직렬화 가능해야 한다(SHALL).

#### Scenario: Snapshot serialization

- **WHEN** caller가 profile snapshot을 JSON으로 직렬화할 때
- **THEN** detector 입력에 필요한 metric과 freshness 정보가 보존되어야 한다.
