## MODIFIED Requirements

### Requirement: dbt DuckDB 프로젝트 구성
시스템은 로컬 DuckDB 데이터베이스를 대상으로 실행 가능한 dbt 프로젝트를 제공해야 한다(SHALL). dbt profile은 개발자 환경과 테스트 환경에서 DuckDB 파일 경로를 환경 변수로 명시적으로 설정할 수 있어야 한다(MUST).

#### Scenario: dbt 프로젝트 설정 검증
- **WHEN** 사용자가 dbt 프로젝트 디렉터리에서 설정 검증 명령을 실행할 때
- **THEN** dbt는 DuckDB adapter와 profile 설정을 정상적으로 해석해야 한다.

### Requirement: raw HMDA source 선언
시스템은 HMDA raw 테이블을 dbt source로 선언해야 한다(SHALL). source 선언은 후속 lineage artifact에서 raw 입력과 staging 모델의 의존 관계를 표현해야 한다(MUST).

#### Scenario: raw source lineage 연결
- **WHEN** dbt가 프로젝트를 parse 또는 build할 때
- **THEN** `manifest.json`에는 HMDA raw source와 이를 참조하는 staging 모델의 의존 관계가 포함되어야 한다.

### Requirement: HMDA staging 모델 생성
시스템은 raw HMDA 신청 데이터를 분석용 staging 모델로 변환해야 한다(SHALL). staging 모델명은 `stg_hmda_loans`로 고정해야 하며(MUST), 후속 mart와 Dagster asset에서 참조할 수 있는 안정된 컬럼명을 제공해야 한다(MUST).

#### Scenario: HMDA staging 모델 빌드
- **WHEN** raw HMDA 테이블이 준비된 상태에서 `dbt build`를 실행할 때
- **THEN** HMDA 대출 신청 staging 모델이 DuckDB에 생성되어야 한다.

#### Scenario: HMDA staging 컬럼 계약
- **WHEN** `stg_hmda_loans`를 조회할 때
- **THEN** `activity_year`, `state_code`, `county_code`, `loan_purpose`, `action_taken`, `loan_amount`, `income`, `source_file`, `source_year` 컬럼이 존재해야 한다.

### Requirement: HMDA mart 모델 생성
시스템은 staging 모델을 기반으로 `mart_hmda_loan_outcomes` 모델을 생성해야 한다(SHALL). mart grain은 `activity_year`, `state_code`, `loan_purpose` 단위로 고정해야 하며(MUST), 신청 건수, 승인 건수, 거절 건수, 승인율, 평균 대출 금액, 평균 소득 지표를 포함해야 한다(MUST).

#### Scenario: HMDA mart 지표 생성
- **WHEN** staging 모델이 준비된 상태에서 mart 모델을 빌드할 때
- **THEN** `activity_year`, `state_code`, `loan_purpose` 단위의 집계 행이 생성되고 핵심 지표 컬럼이 조회 가능해야 한다.

#### Scenario: HMDA mart grain 중복 방지
- **WHEN** `mart_hmda_loan_outcomes`를 조회할 때
- **THEN** `activity_year`, `state_code`, `loan_purpose` 조합은 중복되지 않아야 한다.

### Requirement: dbt 테스트 적용
시스템은 HMDA source, staging, mart 모델에 기본 dbt test를 적용해야 한다(SHALL). 테스트는 필수 컬럼 누락, null grain, mart grain 중복을 조기에 드러낼 수 있어야 한다(MUST).

#### Scenario: dbt build 테스트 실행
- **WHEN** 사용자가 `dbt build`를 실행할 때
- **THEN** 모델 빌드와 기본 dbt test가 함께 실행되고 결과가 성공 또는 실패 상태로 기록되어야 한다.

#### Scenario: HMDA 최소 테스트 계약
- **WHEN** dbt test 정의를 확인할 때
- **THEN** staging의 `activity_year`, `state_code`, `loan_purpose`, `action_taken` 컬럼에는 `not_null` 테스트가 적용되어야 한다.
- **AND** mart grain에는 중복 방지 테스트가 적용되어야 한다.

### Requirement: dbt artifact 생성
시스템은 dbt 실행 이후 `manifest.json`과 `run_results.json` artifact를 생성해야 한다(SHALL). artifact는 `dbt/target/manifest.json`, `dbt/target/run_results.json` 경로에서 후속 lineage evidence와 profile evidence 생성 단계가 참조 가능해야 한다(MUST).

#### Scenario: artifact 파일 확인
- **WHEN** `dbt build`가 완료될 때
- **THEN** `dbt/target/manifest.json`과 `dbt/target/run_results.json`이 존재해야 한다.

### Requirement: Dagster asset 호환 모델 경계
시스템은 후속 Dagster asset이 dbt 모델을 감쌀 수 있도록 모델명, mart grain, 파티션 컬럼, artifact 경로를 안정적으로 유지해야 한다(SHALL). 이번 변경은 Dagster schedule, retry, backfill, asset definition 신규 자동화를 구현하지 않아야 한다(MUST NOT).

#### Scenario: dbt 모델과 Dagster asset 경계 연결
- **WHEN** 후속 Dagster asset이 dbt 모델을 참조할 때
- **THEN** `stg_hmda_loans`와 `mart_hmda_loan_outcomes`는 dbt node id와 Dagster asset key로 일관되게 매핑 가능해야 한다.
- **AND** `mart_hmda_loan_outcomes.activity_year`는 연도 파티션 키로 사용할 수 있어야 한다.

### Requirement: dbt 변환 멱등성
시스템은 동일 raw 입력과 동일 dbt 명령에 대해 중복 행을 누적하지 않는 결정적 분석 결과를 생성해야 한다(SHALL). foundation 단계의 dbt 모델은 append-only incremental 전략을 사용하지 않아야 한다(MUST NOT).

#### Scenario: dbt build 재실행
- **WHEN** 동일 DuckDB raw HMDA 데이터에 대해 `dbt build`를 2회 연속 실행할 때
- **THEN** `mart_hmda_loan_outcomes`의 행 수와 `activity_year`, `state_code`, `loan_purpose` grain은 1회 실행 결과와 동일해야 한다.
