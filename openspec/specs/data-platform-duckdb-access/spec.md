# data-platform-duckdb-access Specification

## Purpose

로컬 DuckDB 연결 수명, schema와 table metadata 접근, 동적 SQL 식별자와 리터럴 표현을 일관된 플랫폼 경계로 제공하는 계약을 정의한다.

## Requirements

### Requirement: Managed DuckDB connection

시스템은 caller가 파일 기반 또는 격리된 in-memory DuckDB 연결을 선택할 수 있게 하고, 관리 범위를 벗어날 때 열린 연결을 닫아야 한다(SHALL).

#### Scenario: Isolated in-memory connection

- **WHEN** caller가 database path 없이 연결을 요청할 때
- **THEN** 시스템은 다른 파일 기반 database와 독립된 in-memory 연결을 제공해야 한다.

### Requirement: Schema and table metadata access

시스템은 지정한 schema의 존재를 보장하고 table의 row count와 column names를 조회할 수 있어야 한다(SHALL).

#### Scenario: Existing table metadata

- **WHEN** caller가 존재하는 table의 metadata를 조회할 때
- **THEN** row count와 column names를 해당 table 상태와 일치하게 반환해야 한다.

### Requirement: Safe SQL identifier representation

시스템은 동적 schema, table과 column 식별자를 DuckDB 식별자 규칙에 맞게 escape해야 하며(SHALL), 비어 있거나 null 문자를 포함한 식별자는 거부해야 한다(MUST).

#### Scenario: Quoted identifier

- **WHEN** identifier에 quote 문자가 포함되어 있을 때
- **THEN** 해당 문자는 DuckDB 식별자 규칙에 맞게 escape되어야 한다.

#### Scenario: Invalid identifier

- **WHEN** identifier가 비어 있거나 null 문자를 포함할 때
- **THEN** 시스템은 유효하지 않은 식별자로 거부해야 한다.

### Requirement: Safe SQL string literal representation

시스템은 직접 표현해야 하는 SQL string literal의 single quote를 DuckDB 규칙에 맞게 escape해야 한다(SHALL).

#### Scenario: Quoted string literal

- **WHEN** string literal 값에 single quote가 포함되어 있을 때
- **THEN** 결과는 원래 값을 보존하면서 DuckDB가 해석할 수 있도록 escape되어야 한다.
