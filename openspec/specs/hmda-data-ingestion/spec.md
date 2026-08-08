# hmda-data-ingestion Specification

## Purpose

HMDA 원천 파일을 발견·검증하고 Bronze dataset으로 전체 또는 partition 단위 적재하며, 원천 값과 provenance를 보존하는 ingestion 계약을 정의한다.

## Requirements

### Requirement: Source discovery

시스템은 configured source root에서 HMDA CSV와 Parquet 파일만 적재 후보로 발견하고 파일명 기준의 결정적인 순서로 처리해야 한다(SHALL). 지원하지 않는 파일은 적재 대상에서 제외해야 한다(MUST).

#### Scenario: Supported source discovery

- **WHEN** source root에 CSV, Parquet와 기타 파일이 함께 있을 때
- **THEN** CSV와 Parquet만 정렬된 적재 후보로 반환되어야 한다.

### Requirement: Source contract validation

시스템은 적재 전에 `activity_year`, `state_code`, `county_code`, `loan_purpose`, `action_taken`, `loan_amount`, `income` 컬럼의 존재를 검증해야 한다(SHALL). 필수 컬럼이 누락된 입력을 성공한 적재로 처리해서는 안 된다(MUST NOT).

#### Scenario: Missing required column

- **WHEN** 적재 대상 파일에 필수 컬럼이 없을 때
- **THEN** 시스템은 누락 컬럼을 식별할 수 있는 HMDA data validation failure로 종료해야 한다.

### Requirement: Bronze load with provenance

시스템은 유효한 원천 행을 `raw.hmda_loans`에 적재하고 `source_file`, `source_file_name`, `source_year`, `ingested_at` provenance를 함께 보존해야 한다(SHALL).

#### Scenario: Full source load

- **WHEN** 유효한 source set을 전체 적재할 때
- **THEN** Bronze dataset에는 원천 행과 provenance가 함께 저장되어야 한다.
- **AND** 같은 입력을 다시 전체 적재해도 행이 누적되어서는 안 된다.

### Requirement: Partition replacement

시스템은 `source_year`와 optional `source_file`로 대상 partition을 선택해 해당 범위만 교체할 수 있어야 한다(SHALL). 교체는 기존 범위를 제거하고 새 범위를 반영하는 하나의 원자적 결과로 끝나야 한다(MUST).

#### Scenario: Year partition reload

- **WHEN** 같은 `source_year` partition을 동일 입력으로 반복 적재할 때
- **THEN** 대상 partition의 최종 행 집합과 행 수는 한 번 적재한 결과와 같아야 한다.

#### Scenario: File-scoped reload

- **WHEN** `source_file`이 지정된 partition 적재를 실행할 때
- **THEN** 지정된 파일 범위만 교체 대상이 되어야 한다.

### Requirement: Source value preservation

시스템은 원천의 null, 코드값과 수치 이상치를 정규화하거나 품질 판단으로 제거하지 않고 Bronze에 보존해야 한다(SHALL).

#### Scenario: Quality outlier input

- **WHEN** 입력에 음수 소득, 큰 대출 금액 또는 알 수 없는 코드값이 있을 때
- **THEN** 필수 구조 계약을 만족하는 행은 품질 분석 대상이 될 수 있도록 적재되어야 한다.
