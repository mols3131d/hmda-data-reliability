## 1. Ingestion Interface & CLI Setup

- [x] 1.1 인제스션 실행을 위해 특정 파티션 날짜(`partition_date`, YYYY-MM-DD 형식)를 매개변수로 받아들이는 Python 함수 및 CLI 모듈 스캐폴딩
- [x] 1.2 DuckDB의 `raw.yellow_tripdata` 적재 테이블 정보와 연결 Context Manager 매핑 완료

## 2. Partition Ingestion & Overwrite Logic

- [x] 2.1 원천 Parquet 파일에서 `date(tpep_pickup_datetime)` 기준 매개변수 일자와 일치하는 행들만 고르는 SQL 필터링 구문 작성
- [x] 2.2 멱등(Idempotent) 적재를 보장하기 위해, 지정된 일자의 기존 데이터를 DELETE 쿼리로 선 삭제하고 신규 데이터를 INSERT 하도록 감싸는 데이터베이스 트랜잭션 구문 구현
- [x] 2.3 탑승 시간 타임스탬프가 비정상적인 이상치(Outlier) 레코드들도 필터링에 의해 제외되지 않고 지정된 픽업 날짜 기준 파티션에 누락 없이 적재되도록 보장

## 3. Verification & Idempotency Testing

- [x] 3.1 특정 일자를 지정하여 인제스션을 2회 연속 실행한 후, 최종 데이터 건수와 1회 실행 건수가 중복 없이 완전히 일치하는지 검증하는 단위 테스트 작성
