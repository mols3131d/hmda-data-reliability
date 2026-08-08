# reliability-evidence-table-metadata Specification

## Purpose

Table schema, columns와 row count metadata를 reliability analysis가 참조 가능한 evidence로 제공하는 계약을 정의한다.

## Requirements

### Requirement: Table metadata evidence

시스템은 target table과 partition identity에 대해 table metadata source의 evidence를 생성해야 한다(SHALL).

#### Scenario: Metadata evidence lookup

- **WHEN** 유효한 table asset과 partition이 주어질 때
- **THEN** evidence는 asset, partition, observation time, summary와 payload를 포함해야 한다.

### Requirement: Metadata payload

Table metadata evidence payload는 schema hash, column 목록과 row count를 포함해야 한다(SHALL).

### Requirement: Metadata failure boundary

Metadata lookup failure는 reliability domain이 처리할 수 있는 failure로 노출되어야 한다(SHALL).

#### Scenario: Missing table

- **WHEN** 존재하지 않는 table의 metadata evidence를 요청할 때
- **THEN** lookup failure를 식별할 수 있는 reliability failure로 종료해야 한다.
