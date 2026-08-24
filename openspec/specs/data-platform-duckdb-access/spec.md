# data-platform-duckdb-access Specification

## Purpose

로컬 DuckDB 연결 수명, schema와 table metadata 접근, 동적 SQL 식별자와 리터럴 표현을 일관된 플랫폼 경계로 제공하는 계약을 정의한다.

## Requirements

### Requirement: Managed DuckDB connection

시스템은 caller가 파일 기반 또는 격리된 in-memory DuckDB 연결과 read-only mode를 선택할 수 있게 하고, 관리 범위를 벗어날 때 열린 연결을 닫아야 한다(SHALL).

#### Scenario: Isolated in-memory connection

- **WHEN** caller가 database path 없이 연결을 요청할 때
- **THEN** 시스템은 다른 파일 기반 database와 독립된 in-memory 연결을 제공해야 한다.

#### Scenario: Read-only connection

- **WHEN** caller가 기존 database에 read-only mode로 연결할 때
- **THEN** 시스템은 해당 연결을 read-only로 열어 write operation이 허용되지 않게 해야 한다.

### Requirement: Schema and table metadata access

시스템은 지정한 schema의 존재를 보장하고 table의 row count와 column names를 조회할 수 있어야 한다(SHALL).

#### Scenario: Schema initialization

- **WHEN** caller가 아직 존재하지 않는 schema의 존재를 보장하도록 요청할 때
- **THEN** 이후 같은 연결에서 해당 schema를 사용할 수 있어야 한다.

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

### Requirement: Local database mutation lock

시스템은 file-based DuckDB의 canonical resolved database path별 cooperative exclusive mutation lock을 제공해야 한다(SHALL). 시스템의 managed writer는 target state 확인과 first mutation 사이에 다른 managed writer가 끼어들지 못하도록 같은 lock을 사용해야 한다(SHALL). Lock I/O failure는 caller가 식별할 수 있는 typed Data Platform failure로 노출해야 하며(SHALL), lock release failure가 body의 원래 exception을 가려서는 안 된다(MUST NOT).

#### Scenario: Serialized file-database writers

- **GIVEN** 두 managed writer가 같은 physical DuckDB file을 변경하려 할 때
- **WHEN** 첫 writer가 mutation lock을 보유할 때
- **THEN** 두 번째 writer는 첫 writer의 mutation boundary가 성공 또는 실패로 종료되고 lock이 해제된 뒤에만 target state를 확인하고 mutation을 진행할 수 있어야 한다.

#### Scenario: Canonically equivalent database paths

- **GIVEN** relative, absolute 또는 symlink path가 canonical resolution 뒤 같은 DuckDB path를 식별할 때
- **WHEN** 두 managed writer가 mutation lock을 요청할 때
- **THEN** 두 요청은 같은 mutation lock을 사용해야 한다.

#### Scenario: In-memory database

- **WHEN** isolated in-memory DuckDB connection이 mutation boundary를 요청할 때
- **THEN** file lock을 생성하지 않고 해당 connection scope의 mutation을 진행할 수 있어야 한다.

#### Scenario: Lock acquisition failure

- **WHEN** file-based database의 mutation lock을 생성하거나 획득할 수 없을 때
- **THEN** target mutation 전에 typed Data Platform failure로 종료해야 한다.

#### Scenario: Body failure preservation

- **GIVEN** mutation body와 lock release가 모두 실패할 때
- **WHEN** lock context를 종료할 때
- **THEN** caller는 mutation body의 원래 failure를 관찰할 수 있어야 한다.
