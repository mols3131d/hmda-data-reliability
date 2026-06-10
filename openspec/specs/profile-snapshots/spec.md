# profile-snapshots Specification

## Purpose

DuckDB asset partition의 품질 지표를 계산해 detector 입력용 `ProfileSnapshot` contract로 제공하는 요구사항을 정의한다.

## Requirements

### Requirement: Partition profile snapshot calculation

시스템은 DuckDB asset의 특정 daily partition을 대상으로 row count, null rate, schema hash, freshness 값을 계산해 `ProfileSnapshot` contract로 반환해야 한다(SHALL).

#### Scenario: 유효한 partition profile 생성

- **WHEN** 사용자가 asset table, partition column, partition date를 지정해 profile 계산을 실행할 때
- **THEN** 결과는 `snapshot_id`, `asset_name`, `partition`, `observed_at`, `row_count`, `null_rates`, `schema_hash`, `freshness_at`, `metric_values`를 포함하는 `ProfileSnapshot`이어야 한다.
- **AND** `row_count`는 partition 조건에 맞는 행 수와 일치해야 한다.

### Requirement: Null rate metric calculation

시스템은 지정된 profile columns의 null 비율을 0 이상 1 이하의 값으로 계산해야 한다(SHALL).

#### Scenario: 컬럼별 null rate 계산

- **WHEN** partition profile 대상 컬럼에 null 값이 포함되어 있을 때
- **THEN** `null_rates`는 각 컬럼별 `null_count / row_count` 값을 포함해야 한다.
- **AND** row count가 0이면 null rate는 0.0으로 기록되어야 한다.

### Requirement: Deterministic schema hash

시스템은 DuckDB table schema에서 컬럼명과 타입을 읽어 결정적인 schema hash를 생성해야 한다(SHALL).

#### Scenario: 동일 schema hash 재현

- **WHEN** 같은 table schema에 대해 profile 계산을 반복 실행할 때
- **THEN** `schema_hash`는 같은 값을 반환해야 한다.

#### Scenario: schema 변경 감지 입력

- **WHEN** table schema의 컬럼명 또는 타입이 변경될 때
- **THEN** `schema_hash`는 변경 전 값과 달라져야 한다.

### Requirement: Freshness metric calculation

시스템은 freshness column이 제공된 경우 partition 내 최대 timestamp를 `freshness_at`으로 사용해야 한다(SHALL). freshness column이 제공되지 않거나 값이 없으면 `observed_at`을 fallback으로 사용해야 한다(MUST).

#### Scenario: freshness column 기반 계산

- **WHEN** freshness column이 있는 partition profile을 계산할 때
- **THEN** `freshness_at`은 partition 내 해당 컬럼의 최대 timestamp와 일치해야 한다.

### Requirement: Profile snapshot serialization

시스템은 계산된 `ProfileSnapshot`을 JSON으로 직렬화 가능하게 제공해야 한다(SHALL).

#### Scenario: detector 입력 JSON 생성

- **WHEN** profile 계산 결과를 JSON으로 직렬화할 때
- **THEN** detector가 사용할 수 있는 `row_count`, `null_rates`, `schema_hash`, `freshness_at`, `metric_values` 값이 보존되어야 한다.
