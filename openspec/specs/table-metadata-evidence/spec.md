# table-metadata-evidence Specification

## Purpose
TBD - created by archiving change add-table-metadata-evidence. Update Purpose after archive.
## Requirements
### Requirement: Table metadata evidence generation

시스템은 DuckDB table metadata를 `EvidenceSource.TABLE_METADATA` Evidence로 생성해야 한다(SHALL).

#### Scenario: metadata evidence 조회

- **WHEN** 사용자가 table metadata evidence builder에 table 이름을 전달할 때
- **THEN** 시스템은 table asset, partition token, observed_at, summary, payload를 가진 Evidence를 반환해야 한다.

### Requirement: Metadata payload contents

시스템은 table metadata evidence payload에 schema hash, column 목록, row count를 포함해야 한다(SHALL).

#### Scenario: payload 검증

- **WHEN** metadata evidence를 생성할 때
- **THEN** payload는 `schema_hash`, `columns`, `row_count` 값을 포함해야 한다.

### Requirement: Metadata lookup error wrapping

시스템은 DuckDB metadata 조회 실패를 reliability 도메인 예외로 변환해야 한다(SHALL).

#### Scenario: 존재하지 않는 table

- **WHEN** 존재하지 않는 table의 metadata evidence를 요청할 때
- **THEN** 시스템은 `TableMetadataEvidenceError`를 발생시켜야 한다.

