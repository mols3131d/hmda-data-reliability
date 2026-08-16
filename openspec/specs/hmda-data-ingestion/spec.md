# hmda-data-ingestion Specification

## Purpose

HMDA 원천 파일을 발견·검증하고 Bronze dataset으로 전체 또는 partition 단위 적재하며, 원천 값과 provenance를 보존하는 ingestion 계약을 정의한다.

## Requirements

### Requirement: Source discovery

시스템은 configured source root에서 HMDA CSV와 Parquet 파일만 적재 후보로 발견하고 파일명 기준의 결정적인 순서로 처리해야 한다(SHALL). 지원하지 않는 파일은 적재 대상에서 제외해야 한다(MUST).

#### Scenario: Supported source discovery

- **WHEN** source root에 CSV, Parquet와 기타 파일이 함께 있을 때
- **THEN** CSV와 Parquet만 정렬된 적재 후보로 반환되어야 한다.

#### Scenario: Missing source root

- **WHEN** configured source root가 존재하지 않을 때
- **THEN** 시스템은 빈 source set을 성공으로 반환하지 않고 HMDA data load failure로 종료해야 한다.

### Requirement: Source contract validation

시스템은 ingestion 과정에서 `activity_year`, `state_code`, `county_code`, `loan_purpose`, `action_taken`, `loan_amount`, `income` 컬럼의 존재를 검증해야 한다(SHALL). 필수 컬럼이 누락되거나 source row를 정상적으로 parse할 수 없는 입력을 성공한 적재로 보고해서는 안 된다(MUST NOT).

#### Scenario: Missing required column

- **WHEN** 적재 대상 파일에 필수 컬럼이 없을 때
- **THEN** 시스템은 누락 컬럼을 식별할 수 있는 HMDA data validation failure로 종료해야 한다.

#### Scenario: Malformed source row

- **WHEN** 적재 대상 파일에 source 구조와 맞지 않아 정상적으로 parse할 수 없는 row가 있을 때
- **THEN** 시스템은 해당 row를 조용히 버리지 않고 HMDA data load 또는 validation failure로 종료해야 한다.

### Requirement: Bronze load with provenance

시스템은 유효한 원천 행을 `raw.hmda_loans`에 적재하고 `source_file`, `source_file_name`, `source_year`, `ingested_at` provenance를 함께 보존해야 한다(SHALL).

#### Scenario: Full source load

- **WHEN** 유효한 source set을 전체 적재할 때
- **THEN** Bronze dataset에는 원천 행과 provenance가 함께 저장되어야 한다.
- **AND** 같은 입력을 다시 전체 적재해도 행이 누적되어서는 안 된다.

### Requirement: Partition replacement

시스템은 `source_year`와 optional `source_file`로 대상 partition을 선택해 해당 범위만 교체할 수 있어야 한다(SHALL). Partition 교체가 완료되지 못하면 기존 partition을 부분 삭제 또는 새 입력과 혼합된 상태로 남겨서는 안 된다(MUST NOT). 시스템은 target table의 schema가 없으면 table name에서 schema를 도출하여 생성해야 한다(SHALL). Caller가 expected current content identity를 제공하면 시스템은 replacement transaction 안에서 mutation 전에 actual identity와 비교해야 하며 다르면 교체해서는 안 된다(SHALL).

#### Scenario: Year partition reload

- **WHEN** 같은 `source_year` partition을 동일 입력으로 반복 적재할 때
- **THEN** 대상 partition의 최종 행 집합과 행 수는 한 번 적재한 결과와 같아야 한다.

#### Scenario: File-scoped reload

- **WHEN** `source_file`이 지정된 partition 적재를 실행할 때
- **THEN** 지정된 파일 범위만 교체 대상이 되어야 한다.

#### Scenario: Failed partition replacement

- **WHEN** 기존 partition을 새 입력으로 교체하는 작업이 완료되기 전에 실패할 때
- **THEN** 기존 partition은 부분적으로 삭제되거나 새 입력과 혼합된 상태로 남아서는 안 된다.

#### Scenario: Custom schema partition load

- **GIVEN** target schema가 없는 새 DuckDB database와 `bronze.hmda_loans` target이 주어졌을 때
- **WHEN** caller가 partition load를 실행할 때
- **THEN** loader는 `bronze` schema와 configured table을 생성하고 해당 partition 행 수를 반환해야 한다.

#### Scenario: Serialized expected-state replacement

- **GIVEN** caller가 actual target과 일치하는 expected current content identity를 제공할 때
- **WHEN** partition replacement를 실행할 때
- **THEN** identity 확인과 replacement는 local concurrent writer가 끼어들 수 없는 경계에서 완료되어야 한다.

#### Scenario: Stale expected state

- **GIVEN** caller의 expected current content identity와 actual target이 다를 때
- **WHEN** partition replacement를 요청할 때
- **THEN** target partition을 변경하지 않고 stale-state failure로 종료해야 한다.

### Requirement: Stable partition content identity

시스템은 `table + source_year + optional source_file` 범위의 stable content identity를 계산할 수 있어야 한다(SHALL). Identity는 row order와 실행마다 달라지는 ingestion metadata에 독립적이어야 하고 duplicate row multiplicity를 보존해야 한다(SHALL).

#### Scenario: Equivalent partition content

- **GIVEN** 같은 logical row multiset이 다른 순서와 다른 volatile ingestion metadata로 저장되어 있을 때
- **WHEN** 같은 partition scope의 content identity를 계산할 때
- **THEN** 두 identity는 같아야 한다.

#### Scenario: Duplicate or value drift

- **WHEN** row value 또는 duplicate multiplicity가 다른 두 partition의 content identity를 계산할 때
- **THEN** 두 identity는 달라야 한다.

### Requirement: Source value preservation

시스템은 원천의 null, 코드값과 수치 이상치를 정규화하거나 품질 판단으로 제거하지 않고 Bronze에 보존해야 한다(SHALL).

#### Scenario: Quality outlier input

- **WHEN** 입력에 음수 소득, 큰 대출 금액 또는 알 수 없는 코드값이 있을 때
- **THEN** 필수 구조 계약을 만족하는 행은 품질 분석 대상이 될 수 있도록 적재되어야 한다.

### Requirement: Serialized managed Bronze mutation

시스템은 file-based DuckDB target에 대한 HMDA full-load와 partition replacement를 공통 database mutation lock 안에서 실행해야 한다(SHALL). Lock은 target을 처음 생성하거나 변경하기 전에 획득하고 full-load call 종료 또는 partition transaction의 commit/rollback까지 유지해야 한다(SHALL). Expected current identity가 있는 partition replacement는 lock 획득 후 actual identity를 다시 계산해야 한다(SHALL). 이 serialization은 full-load의 기존 validation-after-replacement failure semantics를 변경하지 않아야 한다(MUST NOT).

#### Scenario: Concurrent full-load writers

- **GIVEN** 두 full-load request가 같은 physical DuckDB file을 대상으로 할 때
- **WHEN** 첫 request가 target replacement를 실행 중일 때
- **THEN** 두 번째 request는 첫 request가 commit 또는 rollback할 때까지 target mutation을 시작해서는 안 된다.

#### Scenario: Concurrent expected-state partition replacement

- **GIVEN** 두 partition replacement가 같은 approved before identity를 사용하고 첫 request가 target을 변경했을 때
- **WHEN** 두 번째 request가 mutation lock을 획득할 때
- **THEN** 두 번째 request는 current identity를 다시 계산하고 stale-state failure로 target mutation 없이 종료해야 한다.

#### Scenario: Concurrent unrelated partition writer

- **GIVEN** 두 managed writer가 같은 database의 서로 다른 partition을 변경하려 할 때
- **WHEN** 한 writer가 mutation lock을 보유할 때
- **THEN** 다른 writer는 database-level lock이 해제된 뒤에 mutation을 진행해야 한다.

#### Scenario: Mutation lock failure

- **WHEN** HMDA ingestion이 target database mutation lock을 획득하지 못할 때
- **THEN** target table 또는 partition을 변경하지 않고 domain failure로 종료해야 한다.
