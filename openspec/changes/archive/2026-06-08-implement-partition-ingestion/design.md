## Context

- 2단계(데이터 파운데이션)에서 로컬 DuckDB 연결 및 원본 파일 스키마 자동 감지 로드가 수립되었습니다.
- 3단계에서는 이 적재 로직을 고도화하여, 특정 일자(Daily) 파티션 키를 매개변수로 받아 해당 날짜의 레코드만 멱등(Idempotent)하게 덮어쓰며 적재하는 메커니즘을 구체화합니다.
- 이 단계는 향후 Dagster 백필(Backfill) 실행 시 안전한 데이터 덮어쓰기를 보장하기 위한 필수적인 데이터 레이어 설계입니다.

## Goals / Non-Goals

**Goals:**
- 특정 파티션 일자(YYYY-MM-DD)를 입력 매개변수로 수신하여 해당 파티션 데이터만 로드하는 인제스션 모듈 구현.
- 동일 파티션을 반복 실행하더라도 중복 데이터 누적이 없도록 하는 오버라이트(Overwrite) 멱등성 보장.
- 센서 오류 등으로 왜곡된 탑승 시간 아웃라이어 데이터를 필터링하여 드롭하지 않고 그대로 파티션에 적재하여 보존.

**Non-Goals:**
- 비정상 데이터의 클렌징(Cleansing) 및 정제 처리 (해당 이상치는 탐지기의 분석 대상이므로 그대로 유지).
- Dagster 스케줄러 자체의 상세 복잡 일정 구성 (Dagster가 호출하기 용이한 Python API/CLI 인터페이스 설계에 초점).

## Decisions

- **매개변수화된 적재 쿼리 및 트랜잭션**:
  - `partition_date` 매개변수(예: `"2024-01-15"`)를 인수로 받아, 동일 파티션 적재 시 아래 트랜잭션 과정을 보장합니다.
    1. `BEGIN TRANSACTION;`
    2. `DELETE FROM raw.yellow_tripdata WHERE date(tpep_pickup_datetime) = '2024-01-15';`
    3. `INSERT INTO raw.yellow_tripdata SELECT * FROM read_parquet(...) WHERE date(tpep_pickup_datetime) = '2024-01-15';`
    4. `COMMIT;`
  - *비교 및 결정 이유*: 이 방식은 DuckDB에서 가장 직관적이고 멱등성이 확실하게 보장되며, 롤백이 용이한 SQL 표준 트랜잭션 방식입니다. 물리적 파일 삭제 및 재생성(DROP/CREATE) 방식에 비해 테이블 구조를 안정적으로 유지할 수 있습니다.
- **초경량 SQL 기반 데이터 조작**:
  - 프로젝트 환경에서 Pandas가 완전히 제거되고 EDA 외에는 Polars 등 일체의 DataFrame 라이브러리를 사용하지 않기로 설계 변경되었습니다.
  - 따라서, 2단계/3단계의 모든 데이터 인제스션 및 합성 결함 데이터 생성(Generator)은 **오직 DuckDB SQL 내부의 임시 테이블 쿼리와 DML(예: SAMPLE, random()을 이용한 Null 치환, CAST 등)로만 가공하여 저장**하도록 규정합니다. 이를 통해 메모리 부족 리스크를 원천 차단하고 연산 성능을 극대화합니다.
- **이상치 데이터의 파티션 유지**:
  - 탑승 시간(`tpep_pickup_datetime`) 기준의 분할 적재 시, 원본 파일의 적재 타겟 범위를 초과하는 아웃라이어 데이터(예: 2024년 1월 파일 내의 2008년 레코드 등)도 필터링을 걸지 않고 그대로 허용합니다.
  - 이 데이터들은 각각 해당하는 일자의 파티션 레코드로 DuckDB에 그대로 적재되어, 6단계 인시던트 감지(Detector) 시 `volume_drop` 또는 `null_spike` 등의 분석 대상으로 정상적으로 활용될 수 있게 보장합니다.

## Risks / Trade-offs

- **[Risk] 대용량 데이터에서 DELETE 연산의 성능 저하**
  - DuckDB에서 인덱스가 없는 상황에 특정 일자 조건을 기반으로 `DELETE`를 빈번하게 구동하면 성능 저하가 발생할 수 있습니다.
  - *[Mitigation]*: 로컬 개발 및 테스트 시에는 1만 행 샘플링된 Parquet 파일을 사용하여 지연을 방지하며, 필요시 `tpep_pickup_datetime` 컬럼에 대한 인덱스 생성을 고려합니다.
