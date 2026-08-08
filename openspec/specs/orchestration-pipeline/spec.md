# orchestration-pipeline Specification

## Purpose

HMDA Bronze load와 analytics build를 data-plane asset graph로 연결하고 실행 순서, config delegation과 materialization evidence를 제공하는 orchestration 계약을 정의한다.

## Requirements

### Requirement: Data-plane asset graph

시스템은 Bronze raw load asset과 analytics build asset을 하나의 loadable orchestration graph로 제공해야 한다(SHALL). Analytics asset은 raw load asset에 의존해야 한다(MUST).

#### Scenario: Graph inspection

- **WHEN** orchestration definitions를 로드할 때
- **THEN** Bronze raw load와 analytics build asset 및 해당 graph의 실행 경로를 식별할 수 있어야 한다.

### Requirement: Ordered materialization

시스템은 pipeline 실행 시 raw load가 성공한 뒤 analytics build를 실행해야 한다(SHALL).

#### Scenario: Pipeline materialization

- **WHEN** data-plane pipeline을 materialize할 때
- **THEN** raw load 이후 analytics build가 실행되어야 한다.

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

#### Scenario: Delegated asset execution

- **WHEN** data-plane asset이 domain 작업을 실행할 때
- **THEN** orchestration은 해당 domain/application boundary에 작업을 위임하고 dependency, config와 materialization evidence만 조율해야 한다.

### Requirement: Configuration boundary

Orchestration resource는 runtime config를 data-operations request로 변환할 수 있어야 하며(SHALL), domain behavior 자체를 소유해서는 안 된다(MUST NOT).

#### Scenario: Runtime configuration conversion

- **WHEN** caller가 orchestration runtime config를 제공할 때
- **THEN** resource는 이를 data-operations request로 변환해야 하며 source parsing이나 analytics behavior를 직접 수행해서는 안 된다.

### Requirement: Single pipeline orchestration owner

시스템은 data-plane 전체 실행 순서를 orchestration graph가 소유하게 해야 하며(SHALL), 다른 domain이 별도의 full-pipeline coordinator를 공개해서는 안 된다(MUST NOT).

#### Scenario: Full pipeline execution surface

- **WHEN** 시스템의 full-pipeline 실행 surface를 확인할 때
- **THEN** data-plane orchestration graph가 단계 순서를 소유해야 하고 data-operations는 별도 전체-pipeline 조율 surface를 제공해서는 안 된다.

### Requirement: Control-plane exclusion

Data-plane graph는 read-only incident lifecycle, approval, recovery와 evaluation을 자동으로 포함하거나 실행해서는 안 된다(MUST NOT).

#### Scenario: Data-plane pipeline execution

- **WHEN** data-plane pipeline이 실행될 때
- **THEN** incident lifecycle, approval, recovery 또는 evaluation이 암묵적으로 실행되어서는 안 된다.
