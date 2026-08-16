# hmda-data-synthetic-defects Specification

## Purpose

HMDA reliability 동작을 검증할 수 있도록 원천을 수정하지 않고 결정적인 synthetic defect 파일을 생성하는 계약을 정의한다.

## Requirements

### Requirement: Isolated synthetic output

시스템은 입력 HMDA 파일을 변경하지 않고 caller가 지정한 output root 아래에 synthetic Parquet를 생성해야 한다(SHALL). case name은 output root 밖의 경로를 가리킬 수 없어야 한다(MUST).

#### Scenario: Synthetic case output

- **WHEN** 유효한 source와 case name으로 synthetic case를 생성할 때
- **THEN** 결과는 output root 아래의 별도 Parquet 파일이어야 한다.
- **AND** source 파일은 변경되지 않아야 한다.

#### Scenario: Output path traversal

- **WHEN** case name이 output root 밖의 경로를 가리키도록 요청될 때
- **THEN** 시스템은 synthetic case 생성을 거부하고 output root 밖의 파일을 변경해서는 안 된다.

### Requirement: Row count drop case

시스템은 `0 < sample_fraction <= 1` 범위에서 `activity_year` 분포를 유지하는 row-count drop case를 생성할 수 있어야 한다(SHALL).

#### Scenario: Stratified row reduction

- **WHEN** 여러 `activity_year`를 가진 source에 row-count drop을 적용할 때
- **THEN** 각 연도는 가능한 경우 최소 한 행을 유지하면서 결정적으로 축소되어야 한다.

### Requirement: Null spike case

시스템은 존재하는 target column에 지정 비율의 null 증가를 주입할 수 있어야 한다(SHALL).

#### Scenario: Income null spike

- **WHEN** `income`에 유효한 null fraction을 적용할 때
- **THEN** 결과 파일의 `income` null 비율은 원본보다 검증 가능하게 증가해야 한다.

#### Scenario: Missing target column

- **WHEN** source에 존재하지 않는 target column에 null spike를 요청할 때
- **THEN** 시스템은 synthetic case failure로 요청을 거부해야 한다.

### Requirement: Schema drift case

시스템은 target column의 physical type을 변경해 schema incompatibility를 재현할 수 있어야 한다(SHALL).

#### Scenario: Loan amount type drift

- **WHEN** `loan_amount`에 schema drift를 적용할 때
- **THEN** 결과 파일에서 해당 column의 type은 원본과 달라져야 한다.
