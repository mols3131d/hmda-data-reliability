---
type: openspec-spec-driven-tdd-spec
category: spec
title: reliability-data-contracts
description: Vendor-neutral orchestration evidence source for Reliability contracts.
tags:
  - capability:reliability-data-contracts
---

## MODIFIED Requirements

### Requirement: Evidence contract

시스템은 RCA와 영향 분석에 사용할 evidence를 독립적으로 참조 가능한 contract로 표현해야 한다(SHALL). Evidence source는 profile, table metadata, dbt artifact, catalog 또는 vendor-neutral orchestration execution 중 하나여야 하며(MUST), 특정 orchestration vendor를 contract에 노출해서는 안 된다(MUST NOT).

#### Scenario: Evidence reference

- **GIVEN** profile, metadata, dbt artifact, catalog 또는 orchestration execution 중 하나에서 근거가 수집됨
- **WHEN** `Evidence`가 생성됨
- **THEN** evidence는 `evidence_id`, `source`, `asset_name`, `partition`, `observed_at`, `summary`, `payload`를 포함해야 함
- **AND** orchestration execution에서 온 evidence의 source는 `ORCHESTRATION`이어야 함
- **AND** source는 `DAGSTER` 또는 `AIRFLOW` 같은 vendor-specific value가 아니어야 함
- **AND** incident는 `evidence_id`를 통해 evidence를 참조해야 함
