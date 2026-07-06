## Purpose

HMDA 원천 데이터와 품질 이상 테스트 데이터를 로컬 DuckDB에서 안정적으로 적재하고 검증하기 위한 데이터 파운데이션을 정의한다.

## Requirements

### Requirement: DuckDB 연결 및 HMDA raw 테이블 초기화

시스템은 로컬 DuckDB 데이터베이스 파일에 연결하고 HMDA 원천 데이터를 영속적으로 관리할 수 있는 raw 테이블 초기화 로직을 제공해야 한다(SHALL). 테스트 환경에서는 병렬 실행을 위해 임시 데이터베이스로 완전히 격리되어 연결될 수 있어야 한다(MUST).

#### Scenario: 데이터베이스 초기 연결 및 테스트 격리

- **WHEN** 시스템이 DuckDB 연결 초기화 함수를 호출하거나 테스트 컨텍스트가 격리 연결을 시도할 때
- **THEN** 충돌 없이 격리된 고유 경로에 혹은 인메모리에 데이터베이스 세션이 정상적으로 생성되어야 한다.

### Requirement: HMDA 원천 파일 로드

시스템은 원천 데이터 디렉터리(`data/raw/hmda`)에서 HMDA CSV 또는 Parquet 파일을 읽어 DuckDB raw 테이블로 적재해야 한다(SHALL). 테이블 스키마는 DuckDB의 구조 감지 기능을 사용해 생성되어야 하며(MUST), 원천 추적을 위해 `source_file`, `source_year`, `ingested_at` 메타데이터를 보존해야 한다(MUST).

#### Scenario: HMDA 원천 파일 적재

- **WHEN** 인제스션 모듈이 `data/raw/hmda` 아래의 HMDA 원천 파일을 읽어 적재를 시도할 때
- **THEN** DuckDB raw 스키마에 HMDA 신청 레코드가 로드되어야 한다.
- **AND** 각 행은 원천 파일명과 활동 연도 추적 정보를 포함해야 한다.

#### Scenario: 지원하지 않는 원천 파일 처리

- **WHEN** 인제스션 모듈이 CSV 또는 Parquet가 아닌 파일을 발견할 때
- **THEN** 해당 파일은 적재 대상에서 제외되어야 하며 사용자에게 노출되는 오류 없이 로그 metadata로 기록되어야 한다.

### Requirement: HMDA 핵심 컬럼 검증

시스템은 HMDA staging과 mart 생성에 필요한 핵심 컬럼의 존재 여부를 raw 적재 후 검증해야 한다(SHALL). 최소 핵심 컬럼은 `activity_year`, `loan_purpose`, `action_taken`, `loan_amount`, `income`, `state_code`, `county_code`를 포함해야 한다(MUST).

#### Scenario: 핵심 컬럼 존재 검증

- **WHEN** HMDA raw 적재가 완료될 때
- **THEN** 시스템은 핵심 컬럼 존재 여부를 검증해야 한다.
- **AND** 누락 컬럼이 있으면 사용자에게는 요약된 커스텀 예외 메시지를 제공하고 상세 컨텍스트는 로그 `extra`에 남겨야 한다.

### Requirement: 테스트용 HMDA 품질 이상 데이터 생성

시스템은 reliability 흐름 검증을 위해 HMDA 신청 레코드의 분포를 보존하며 품질 결함이 주입된 테스트 파일을 생성할 수 있어야 한다(SHALL). 결함 유형은 행 수 급감, Null 비율 급증, 스키마 변형, 원천 파일 지연을 포함해야 한다(MUST).

#### Scenario: HMDA 행 개수 유실 데이터 생성

- **WHEN** 행 유실 생성기를 가동할 때
- **THEN** 원본 HMDA 데이터 대비 행 수가 대폭 유실된 테스트 파일이 별도 경로에 저장되어야 한다.

#### Scenario: HMDA Null 급증 데이터 생성

- **WHEN** Null 급증 생성기를 가동할 때
- **THEN** `income` 또는 `loan_amount` 같은 핵심 분석 컬럼의 Null 비율이 검증 가능한 수준으로 증가한 테스트 파일이 생성되어야 한다.

#### Scenario: HMDA 스키마 변형 데이터 생성

- **WHEN** 스키마 변형 생성기를 가동할 때
- **THEN** 핵심 컬럼 제거 또는 타입 변경으로 스키마 호환성 문제가 드러나는 테스트 파일이 생성되어야 한다.

#### Scenario: HMDA 원천 파일 지연 데이터 생성

- **WHEN** 지연 적재 생성기를 가동할 때
- **THEN** 관측 시점과 적재 시점의 차이가 SLA 기준을 초과하는 테스트 metadata가 생성되어야 한다.
