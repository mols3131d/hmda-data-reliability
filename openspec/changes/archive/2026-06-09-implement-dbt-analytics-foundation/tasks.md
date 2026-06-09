## 1. dbt Project Setup

- [x] 1.1 `dbt/` 하위에 `dbt_project.yml`, `profiles.yml`, 기본 디렉터리 구조를 만든다.
- [x] 1.2 DuckDB 파일 경로를 환경 변수로 주입할 수 있게 profile을 구성한다.
- [x] 1.3 dbt 설정 검증 명령이 로컬에서 통과하는지 확인한다.

## 2. Source and Staging Models

- [x] 2.1 `raw.yellow_tripdata`, `raw.taxi_zones` source 선언과 기본 source test를 추가한다.
- [x] 2.2 `stg_yellow_tripdata` 모델을 만들고 `pickup_at`, `dropoff_at`, `pickup_date`, `pickup_location_id`, `dropoff_location_id`, `passenger_count`, `total_amount`, `source_partition`, `source_file` 컬럼을 제공한다.
- [x] 2.3 `stg_taxi_zones` 모델을 만들고 `location_id`, `borough`, `zone`, `service_zone` 컬럼을 제공한다.
- [x] 2.4 staging 핵심 날짜/지역 컬럼의 `not_null` 테스트와 지역 참조 관계 테스트를 추가한다.

## 3. Mart Models

- [x] 3.1 `pickup_date`, `pickup_location_id` grain의 `mart_daily_taxi_trips` 모델을 만든다.
- [x] 3.2 mart에 운행 건수, 총 요금, 평균 요금, 승객 수 지표를 포함한다.
- [x] 3.3 mart 모델의 grain 중복 방지, null, reference 테스트를 추가한다.
- [x] 3.4 dbt 모델은 foundation 단계에서 append-only incremental 전략을 사용하지 않도록 구성한다.

## 4. Dagster Compatibility

- [x] 4.1 모델명 `stg_yellow_tripdata`, `stg_taxi_zones`, `mart_daily_taxi_trips`가 dbt node id와 Dagster asset key로 매핑 가능한지 확인한다.
- [x] 4.2 `mart_daily_taxi_trips.pickup_date`가 daily partition key로 사용 가능한지 확인한다.
- [x] 4.3 Dagster schedule, retry, backfill, asset definition 구현은 이번 change에 포함하지 않는다.

## 5. Artifact and Validation

- [x] 5.1 pytest에서 임시 DuckDB 파일과 raw 테이블 fixture를 준비한다.
- [x] 5.2 테스트 fixture를 대상으로 `dbt build`가 성공하는지 검증한다.
- [x] 5.3 `dbt/target/manifest.json`, `dbt/target/run_results.json` 생성 여부를 검증한다.
- [x] 5.4 manifest에 raw source → staging → mart lineage가 포함되는지 확인한다.
- [x] 5.5 동일 raw 입력에 대해 `dbt build`를 2회 실행해 mart 결과가 중복 누적되지 않는지 검증한다.

## 6. Documentation

- [x] 6.1 dbt 실행 방법과 필요한 환경 변수를 짧게 문서화한다.
- [x] 6.2 후속 profile/impact-analysis/Dagster 단계가 참조할 모델명, partition 컬럼, artifact 경로를 문서화한다.
