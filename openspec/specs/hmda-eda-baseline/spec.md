# hmda-eda-baseline Specification

## Purpose

HMDA 원천 CSV를 read-only로 탐색해 six-core descriptive evidence를 생성하고, 같은 계산 경로의 correctness와 controlled actual-source observation을 검증한다.

## Requirements

### Requirement: Parse-integrity baseline input

`analyze_hmda_csv`는 입력 CSV의 존재를 확인하고 DuckDB parse 오류가 발생하면 partial evidence를 반환해서는 안 된다(MUST).

#### Scenario: 입력 파일이 없거나 파싱할 수 없는 경우

- **WHEN** 입력 파일이 없거나 DuckDB가 읽을 수 없는 행을 만날 때
- **THEN** entrypoint는 원인을 식별하는 오류를 반환해야 한다.
- **AND** volume 또는 null baseline을 성공 결과로 반환해서는 안 된다.

### Requirement: Six-core schema, volume and null baseline

EDA는 `activity_year`, `state_code`, `loan_purpose`, `action_taken`, `loan_amount`, `income`의 type family compatibility, 전체 row count, `activity_year`별 row count, null count와 null rate를 제공해야 한다(SHALL). `county_code`는 EDA type compatibility 또는 metric 대상에 포함해서는 안 된다(MUST NOT).

#### Scenario: Six-core source is compatible

- **WHEN** source가 호환되는 여섯 core column을 포함할 때
- **THEN** EDA는 각 column의 inferred type과 valid status를 반환해야 한다.
- **AND** `NA`와 빈 문자열을 null로 해석해야 한다.

#### Scenario: Core column is absent or incompatible

- **WHEN** 여섯 core column 중 하나가 없거나 type family가 호환되지 않을 때
- **THEN** EDA는 대상 column을 식별하는 validation failure로 종료해야 한다.
- **AND** partial evidence를 반환해서는 안 된다.

### Requirement: Descriptive distributions and numeric summaries

EDA는 `state_code`, `loan_purpose`, `action_taken`의 observed non-null value별 count와 전체 row 대비 share를 제공해야 한다(SHALL). `loan_amount`와 `income`에는 non-null count, min, p25, median, p75와 max를 제공해야 한다(SHALL). 원천 값은 정제, clipping 또는 anomaly 분류해서는 안 된다(MUST NOT).

#### Scenario: Observed values are preserved

- **WHEN** EDA가 유효한 source를 분석할 때
- **THEN** observed categorical value는 변환 없이 count되어야 한다.
- **AND** numeric summary는 null을 제외한 원천 값으로 계산되어야 한다.

### Requirement: Complete-key grain coverage

EDA는 `activity_year + state_code + loan_purpose`가 모두 non-null인 row의 distinct group count, 하나 이상 null인 row count와 complete-key coverage rate를 제공해야 한다(SHALL). distinct group count는 complete-key row만 대상으로 계산해야 한다(MUST).

#### Scenario: Grain key includes nulls

- **WHEN** grain key 일부가 null인 source를 분석할 때
- **THEN** null-key row는 distinct group count에서 제외되어야 한다.
- **AND** coverage rate는 complete-key row count를 전체 row count로 나눈 값이어야 한다.

### Requirement: Reusable Python evidence boundary

시스템은 CSV path와 명시적인 DuckDB resource 설정을 입력받아 JSON-serializable 및 YAML-exportable evidence를 반환하는 Python entrypoint를 제공해야 한다(SHALL). `duration_seconds`는 모든 retained aggregate 계산 시간을 포함해야 한다(MUST). anomaly, freshness, schema hash와 Profile mapping evidence를 계산하거나 반환해서는 안 된다(MUST NOT).

#### Scenario: Shared calculation path

- **WHEN** automated test 또는 exploration API가 EDA를 실행할 때
- **THEN** `analyze_hmda_csv`를 호출해야 한다.
- **AND** schema, volume, null, distributions, numeric summaries와 grain coverage를 검증하거나 직렬화해야 한다.

### Requirement: Read-only resource lifecycle

EDA entrypoint는 원천 파일과 데이터베이스를 수정하지 않아야 하며(MUST), 성공 또는 실패와 관계없이 자신이 연 DuckDB connection을 닫아야 한다(MUST).

### Requirement: Actual-source observation

actual-source observation은 한 controlled run에서 portable JSON과 그 JSON에서 파생한 Markdown summary를 생성해야 한다(SHALL). 두 artifact는 source ID, SHA-256, repository revision, execution timestamp, total duration과 같은 key metrics를 기록해야 한다(MUST).

#### Scenario: Evidence consistency

- **WHEN** actual-source observation을 수행할 때
- **THEN** Markdown의 income null count와 grain distinct group count는 같은 JSON 값과 일치해야 한다.
- **AND** absolute source path와 temporary directory는 canonical evidence에 포함되어서는 안 된다.
