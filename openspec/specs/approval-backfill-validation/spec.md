# approval-backfill-validation Specification

## Purpose

승인 상태와 필수 recovery action을 검증한 뒤 HMDA target partition을 overwrite하고 같은 partition의 profile을 재생성해 backfill 결과를 검증하는 계약을 정의한다.

## Requirements

### Requirement: Approval gate for backfill

시스템은 backfill 실행 전에 approval이 승인 상태이며 `overwrite_partition`과 `rerun_profile_snapshot` action을 모두 허용하는지 확인해야 한다(SHALL).

#### Scenario: 미승인 요청 차단

- **WHEN** 승인 상태가 아닌 요청으로 backfill을 실행할 때
- **THEN** 시스템은 source 처리와 target partition 변경 전에 reliability 도메인 오류로 차단해야 한다.

#### Scenario: 필수 action 누락 차단

- **WHEN** 승인된 요청에 `overwrite_partition` 또는 `rerun_profile_snapshot` action이 없을 때
- **THEN** 시스템은 source 처리와 target partition 변경 전에 reliability 도메인 오류로 차단해야 한다.

### Requirement: Partition overwrite execution

시스템은 승인된 요청의 source input으로 `source_year`와 optional `source_file`이 식별하는 HMDA target partition을 overwrite 방식으로 재처리해야 한다(SHALL).

#### Scenario: 승인된 partition backfill

- **WHEN** 유효한 approval, source input과 target partition identity가 주어질 때
- **THEN** 시스템은 해당 partition을 재적재하고 적재 row count를 반환해야 한다.

### Requirement: Post-backfill profile validation

시스템은 backfill 완료 후 같은 target table과 `source_year` partition의 profile snapshot을 재생성해야 한다(SHALL).

#### Scenario: profile snapshot 재생성

- **WHEN** 승인된 backfill이 성공할 때
- **THEN** 결과는 갱신된 partition을 기반으로 생성된 profile snapshot을 포함해야 한다.
- **AND** 재생성된 profile row count와 적재 row count의 일치 여부를 validation 결과로 제공해야 한다.
