---
type: openspec-spec-driven-tdd-spec
category: spec
title: "hmda-eda-baseline"
description: "HMDA EDA를 6개 core column의 read-only descriptive evidence로 축소한다."
tags:
  - "domain:hmda-data"
  - "subdomain:eda"
  - "capability:hmda-eda-baseline"
  - "scope-reduction"
---

## ADDED Requirements

### Requirement: Core numeric summaries

시스템은 `loan_amount`와 `income`에 대해 non-null count, min, p25, median, p75와 max를 제공해야 한다(SHALL). 원천 값을 삭제하거나 clipping해서는 안 된다(MUST NOT).

#### Scenario: Numeric summary evidence

- **WHEN** 유효한 HMDA source를 분석할 때
- **THEN** `loan_amount`와 `income` 각각의 non-null count와 five-number summary를 반환해야 한다.
- **AND** null은 summary population에서 제외하고 null count는 별도 core metric으로 제공해야 한다.

### Requirement: Minimal notebook rendering

Notebook은 공유 EDA entrypoint의 결과를 입력, schema, volume, null, categorical distribution, numeric summary와 mart grain section으로 표시해야 한다(SHALL).

#### Scenario: Valid source rendering

- **WHEN** valid fixture로 Notebook smoke를 실행할 때
- **THEN** 모든 core section이 계산 결과를 사용해 렌더링되어야 한다.
- **AND** Notebook은 별도의 anomaly, freshness 또는 Profile mapping section을 생성해서는 안 된다.

#### Scenario: Invalid source failure

- **WHEN** missing-column 또는 malformed source로 Notebook smoke를 실행할 때
- **THEN** 원래 validation 또는 parse failure를 식별할 수 있어야 한다.
- **AND** 완료된 core evidence section을 partial success로 표시해서는 안 된다.

### Requirement: Actual-source observation

Foundation 종료 전 실제 HMDA source를 공유 EDA entrypoint로 한 번 read-only 실행하고 source identifier, 실행 시각·환경, row count, activity-year 범위, duration, 핵심 observation과 limitation을 기록해야 한다(SHALL).

#### Scenario: Actual-source smoke evidence

- **WHEN** focused correctness와 Notebook smoke가 통과한 뒤 actual-source observation을 수행할 때
- **THEN** 재현 가능한 command와 관찰 결과를 EDA reference에 기록해야 한다.
- **AND** 이 결과를 strict performance threshold 또는 OOM 안전성 보장으로 표현해서는 안 된다.

## MODIFIED Requirements

### Requirement: HMDA required schema baseline

EDA는 원천 HMDA CSV에서 `activity_year`, `state_code`, `loan_purpose`, `action_taken`, `loan_amount`, `income`의 존재와 expected type family 충족 상태를 검증해야 한다(SHALL). `county_code`의 source 존재 검증은 ingestion contract가 소유하며 EDA core schema에 포함하지 않아야 한다(MUST NOT).

#### Scenario: Core columns가 모두 유효한 경우

- **WHEN** 원천 CSV가 6개 core column과 호환 타입을 포함할 때
- **THEN** EDA는 각 core column의 존재 상태와 추론 타입을 제공해야 한다.
- **AND** `county_code` 유무를 이유로 EDA 실행을 실패시켜서는 안 된다.

#### Scenario: Core schema 불일치

- **WHEN** core column이 누락되거나 타입 기준과 호환되지 않을 때
- **THEN** 대상 column과 불일치 이유를 포함한 validation failure를 반환해야 한다.
- **AND** partial evidence를 성공 결과로 반환해서는 안 된다.

### Requirement: Volume and null baseline

EDA는 전체 row count, `activity_year`별 row count와 6개 core column별 null count·null rate를 제공해야 한다(SHALL).

#### Scenario: Core null baseline 계산

- **WHEN** 유효한 HMDA source를 분석할 때
- **THEN** 6개 core column별 null count와 `null_count / total_row_count` null rate를 반환해야 한다.
- **AND** `NA`와 빈 문자열을 null로 해석한 reader 조건을 제공해야 한다.

#### Scenario: Partition volume baseline 계산

- **WHEN** 유효한 HMDA source를 분석할 때
- **THEN** 전체 row count와 `activity_year`별 row count를 반환해야 한다.

### Requirement: Core code distributions

시스템은 `state_code`, `loan_purpose`, `action_taken`의 observed non-null value별 count와 전체 row 대비 share를 제공해야 한다(SHALL). code 의미를 분류하거나 허용 목록 밖의 값을 anomaly로 판정해서는 안 된다(MUST NOT).

#### Scenario: Code distribution evidence

- **WHEN** 유효한 HMDA source를 분석할 때
- **THEN** 세 categorical field의 observed value별 count와 share를 반환해야 한다.
- **AND** null은 별도 null metric으로 제공하고 observed value를 정제하거나 변환해서는 안 된다.

#### Scenario: Unrecognized value preservation

- **WHEN** EDA가 해석하지 않는 categorical value가 관찰될 때
- **THEN** 해당 값은 일반 observed value로 count되어야 한다.
- **AND** unknown 또는 anomaly classification을 생성해서는 안 된다.

### Requirement: MVP grain alignment

시스템은 `activity_year + state_code + loan_purpose` grain의 distinct group count, null key row count와 coverage rate를 제공해야 한다(SHALL). EDA는 canonical business grain이나 dbt mart grouping rule을 변경해서는 안 된다(MUST NOT).

#### Scenario: Mart grain evidence

- **WHEN** 유효한 HMDA source를 분석할 때
- **THEN** grain columns, distinct group count, null key row count와 coverage rate를 반환해야 한다.
- **AND** 결과는 현재 Gold mart를 설명하는 관찰값이며 새로운 mart contract로 취급되어서는 안 된다.

### Requirement: Reusable EDA computation boundary

시스템은 HMDA CSV path와 명시적인 DuckDB resource 설정을 입력받아 JSON-serializable core evidence를 반환하는 `analyze_hmda_csv` entrypoint를 제공해야 한다(SHALL). Notebook과 automated test는 같은 entrypoint를 사용해야 한다(MUST).

#### Scenario: Shared calculation path

- **WHEN** Notebook 또는 automated test가 EDA를 실행할 때
- **THEN** `analyze_hmda_csv`를 호출해야 한다.
- **AND** 결과는 source metadata, duration, schema, volume, null, distribution, numeric summary와 grain을 포함해야 한다.
- **AND** anomaly, freshness, schema hash 또는 Profile mapping key를 포함해서는 안 된다.

## REMOVED Requirements

### Requirement: Numeric summary and anomaly observation

- **Reason** - Numeric summary는 유지하지만 근거가 확정되지 않은 suspicious condition과 anomaly classification은 Foundation EDA 책임이 아니다.
- **Migration** - `Core numeric summaries` requirement로 summary 계약만 이전한다.

### Requirement: Profile evidence mapping

- **Reason** - Descriptive EDA를 production `ProfileSnapshot` schema와 결합하지 않는다.
- **Migration** - Profile mapping이 필요하면 reliability profile capability에서 별도로 정의한다.

### Requirement: Source freshness measurement boundary

- **Reason** - 현재 source에는 신뢰할 수 있는 observation timestamp contract가 없으며 Foundation EDA 필수 근거가 아니다.
- **Migration** - Freshness는 Bronze ingestion 또는 reliability profile의 versioned contract에서 다룬다.

### Requirement: Representative HMDA memory workload

- **Reason** - Representative fixture와 manifest는 최소 descriptive EDA보다 큰 독립 resource-validation capability다.
- **Migration** - 실제 성능 문제가 확인되면 별도 change로 재설계한다.

### Requirement: Process-level memory budget enforcement

- **Reason** - Foundation EDA는 systemd/container hard-limit gate를 소유하지 않는다.
- **Migration** - 별도 performance workstream이 명시적인 환경과 threshold를 소유한다.

### Requirement: Memory result and correctness validation

- **Reason** - Process resource report는 focused correctness와 actual-source observation의 완료 조건이 아니다.
- **Migration** - Core correctness는 deterministic small fixture, 실제 데이터 근거는 one-time observation으로 검증한다.

### Requirement: Memory test isolation

- **Reason** - Representative memory test 자체를 제거한다.
- **Migration** - 기본 test는 focused correctness와 terminating Notebook smoke만 실행한다.
