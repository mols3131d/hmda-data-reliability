## ADDED Requirements

### Requirement: dbt DuckDB 프로젝트 구성
시스템은 로컬 DuckDB 데이터베이스를 대상으로 실행 가능한 dbt 프로젝트를 제공해야 한다(SHALL). dbt profile은 개발자 환경과 테스트 환경에서 DuckDB 파일 경로를 환경 변수로 명시적으로 설정할 수 있어야 한다(MUST).

#### Scenario: dbt 프로젝트 설정 검증
- **WHEN** 사용자가 dbt 프로젝트 디렉터리에서 설정 검증 명령을 실행할 때
- **THEN** dbt는 DuckDB adapter와 profile 설정을 정상적으로 해석해야 한다.

### Requirement: raw taxi source 선언
시스템은 `raw.yellow_tripdata`와 `raw.taxi_zones`를 dbt source로 선언해야 한다(SHALL). source 선언은 후속 lineage artifact에서 raw 입력과 staging 모델의 의존 관계를 표현해야 한다(MUST).

#### Scenario: raw source lineage 연결
- **WHEN** dbt가 프로젝트를 parse 또는 build할 때
- **THEN** `manifest.json`에는 raw source와 이를 참조하는 staging 모델의 의존 관계가 포함되어야 한다.

### Requirement: staging 모델 생성
시스템은 raw 택시 운행 데이터와 택시 지역 데이터를 분석용 staging 모델로 변환해야 한다(SHALL). staging 모델명은 `stg_yellow_tripdata`, `stg_taxi_zones`로 고정해야 하며(MUST), 후속 mart와 Dagster asset에서 참조할 수 있는 안정된 컬럼명을 제공해야 한다(MUST).

#### Scenario: staging 모델 빌드
- **WHEN** raw 테이블이 준비된 상태에서 `dbt build`를 실행할 때
- **THEN** 택시 운행 staging 모델과 택시 지역 staging 모델이 DuckDB에 생성되어야 한다.

#### Scenario: staging 컬럼 계약
- **WHEN** `stg_yellow_tripdata`를 조회할 때
- **THEN** `pickup_at`, `dropoff_at`, `pickup_date`, `pickup_location_id`, `dropoff_location_id`, `passenger_count`, `total_amount`, `source_partition`, `source_file` 컬럼이 존재해야 한다.
- **AND** `stg_taxi_zones`는 `location_id`, `borough`, `zone`, `service_zone` 컬럼을 제공해야 한다.

### Requirement: mart 모델 생성
시스템은 staging 모델을 기반으로 `mart_daily_taxi_trips` 모델을 생성해야 한다(SHALL). mart grain은 `pickup_date`, `pickup_location_id` 단위로 고정해야 하며(MUST), 최소한 운행 건수, 총 요금, 평균 요금, 승객 수 집계 지표를 포함해야 한다(MUST).

#### Scenario: mart 지표 생성
- **WHEN** staging 모델이 준비된 상태에서 mart 모델을 빌드할 때
- **THEN** `pickup_date`, `pickup_location_id` 단위의 집계 행이 생성되고 핵심 지표 컬럼이 조회 가능해야 한다.

#### Scenario: mart grain 중복 방지
- **WHEN** `mart_daily_taxi_trips`를 조회할 때
- **THEN** `pickup_date`, `pickup_location_id` 조합은 중복되지 않아야 한다.

### Requirement: dbt 테스트 적용
시스템은 source, staging, mart 모델에 기본 dbt test를 적용해야 한다(SHALL). 테스트는 필수 컬럼 누락, null grain, 참조 관계 깨짐, mart grain 중복을 조기에 드러낼 수 있어야 한다(MUST).

#### Scenario: dbt build 테스트 실행
- **WHEN** 사용자가 `dbt build`를 실행할 때
- **THEN** 모델 빌드와 기본 dbt test가 함께 실행되고 결과가 성공 또는 실패 상태로 기록되어야 한다.

#### Scenario: 최소 테스트 계약
- **WHEN** dbt test 정의를 확인할 때
- **THEN** staging의 핵심 날짜/지역 컬럼에는 `not_null` 테스트가 적용되어야 한다.
- **AND** mart grain에는 중복 방지 테스트가 적용되어야 한다.
- **AND** staging 지역 키는 `stg_taxi_zones.location_id`와의 참조 관계를 검증해야 한다.

### Requirement: dbt artifact 생성
시스템은 dbt 실행 이후 `manifest.json`과 `run_results.json` artifact를 생성해야 한다(SHALL). artifact는 `dbt/target/manifest.json`, `dbt/target/run_results.json` 경로에서 후속 lineage evidence와 profile evidence 생성 단계가 참조 가능해야 한다(MUST).

#### Scenario: artifact 파일 확인
- **WHEN** `dbt build`가 완료될 때
- **THEN** `dbt/target/manifest.json`과 `dbt/target/run_results.json`이 존재해야 한다.

### Requirement: Dagster asset 호환 모델 경계
시스템은 후속 Dagster 도입 시 dbt 모델을 asset으로 감쌀 수 있도록 모델명, daily grain, partition 컬럼, artifact 경로를 안정적으로 유지해야 한다(SHALL). 이번 변경은 Dagster schedule, retry, backfill, asset definition을 구현하지 않아야 한다(MUST NOT).

#### Scenario: dbt 모델과 Dagster asset 경계 연결
- **WHEN** 후속 Dagster asset이 dbt 모델을 참조할 때
- **THEN** `stg_yellow_tripdata`, `stg_taxi_zones`, `mart_daily_taxi_trips`는 dbt node id와 Dagster asset key로 일관되게 매핑 가능해야 한다.
- **AND** `mart_daily_taxi_trips.pickup_date`는 daily partition key로 사용할 수 있어야 한다.

### Requirement: dbt 변환 멱등성
시스템은 동일 raw 입력과 동일 dbt 명령에 대해 중복 행을 누적하지 않는 결정적 분석 결과를 생성해야 한다(SHALL). foundation 단계의 dbt 모델은 append-only incremental 전략을 사용하지 않아야 한다(MUST NOT).

#### Scenario: dbt build 재실행
- **WHEN** 동일 DuckDB raw 데이터에 대해 `dbt build`를 2회 연속 실행할 때
- **THEN** `mart_daily_taxi_trips`의 행 수와 `pickup_date`, `pickup_location_id` grain은 1회 실행 결과와 동일해야 한다.
