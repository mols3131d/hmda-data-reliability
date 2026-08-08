# hmda-data-eda-descriptive-evidence Specification

## Purpose

HMDA 원천을 read-only로 탐색해 six-core schema, volume, null, distribution, numeric와 grain coverage evidence를 일관된 계산 경로로 제공하는 계약을 정의한다.

## Requirements

### Requirement: Parse-integrity input

EDA는 입력 파일이 없거나 전체 입력을 정상적으로 parse할 수 없을 때 partial evidence를 성공 결과로 반환해서는 안 된다(MUST NOT).

#### Scenario: Invalid source

- **WHEN** 입력이 없거나 parse failure가 발생할 때
- **THEN** EDA는 원인을 식별하는 failure로 종료해야 한다.

### Requirement: Six-core schema, volume and null evidence

EDA는 `activity_year`, `state_code`, `loan_purpose`, `action_taken`, `loan_amount`, `income`의 type compatibility, 전체 row count, 연도별 row count, null count와 null rate를 제공해야 한다(SHALL). `county_code` 존재 검증은 ingestion contract가 소유하며 EDA six-core metric 대상에는 포함하지 않아야 한다(MUST NOT).

#### Scenario: Compatible source

- **WHEN** source가 호환되는 six-core column을 포함할 때
- **THEN** 각 column의 type status와 volume/null evidence가 반환되어야 한다.
- **AND** `NA`와 빈 문자열은 null로 해석되어야 한다.

### Requirement: Descriptive distributions and numeric summaries

EDA는 `state_code`, `loan_purpose`, `action_taken`의 observed non-null value별 count와 전체 row 대비 share를 제공해야 한다(SHALL). `loan_amount`와 `income`에는 non-null count, min, p25, median, p75와 max를 제공해야 한다(SHALL).

#### Scenario: Source values remain descriptive input

- **WHEN** 유효한 source를 분석할 때
- **THEN** categorical value는 변환 없이 집계되어야 한다.
- **AND** numeric summary는 null을 제외한 원천 값으로 계산되어야 한다.

### Requirement: Complete-key grain coverage

EDA는 `activity_year + state_code + loan_purpose`가 모두 non-null인 row의 distinct group count, incomplete-key row count와 coverage rate를 제공해야 한다(SHALL).

#### Scenario: Incomplete grain keys

- **WHEN** grain key 일부가 null인 row가 있을 때
- **THEN** 해당 row는 distinct group count에서 제외되어야 한다.
- **AND** coverage rate는 complete-key row count를 전체 row count로 나눈 값이어야 한다.

### Requirement: Portable evidence boundary

시스템은 source path와 명시적 resource 설정을 입력받아 JSON-serializable evidence를 반환하고 YAML로 export할 수 있어야 한다(SHALL). 시각화가 필요하면 동일 evidence에서 정적 이미지 또는 독립 실행형 HTML을 생성할 수 있어야 한다(SHALL).

#### Scenario: Shared calculation path

- **WHEN** automated test와 exploration 경로가 같은 source를 분석할 때
- **THEN** 둘은 같은 descriptive calculation boundary를 사용해야 한다.

### Requirement: Read-only resource lifecycle

EDA는 source와 database를 수정하지 않아야 하며(MUST), 성공 또는 실패와 관계없이 자신이 연 resource를 정리해야 한다(MUST).

#### Scenario: Analysis resource cleanup

- **WHEN** EDA가 자신이 연 resource를 사용한 뒤 성공하거나 failure로 종료될 때
- **THEN** 해당 resource는 정리되어야 하며 source와 database 내용은 EDA 때문에 변경되어서는 안 된다.

### Requirement: Portable actual-source observation

시스템은 controlled actual-source run에서 portable JSON과 그 JSON에서 파생한 Markdown summary를 생성할 수 있어야 한다(SHALL). 두 artifact는 source fingerprint, execution revision, execution timestamp와 duration을 추적할 수 있어야 한다(MUST).

#### Scenario: Observation consistency

- **WHEN** actual-source observation을 생성할 때
- **THEN** Markdown의 key metric은 같은 JSON 값과 일치해야 한다.
- **AND** absolute source path와 temporary directory는 portable evidence에 포함되어서는 안 된다.
