## ADDED Requirements

### Requirement: DuckDB 연결 및 raw 테이블 초기화
시스템은 로컬 DuckDB 데이터베이스 파일에 연결하고 데이터를 영속적으로 관리할 수 있는 raw 테이블 초기화 로직을 제공해야 한다(SHALL). 테스트 환경에서는 병렬 실행을 위해 임시 데이터베이스로 완전히 격리되어 연결될 수 있어야 한다.

#### Scenario: 데이터베이스 초기 연결 및 테스트 격리
- **WHEN** 시스템이 DuckDB 연결 초기화 함수를 호출하거나 테스트 컨텍스트가 격리 연결을 시도할 때
- **THEN** 충돌 없이 격리된 고유 경로에 혹은 인메모리에 데이터베이스 세션이 정상적으로 생성되어야 한다.

### Requirement: 원천 Parquet 및 CSV 데이터 로드
시스템은 원천 데이터 디렉터리(`data/raw/tlc`)에서 Parquet 및 CSV 파일을 읽어 DuckDB 테이블로 적재해야 한다(SHALL). 테이블 스키마는 Parquet 구조 자동 감지(Auto-detection) 방식으로 생성되어 하드코딩 오류를 배제해야 한다.

#### Scenario: Taxi Zone Lookup 데이터 적재
- **WHEN** 인제스션 모듈이 `taxi_zone_lookup.csv`를 읽어 DuckDB에 적재를 시도할 때
- **THEN** DuckDB 테이블 `raw.taxi_zones`에 데이터가 중복 없이 로드되어야 한다.

#### Scenario: Yellow Tripdata Parquet 파일 적재
- **WHEN** 인제스션 모듈이 지정 연도의 옐로우 택시 Parquet 파일을 읽어 적재할 때
- **THEN** 컬럼 스키마가 자동 감지되어 테이블 구조가 생성되고, 파티션 정보와 원본 행이 모두 올바르게 DuckDB의 raw 데이터 레이어에 반영되어야 한다.

### Requirement: 테스트용 합성 이상치 데이터 생성
시스템은 인시던트 탐지 및 에이전트의 작동을 검증하기 위해, 일자별 파티션 분포를 보존하며 품질 결함이 조작/주입된 4가지 변형 파티션 파일을 생성하여 디스크에 쓸 수 있어야 한다(SHALL).

#### Scenario: 행 개수 유실(Row Count Drop) 합성 데이터 생성
- **WHEN** 행 유실 생성기를 가동할 때
- **THEN** 일자별 파티션 날짜를 고르게 포함하되 원본 데이터 대비 행 수가 대폭 유실된 파티션 파일이 별도의 테스트 경로에 저장되어야 한다.

#### Scenario: Null 비율 급증(Null Rate Spike) 합성 데이터 생성
- **WHEN** Null 급증 생성기를 가동할 때
- **THEN** 특정 주요 열(예: `total_amount`)의 Null 비율을 5% 이상으로 유입시킨 테스트 파티션 파일이 생성되어야 한다.

#### Scenario: 스키마 변형(Schema Drift) 합성 데이터 생성
- **WHEN** 스키마 변형 생성기를 가동할 때
- **THEN** 특정 컬럼이 제거되거나 데이터 타입이 달라져 스키마 호환성이 맞지 않는 파티션 파일이 생성되어야 한다.

#### Scenario: 지연 적재(Freshness Delay) 합성 데이터 생성
- **WHEN** 적재 지연 생성기를 가동할 때
- **THEN** 데이터 관측 시간(observed_at)이 SLA 기준 시간보다 훨씬 지연된 형태의 메타데이터 파티션이 생성되어야 한다.

### Requirement: 합성 파티션 개별 쿼리 검증
시스템은 로컬 DuckDB 내에서 생성된 5가지 정상 및 이상치 파티션들이 독립적으로 쿼리 가능하고 의도된 결함 특성을 드러내는지 검증해야 한다(SHALL).

#### Scenario: 정상 파티션 조회
- **WHEN** `normal` 파티션을 대상으로 SELECT 쿼리를 돌릴 때
- **THEN** 쿼리가 성공하며, 모든 열의 데이터 및 Null 비율이 기대 기준에 맞게 조회되어야 한다.

#### Scenario: 볼륨 급감 파티션 조회
- **WHEN** `row_count_drop` 이상치 파티션을 대상으로 SELECT 쿼리를 돌릴 때
- **THEN** 쿼리가 성공하며, 행 개수가 원본 대비 대폭 감소한 유실 통계 수치가 반환되어야 한다.

#### Scenario: Null 급증 파티션 조회
- **WHEN** `null_spike` 이상치 파티션을 대상으로 SELECT 쿼리를 돌릴 때
- **THEN** 쿼리가 성공하며, 지정된 열의 Null 개수 및 비율이 5% 이상으로 나타나야 한다.

#### Scenario: 스키마 변형 파티션 조회
- **WHEN** `schema_drift` 이상치 파티션을 대상으로 SELECT 쿼리를 돌릴 때
- **THEN** 쿼리가 성공하며, 변경된 컬럼 구조 또는 형 변환 에러 등의 예외가 검증 가능한 형태로 나타나야 한다.

#### Scenario: 지연 적재 파티션 조회
- **WHEN** `freshness_delay` 이상치 파티션을 대상으로 SELECT 쿼리를 돌릴 때
- **THEN** 쿼리가 성공하며, 관측 타임스탬프와 적재 시점의 격차가 설정한 임계치(SLA 지연)를 초과해야 한다.
