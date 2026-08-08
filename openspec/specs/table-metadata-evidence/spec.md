# table-metadata-evidence Specification

## Purpose

DuckDB table의 schema, column과 row-count metadata를 reliability analysis가 재사용할 수 있는 table metadata evidence로 제공하는 계약을 정의한다.

## Requirements

### Requirement: Table metadata evidence generation

시스템은 DuckDB table metadata를 table-metadata source의 Evidence로 생성해야 한다(SHALL).

#### Scenario: metadata evidence 조회

- **WHEN** 사용자가 table metadata evidence 생성에 table asset과 partition identity를 전달할 때
- **THEN** 시스템은 table asset, partition, observed_at, summary, payload를 가진 Evidence를 반환해야 한다.

### Requirement: Metadata payload contents

시스템은 table metadata evidence payload에 schema hash, column 목록, row count를 포함해야 한다(SHALL).

#### Scenario: payload 검증

- **WHEN** metadata evidence를 생성할 때
- **THEN** payload는 `schema_hash`, `columns`, `row_count` 값을 포함해야 한다.

### Requirement: Metadata lookup error wrapping

시스템은 DuckDB metadata 조회 실패를 reliability 도메인 오류로 변환해야 한다(SHALL).

#### Scenario: 존재하지 않는 table

- **WHEN** 존재하지 않는 table의 metadata evidence를 요청할 때
- **THEN** 시스템은 table metadata 조회 실패를 식별하는 reliability 도메인 오류를 반환해야 한다.
