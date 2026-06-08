## 1. DuckDB Database & Schema Setup

- [x] 1.1 병렬 테스트 실행 격리(임시 DB 생성 및 teardown 자동화)가 가능한 DuckDB 연결 Context Manager 구현
- [x] 1.2 DuckDB의 read_parquet/read_csv 스키마 자동 감지(Auto-detection) 기능을 활용한 `raw.taxi_zones` 및 `raw.yellow_tripdata` 테이블 동적 DDL 모듈 구현

## 2. Raw Ingestion Implementation

- [x] 2.1 `taxi_zone_lookup.csv`를 읽어 DuckDB `raw.taxi_zones` 테이블에 멱등하게 적재하는 기본 로더 함수 작성
- [x] 2.2 2024년 옐로우 택시 Parquet 원천 데이터 파일을 파티션별로 파싱하여 DuckDB에 로드하는 기본 로더 함수 작성 (3단계 Ingestion의 입력 소스로 전환이 가능한 구조 설계)

## 3. Synthetic Defect Data Generator

- [x] 3.1 원본 데이터의 데일리 파티션 분포를 유지한 채 고르게 샘플링하여 행의 수를 대폭 감소시킨 뒤 별도 격리된 파티션 파일로 저장하는 `row_count_drop` 유틸 개발
- [x] 3.2 데일리 파티션 분포 유지 샘플링 후, 특정 컬럼(예: `total_amount`) 값을 강제 `NaN`으로 치환해 Null 비율을 급증시키고 디스크에 영속화하는 `null_spike` 유틸 개발
- [x] 3.3 컬럼 이름을 변형시키거나 데이터 타입을 텍스트로 오버라이딩하여 저장하는 `schema_drift` 유틸 개발
- [x] 3.4 관측 시간(observed_at)을 임계치보다 훨씬 이전 시점으로 밀어서 메타데이터 상으로 저장하는 `freshness_delay` 유틸 개발

## 4. Verification and Tests

- [x] 4.1 DuckDB 상에서 생성된 5가지 정상/이상 파티션(normal, row_count_drop, null_spike, schema_drift, freshness_delay) 각각이 정상 조회되고 기대하는 결함 통계치를 정상적으로 드러내는지 확인하는 개별 단위 테스트 작성
