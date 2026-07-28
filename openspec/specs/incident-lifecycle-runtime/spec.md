## Purpose

caller-supplied baseline과 실제 current profile을 비교해 탐지·영향 분석·remediation draft만 수행하는 operational incident lifecycle 계약을 정의한다.

## Requirements

### Requirement: Actual profile comparison

시스템은 caller가 제공한 baseline `ProfileSnapshot`과 DuckDB 대상 partition에서 새로 측정한 current `ProfileSnapshot`을 비교해야 한다(SHALL). 시스템은 운영 lifecycle에서 snapshot 값을 합성하지 않아야 한다(MUST NOT).

#### Scenario: Compare baseline with current partition

- **WHEN** caller가 유효한 data operation request와 baseline profile을 전달할 때
- **THEN** 시스템은 request의 table과 partition에서 current profile을 계산해야 한다.
- **AND** detector는 전달된 baseline과 계산된 current를 입력으로 받아야 한다.

#### Scenario: Reject incompatible baseline

- **WHEN** baseline과 current의 asset 또는 partition이 다를 때
- **THEN** 시스템은 비교 대상을 포함한 `DataOperationError`를 발생시켜야 한다.

### Requirement: Complete incident analysis

시스템은 탐지된 모든 incident에 대해 dbt lineage impact analysis와 remediation draft를 생성해야 한다(SHALL).

#### Scenario: Analyze multiple detections

- **WHEN** current profile 비교에서 둘 이상의 incident가 탐지될 때
- **THEN** 결과는 각 incident의 evidence와 lineage evidence를 포함해야 한다.
- **AND** 결과는 모든 incident에서 도출된 affected assets와 remediation actions를 포함해야 한다.
- **AND** 요약 목록은 탐지 순서를 유지하며 중복 값을 한 번만 포함해야 한다.

#### Scenario: No incident detected

- **WHEN** baseline과 current가 detection threshold를 넘지 않을 때
- **THEN** 시스템은 빈 incident, evidence, affected asset, action 목록을 반환해야 한다.
- **AND** dbt impact analysis를 실행하지 않아야 한다.

### Requirement: Detection-only lifecycle boundary

시스템은 lifecycle 단계에서 approval 생성, partition backfill, post-backfill validation, synthetic evaluation을 실행하지 않아야 한다(MUST NOT).

#### Scenario: Lifecycle completes with an incident

- **WHEN** lifecycle 단계가 하나 이상의 incident와 remediation draft를 생성할 때
- **THEN** 시스템은 DuckDB target partition을 변경하지 않아야 한다.
- **AND** evaluation report 파일을 생성하지 않아야 한다.
- **AND** approval 객체를 생성하지 않아야 한다.

### Requirement: Operational lifecycle result

시스템은 실제 관측값과 탐지·영향·조치 요약을 `LifecycleResult`로 반환해야 한다(SHALL).

#### Scenario: Return lifecycle summary

- **WHEN** lifecycle 단계가 완료될 때
- **THEN** 결과는 metadata row count, baseline row count, current row count, detected incident types, evidence refs, affected assets, recommended actions, backfill actions, validation actions를 포함해야 한다.
- **AND** 결과는 evaluation report path, evaluation success rate, backfill validation 결과를 포함하지 않아야 한다.
