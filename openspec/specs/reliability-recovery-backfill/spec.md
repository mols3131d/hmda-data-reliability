# reliability-recovery-backfill Specification

## Purpose

명시적으로 승인된 HMDA partition recovery를 실행하고 backfill 이후 profile을 재측정해 validation 결과를 제공하는 계약을 정의한다.

## Requirements

### Requirement: Approval gate

시스템은 recovery 실행 전에 approval이 승인 상태이며 `overwrite_partition`과 `rerun_profile_snapshot` action을 모두 허용하는지 확인해야 한다(SHALL).

#### Scenario: Missing approval

- **WHEN** 승인되지 않았거나 필수 action이 없는 recovery를 요청할 때
- **THEN** source 처리와 target 변경 전에 요청을 차단해야 한다.

### Requirement: Partition backfill

시스템은 승인된 request의 `source_year`와 optional `source_file`이 식별하는 HMDA target partition을 overwrite 방식으로 재처리해야 한다(SHALL).

#### Scenario: Approved backfill

- **WHEN** 유효한 approval, source input과 target partition이 주어질 때
- **THEN** 대상 partition을 재적재하고 적재 row count를 반환해야 한다.

### Requirement: Profile alignment

Post-backfill profile request는 backfill target table과 같은 table을 가리키고 partition identity는 recovery target과 일치해야 한다(SHALL).

#### Scenario: Misaligned profile request

- **WHEN** profile target 또는 partition이 recovery target과 다를 때
- **THEN** 시스템은 backfill 실행 전에 요청을 거부해야 한다.

### Requirement: Post-backfill validation

시스템은 backfill 이후 aligned profile snapshot을 생성하고 snapshot row count와 적재 row count의 일치 여부를 validation 결과로 제공해야 한다(SHALL). `source_file` scoped backfill의 row-count 비교를 file-level population equivalence로 해석해서는 안 된다(MUST NOT).

#### Scenario: Profile validation

- **WHEN** approved backfill이 성공할 때
- **THEN** 결과는 새 profile snapshot과 row-count comparison을 포함해야 한다.

### Requirement: Recovery remains outside read-only lifecycle

시스템은 read-only incident lifecycle이 recovery를 자동으로 실행하게 해서는 안 된다(MUST NOT).

#### Scenario: Incident lifecycle execution

- **WHEN** read-only incident lifecycle이 incident와 remediation draft를 생성할 때
- **THEN** approved backfill은 자동으로 실행되어서는 안 된다.
