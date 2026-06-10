## ADDED Requirements

### Requirement: Approval gate for backfill

시스템은 backfill 실행 전에 `ApprovalStatus.APPROVED` 상태를 확인해야 한다(SHALL).

#### Scenario: 미승인 요청 차단

- **WHEN** approval status가 `APPROVED`가 아닌 요청으로 backfill을 실행할 때
- **THEN** 시스템은 target partition을 변경하지 않고 도메인 예외를 발생시켜야 한다.

### Requirement: Partition overwrite execution

시스템은 승인된 요청에 대해 대상 partition을 overwrite 방식으로 재처리해야 한다(SHALL).

#### Scenario: 승인된 partition backfill

- **WHEN** 승인된 approval과 source parquet, partition date가 주어질 때
- **THEN** 시스템은 해당 partition을 재적재하고 적재 row count를 반환해야 한다.

### Requirement: Post-backfill profile validation

시스템은 backfill 완료 후 같은 partition의 `ProfileSnapshot`을 자동 재생성해야 한다(SHALL).

#### Scenario: profile snapshot 재생성

- **WHEN** 승인된 backfill이 성공할 때
- **THEN** 결과는 갱신된 데이터를 기반으로 생성된 `ProfileSnapshot`을 포함해야 한다.
