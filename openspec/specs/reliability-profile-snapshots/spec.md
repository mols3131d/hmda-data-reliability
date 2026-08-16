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

#### Scenario: Column null rate

- **WHEN** partition의 profile column에 null 값이 포함되어 있을 때
- **THEN** 해당 column의 null rate는 `null_count / row_count`와 일치해야 한다.

#### Scenario: Empty partition null rate

- **WHEN** profile 대상 partition의 row count가 0일 때
- **THEN** 요청된 profile column의 null rate는 0.0이어야 한다.

### Requirement: Deterministic schema hash

시스템은 table schema의 column name과 physical type에서 결정적인 schema hash를 생성해야 한다(SHALL).

#### Scenario: Stable schema hash

- **WHEN** 같은 table schema에 대해 schema hash를 반복 계산할 때
- **THEN** 같은 hash를 반환해야 한다.

#### Scenario: Schema change

- **WHEN** column name 또는 type이 변경될 때
- **THEN** schema hash는 변경 전과 달라야 한다.

### Requirement: Freshness metric

시스템은 freshness column이 제공되고 partition에서 timestamp를 측정할 수 있으면 해당 column의 최대 timestamp를 `freshness_at`으로 사용하고 `freshness_status=measured`를 반환해야 한다(SHALL). Freshness column이 없거나 partition에서 값을 측정할 수 없으면 `freshness_at=null`, `freshness_status=unavailable`을 반환해야 하며 `observed_at`을 freshness timestamp로 대체해서는 안 된다(MUST NOT). 측정 timestamp가 `observed_at`보다 미래이면 성공한 profile로 반환해서는 안 된다(MUST NOT).

#### Scenario: Measured Bronze ingestion freshness

- **GIVEN** HMDA Bronze partition에 `ingested_at` 값이 있을 때
- **WHEN** `ingested_at`을 freshness column으로 profile할 때
- **THEN** `freshness_at`은 partition의 `max(ingested_at)`과 일치해야 한다.
- **AND** `freshness_status`는 `measured`여야 한다.

#### Scenario: Missing freshness measurement

- **WHEN** freshness column이 제공되지 않거나 대상 partition의 값이 모두 null일 때
- **THEN** `freshness_at`은 `null`이고 `freshness_status`는 `unavailable`이어야 한다.
- **AND** `observed_at` fallback 또는 `freshness_used_fallback` numeric metric을 생성해서는 안 된다.

#### Scenario: Future freshness measurement

- **GIVEN** partition의 최대 freshness timestamp가 profile `observed_at`보다 미래일 때
- **WHEN** profile snapshot을 계산할 때
- **THEN** 시스템은 해당 measurement를 fresh 상태로 반환하지 않고 profile failure로 종료해야 한다.

### Requirement: Serializable snapshot

Profile snapshot은 detector가 사용할 row count, null rates, schema hash, freshness와 추가 metric을 보존하며 JSON으로 직렬화 가능해야 한다(SHALL).

#### Scenario: Snapshot serialization

- **WHEN** caller가 profile snapshot을 JSON으로 직렬화할 때
- **THEN** detector 입력에 필요한 metric과 freshness 정보가 보존되어야 한다.
