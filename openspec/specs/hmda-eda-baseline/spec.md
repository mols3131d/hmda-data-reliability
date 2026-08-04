# hmda-eda-baseline Specification

## Purpose

HMDA 원천 CSV를 fail-fast로 탐색해 schema, volume, null, freshness evidence를
생성하고, 동일한 계산 경로의 correctness와 process-level memory budget을
검증하는 계약을 정의한다.

## Requirements

### Requirement: Parse-integrity baseline input

노트북은 `HMDA_EDA_DATA_PATH` 또는 기본 원천 CSV의 존재를 확인하고, DuckDB가 파싱 오류를 반환하면 baseline metric과 `eda_evidence`를 생성하지 않아야 한다(MUST).

#### Scenario: 입력 파일이 없는 경우

- **WHEN** 지정된 EDA CSV 경로에 파일이 없을 때
- **THEN** 노트북은 DuckDB reader 실행 전에 입력 경로 오류를 표시해야 한다.
- **AND** `row_count`, `null_rates`, `eda_evidence`를 생성해서는 안 된다.

#### Scenario: CSV 파싱 오류가 있는 경우

- **WHEN** CSV에 DuckDB가 읽을 수 없는 행이 있을 때
- **THEN** 노트북은 CSV parse error로 실행을 실패시켜야 한다.
- **AND** 손상 행을 제외한 volume 또는 null baseline을 표시해서는 안 된다.

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

### Requirement: Core code distributions

시스템은 `action_taken`, `loan_purpose`, `state_code`와 선택적으로 `county_code`의 observed value별 count와 share를 제공해야 한다(SHALL). 허용 code 밖의 값은 정제하지 않고 unknown 또는 anomaly observation으로 식별해야 한다(MUST).

#### Scenario: Code distribution evidence

- **WHEN** 핵심 code field가 존재하는 HMDA source를 분석할 때
- **THEN** 각 field의 observed value별 count와 전체 row 대비 share를 반환해야 한다.
- **AND** count의 합은 해당 field의 분석 population과 일치해야 한다.

#### Scenario: Unknown code preservation

- **WHEN** 허용 code 목록에 없는 값이 관찰될 때
- **THEN** 해당 값과 count는 anomaly observation으로 기록되어야 한다.
- **AND** 원천 row는 삭제되거나 자동 변환되지 않아야 한다.

### Requirement: Numeric summary and anomaly observation

시스템은 `loan_amount`와 `income`에 대해 non-null count, min, p25, median, p75, max와 suspicious range count를 제공해야 한다(SHALL). domain 의미가 확정되지 않은 extreme value는 관찰 flag로만 기록해야 한다(MUST).

#### Scenario: Numeric summary evidence

- **WHEN** 수치형 핵심 field가 포함된 HMDA source를 분석할 때
- **THEN** 각 대상 field에 대해 non-null count와 five-number summary를 반환해야 한다.
- **AND** summary는 원천 값을 삭제하거나 임의의 범위로 clipping하지 않고 계산되어야 한다.

#### Scenario: Suspicious numeric observation

- **WHEN** `income < 0`, `loan_amount <= 0` 또는 configured suspicious condition이 관찰될 때
- **THEN** field, condition, count와 share가 anomaly observation에 포함되어야 한다.
- **AND** anomaly는 자동 정제나 incident 생성으로 이어지지 않아야 한다.

### Requirement: MVP grain alignment

시스템은 `activity_year + state_code + loan_purpose` grain을 기준으로 aggregate row count와 핵심 metric의 연결을 확인할 수 있는 evidence를 제공해야 한다(SHALL). EDA는 새로운 canonical business grain을 정의하거나 현재 mart grouping rule을 변경해서는 안 된다(MUST NOT).

#### Scenario: Mart grain evidence

- **WHEN** HMDA source에 현재 mart의 grain field가 존재할 때
- **THEN** EDA evidence는 해당 grain의 aggregate count와 null/coverage 상태를 포함해야 한다.
- **AND** grain key와 metric 해석은 current dbt mart contract와 일치해야 한다.

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

### Requirement: Reusable EDA computation boundary

시스템은 HMDA CSV path와 명시적인 DuckDB resource 설정을 입력받아 기존
baseline metric과 JSON-serializable `eda_evidence`를 반환하는 일반 Python
entrypoint를 제공해야 한다(SHALL). Marimo notebook과 automated test는 동일한
entrypoint를 사용해야 한다(MUST).

#### Scenario: Notebook baseline 실행

- **WHEN** 사용자가 유효한 HMDA CSV를 선택하고 notebook 실행 버튼을 누를 때
- **THEN** 노트북은 공유 EDA entrypoint를 호출해야 한다.
- **AND** 반환된 schema, volume, null, freshness와 evidence mapping을 기존 UI에 표시해야 한다.

#### Scenario: Automated correctness 검증

- **WHEN** 작은 deterministic fixture로 correctness test를 실행할 때
- **THEN** test는 notebook UI를 시작하지 않고 공유 EDA entrypoint를 호출해야 한다.
- **AND** 노트북과 동일한 evidence 계약을 검증해야 한다.

### Requirement: EDA resource lifecycle

EDA entrypoint는 원천 파일과 데이터베이스를 수정하지 않아야 하며(MUST),
성공 또는 실패와 관계없이 자신이 연 DuckDB connection을 명시적으로 닫아야
한다(MUST). 실행별 temp resource는 다른 실행과 분리되고 호출자가 정한
lifecycle 안에서 정리 가능해야 한다(SHALL).

#### Scenario: 정상 실행 종료

- **WHEN** EDA metric과 evidence 생성이 완료될 때
- **THEN** entrypoint는 결과를 반환하기 전에 DuckDB connection을 닫아야 한다.
- **AND** 원천 HMDA CSV를 변경해서는 안 된다.

#### Scenario: Query 또는 parse 실패

- **WHEN** CSV parse 또는 aggregate query가 실패할 때
- **THEN** entrypoint는 부분 `eda_evidence`를 성공 결과로 반환해서는 안 된다.
- **AND** DuckDB connection을 닫은 뒤 원래 실패를 호출자에게 전달해야 한다.

### Requirement: Bounded grouped result

EDA entrypoint는 `activity_year` grouping 결과를 Python에 materialize하기 전에
HMDA baseline에서 허용하는 cardinality bound를 적용해야 한다(SHALL).

#### Scenario: 정상 activity-year cardinality

- **WHEN** grouping 결과가 설정된 cardinality bound 안에 있을 때
- **THEN** entrypoint는 모든 activity-year count를 evidence에 포함해야 한다.

#### Scenario: 비정상 activity-year cardinality

- **WHEN** grouping 결과가 설정된 cardinality bound를 초과할 때
- **THEN** entrypoint는 전체 grouping 결과를 무제한으로 Python heap에 적재해서는 안 된다.
- **AND** 명시적인 validation failure를 반환해야 한다.

### Requirement: Representative HMDA memory workload

시스템은 HMDA EDA memory-budget test에 사용할 deterministic representative
fixture와 fixture manifest를 제공해야 한다(SHALL). manifest는 최소한 fixture
version, seed, schema, row 수, row 폭, null 비율, `activity_year` cardinality와
skew, 파일 수를 기록해야 한다(MUST).

#### Scenario: Representative fixture 준비

- **WHEN** memory-budget test를 시작할 때
- **THEN** 측정 process를 실행하기 전에 fixture와 manifest가 준비되어 있어야 한다.
- **AND** fixture 생성 비용은 EDA 측정 구간에 포함되지 않아야 한다.

#### Scenario: Fixture 계약 누락

- **WHEN** fixture가 없거나 manifest의 필수 특성이 누락되었을 때
- **THEN** 실행은 유효한 memory-budget test로 통과해서는 안 된다.

### Requirement: Process-level memory budget enforcement

memory-budget runner는 EDA process tree에 hard memory limit과 swap limit,
timeout을 적용해야 한다(MUST). DuckDB 내부 memory limit은 process hard
limit보다 낮아야 하며 DuckDB thread 수와 전용 temp directory를 명시해야
한다(MUST).

#### Scenario: 제한된 대표 workload 실행

- **WHEN** 대표 fixture의 EDA를 process 3 GiB, swap 0, DuckDB 1600 MB, DuckDB 2 threads, timeout 15분 조건으로 실행할 때
- **THEN** hard limit은 EDA를 실행하는 전체 process tree에 적용되어야 한다.
- **AND** 실행별 전용 temp directory가 사용되어야 한다.

#### Scenario: Hard limit을 적용할 수 없는 환경

- **WHEN** runner가 systemd 또는 동등한 container memory limit을 실제로 적용할 수 없을 때
- **THEN** 해당 실행은 memory-budget 통과로 기록되어서는 안 된다.

### Requirement: Memory result and correctness validation

memory-budget test는 process 성공뿐 아니라 EDA 결과의 schema, row count,
required-column null invariant, activity-year count와 freshness 상태를 함께
검증해야 한다(MUST). 실행 결과는 process limit, DuckDB limit, thread,
peak RSS, elapsed time, temp disk, output validation과 environment version을
보고해야 한다(SHALL).

#### Scenario: Memory-budget 통과

- **WHEN** 동일한 fixture로 세 번 실행한 모든 process가 exit code 0이고 OOM 또는 timeout 없이 결과 invariant를 통과할 때
- **THEN** 세 실행 중 최대 peak RSS와 실행 조건을 포함해 통과로 보고해야 한다.
- **AND** 최대 peak RSS가 hard limit의 85%를 초과하면 개선 필요로 표시해야 한다.

#### Scenario: 불완전한 결과

- **WHEN** process가 종료되었지만 결과 invariant가 실패하거나 output이 완전하게 생성되지 않았을 때
- **THEN** 파일 존재 여부와 관계없이 memory-budget test를 실패로 판정해야 한다.

#### Scenario: Resource limit 초과

- **WHEN** process가 OOM kill, timeout 또는 temp disk limit 초과로 종료될 때
- **THEN** 종료 코드만으로 원인을 단정하지 않고 runner와 resource-control evidence를 포함해 실패로 보고해야 한다.

### Requirement: Memory test isolation

시스템은 작은 fixture의 correctness test와 대표 fixture의 memory-budget
test를 분리해야 한다(SHALL). Marimo notebook 자체는 memory-budget gate가
아니라 공유 계산 entrypoint를 연결하는 smoke 대상으로 검증해야 한다(MUST).

#### Scenario: 일반 test 실행

- **WHEN** 개발자가 기본 correctness test를 실행할 때
- **THEN** 대표 memory workload는 일반 병렬 test 실행에 포함되지 않아야 한다.

#### Scenario: Memory test 선택 실행

- **WHEN** 개발자 또는 CI가 `memory` marker를 선택할 때
- **THEN** 대표 fixture를 사용하는 계산 entrypoint만 memory-budget runner 안에서 실행해야 한다.
- **AND** Marimo UI process는 측정 process에 포함되지 않아야 한다.
