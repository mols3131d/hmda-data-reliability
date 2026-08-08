# orchestration-pipeline Specification

## Purpose

HMDA Bronze load와 analytics build를 data-plane asset graph로 연결하고 실행 순서, config delegation과 materialization evidence를 제공하는 orchestration 계약을 정의한다.

## Requirements

### Requirement: Data-plane asset graph

시스템은 Bronze raw load asset과 analytics build asset을 하나의 loadable orchestration graph로 제공해야 한다(SHALL). Analytics asset은 raw load asset에 의존해야 한다(MUST).

#### Scenario: Graph inspection

- **WHEN** orchestration definitions를 로드할 때
- **THEN** `raw_hmda_loans`, `dbt_loan_analytics`와 해당 graph를 실행하는 `pipeline_job`을 식별할 수 있어야 한다.

### Requirement: Ordered materialization

시스템은 pipeline 실행 시 raw load가 성공한 뒤 analytics build를 실행해야 한다(SHALL).

#### Scenario: Pipeline materialization

- **WHEN** `pipeline_job`을 materialize할 때
- **THEN** `raw_hmda_loans` 이후 `dbt_loan_analytics`가 실행되어야 한다.

### Requirement: Materialization metadata

각 asset materialization은 caller가 실행 범위와 결과를 판단할 수 있는 핵심 metadata를 기록해야 한다(SHALL).

#### Scenario: Raw materialization

- **WHEN** raw asset이 완료될 때
- **THEN** source 범위와 적재 row count를 확인할 수 있어야 한다.

#### Scenario: Analytics materialization

- **WHEN** analytics asset materialization이 완료될 때
- **THEN** analytics 실행 상태와 available artifact 위치를 확인할 수 있어야 한다.

### Requirement: Domain delegation

Orchestration은 source parsing, ingestion, analytics build 또는 reliability business rule을 중복 구현하지 않고 application/domain entrypoint에 위임해야 한다(SHALL).

### Requirement: Configuration boundary

Orchestration resource는 runtime config를 data-operations request로 변환할 수 있어야 하며(SHALL), domain behavior 자체를 소유해서는 안 된다(MUST NOT).

### Requirement: Control-plane exclusion

Data-plane graph는 read-only incident lifecycle, approval, recovery와 evaluation을 자동으로 포함하거나 실행해서는 안 된다(MUST NOT).
