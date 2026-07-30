# hmda-eda-baseline Specification

## Purpose

TBD - created by archiving change add-hmda-eda-baseline. Update Purpose after archive.

## Requirements

### Requirement: HMDA required schema baseline

노트북은 원천 HMDA CSV를 읽어 `activity_year`, `state_code`, `county_code`, `loan_purpose`, `action_taken`, `loan_amount`, `income`의 존재와 타입 기준 충족 상태를 표시해야 한다(SHALL).

#### Scenario: Required columns가 모두 유효한 경우

- **WHEN** 원천 CSV가 모든 required column과 호환 타입을 포함할 때
- **THEN** 노트북은 각 컬럼의 존재 상태와 추론 타입을 표시해야 한다.
- **AND** schema 상태를 유효로 표시해야 한다.

#### Scenario: Required schema 불일치

- **WHEN** required column이 누락되거나 타입 기준과 호환되지 않을 때
- **THEN** 노트북은 대상 컬럼과 불일치 이유를 포함한 callout을 표시해야 한다.

### Requirement: Volume and null baseline

노트북은 원천 HMDA CSV의 전체 row count, `activity_year`별 row count, required column별 null count와 null rate를 표시해야 한다(SHALL).

#### Scenario: Null baseline 계산

- **WHEN** 원천 CSV를 분석할 때
- **THEN** required column별 null count와 `null_count / total_row_count` null rate를 표시해야 한다.
- **AND** `NA`와 빈 문자열은 null로 해석한 입력 조건을 표시해야 한다.

#### Scenario: Partition volume baseline 계산

- **WHEN** `activity_year` column이 존재하는 원천 CSV를 분석할 때
- **THEN** 노트북은 전체 row count와 `activity_year`별 row count를 표시해야 한다.

### Requirement: Profile evidence mapping

노트북은 `row_count`, `null_rates`, schema 정보, freshness 상태를 포함하는 JSON-serializable EDA evidence 구조를 만들고 화면 출력과 분리해야 한다(SHALL).

#### Scenario: ProfileSnapshot 대응 표시

- **WHEN** EDA 분석을 완료할 때
- **THEN** 노트북은 EDA evidence 필드와 `ProfileSnapshot`의 `row_count`, `null_rates`, `schema_hash`, `freshness_at` 대응을 표시해야 한다.
- **AND** baseline과 current는 비교 역할 label이며 production lifecycle을 실행하지 않음을 표시해야 한다.

### Requirement: Source freshness measurement boundary

노트북은 원천 CSV의 관측 시각이 있을 때만 source freshness를 측정해야 한다(SHALL). 관측 시각이 없으면 freshness를 `미측정`으로 표시해야 한다(MUST).

#### Scenario: Source observation timestamp가 있는 경우

- **WHEN** 원천 CSV에 유효한 `observed_at` timestamp가 있을 때
- **THEN** 노트북은 최대 `observed_at`을 source freshness로 표시해야 한다.

#### Scenario: Source observation timestamp가 없는 경우

- **WHEN** 원천 CSV에 `observed_at`이 없거나 유효 timestamp가 없을 때
- **THEN** 노트북은 source freshness를 `미측정`으로 표시해야 한다.
- **AND** 파일 수정 시각은 filesystem metadata이며 data freshness가 아니고, Bronze `ingested_at`은 별도 raw-table 경로의 ingestion time임을 표시해야 한다.
