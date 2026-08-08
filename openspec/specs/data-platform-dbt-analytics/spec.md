# data-platform-dbt-analytics Specification

## Purpose

HMDA Bronze source를 분석 가능한 staging과 mart로 변환하고 grain, metric, quality test와 lineage contract를 제공하는 dbt analytics capability를 정의한다.

## Requirements

### Requirement: Bronze source contract

시스템은 `raw.hmda_loans`를 analytics source로 선언하고 downstream model이 해당 source dependency를 추적할 수 있게 해야 한다(SHALL).

#### Scenario: Source lineage

- **WHEN** analytics project가 parse 또는 build될 때
- **THEN** source와 이를 참조하는 staging dependency를 식별할 수 있어야 한다.

### Requirement: HMDA staging contract

시스템은 raw HMDA row를 분석용 staging representation으로 제공해야 한다(SHALL). `activity_year`, `loan_purpose`, `action_taken`, `source_year`는 integer semantics를, `state_code`, `county_code`, `source_file`은 string semantics를 가져야 한다(MUST). `loan_amount`와 `income`의 수치 변환 실패는 row 제거가 아니라 null로 표현되어야 한다(MUST).

#### Scenario: Staging row preservation

- **WHEN** raw row에 nullable 지역 코드 또는 수치 형식 오류가 있을 때
- **THEN** staging은 row를 유지하고 nullable 값 또는 수치 변환 실패를 null로 표현해야 한다.

### Requirement: Loan outcome mart contract

시스템은 `activity_year + state_code + loan_purpose`가 모두 non-null인 staging row를 해당 조합의 grain으로 집계해야 한다(SHALL). grain은 중복되지 않아야 한다(MUST).

다음 metric semantics를 사용해야 한다(MUST).

- `application_count`: grain의 전체 row 수
- `approval_count`: `action_taken IN (1, 2)` row 수
- `denial_count`: `action_taken IN (3, 7)` row 수
- `approval_rate`: `approval_count / application_count`, 소수점 여섯 자리 반올림
- `average_loan_amount`: non-null `loan_amount` 평균
- `average_income`: non-null `income` 평균

#### Scenario: Mart aggregation

- **WHEN** staging data를 mart로 변환할 때
- **THEN** eligible population만 grain별로 집계되어야 한다.
- **AND** metric은 위 정의에 따라 계산되어야 한다.

### Requirement: Analytics quality tests

Analytics project는 source와 model의 필수 값, mart grain null과 duplicate를 검출할 수 있는 quality tests를 가져야 한다(SHALL). 원천 계약상 허용되는 `state_code`와 `county_code` null을 staging failure로 취급해서는 안 된다(MUST NOT).

#### Scenario: Quality test execution

- **WHEN** caller가 analytics build와 tests를 실행할 때
- **THEN** model contract 위반은 성공한 analytics 결과로 보고되어서는 안 된다.

### Requirement: Analytics lineage metadata

Analytics metadata는 Bronze source, staging과 mart의 dependency를 downstream impact analysis가 해석할 수 있게 표현해야 한다(SHALL).

#### Scenario: Downstream dependency lookup

- **WHEN** lineage consumer가 Bronze source의 downstream을 조회할 때
- **THEN** staging과 mart dependency를 순서대로 식별할 수 있어야 한다.

### Requirement: Deterministic rebuild

시스템은 동일 raw input에 같은 analytics transformation을 다시 적용해도 mart row를 누적하지 않고 같은 grain과 metric 결과를 생성해야 한다(SHALL).

#### Scenario: Repeated build

- **WHEN** 동일 raw input으로 analytics build를 반복할 때
- **THEN** mart의 grain set, row count와 metric 결과는 이전 성공 결과와 같아야 한다.
