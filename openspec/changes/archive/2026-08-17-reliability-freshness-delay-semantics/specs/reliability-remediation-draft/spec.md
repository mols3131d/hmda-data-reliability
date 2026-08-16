---
type: openspec-spec-driven-tdd-spec
category: spec
title: reliability-remediation-draft
description: Freshness remediation이 Bronze ingestion boundary를 정확히 가리키도록 변경한다.
tags:
  - "domain:reliability"
  - "capability:reliability-remediation-draft"
  - "freshness-delay"
---

## MODIFIED Requirements

### Requirement: Incident-specific actions

시스템은 incident type과 evidence payload를 바탕으로 검증 가능한 recommended action을 결정해야 한다(SHALL). `freshness_delay` action은 현재 측정하는 Bronze ingestion freshness와 partition reload 검토를 가리켜야 하며 upstream publication freshness를 확인했다고 표현해서는 안 된다(MUST NOT).

#### Scenario: Volume drop

- **WHEN** `volume_drop` incident의 draft를 만들 때
- **THEN** source partition validation과 partition backfill 준비 action을 제안해야 한다.

#### Scenario: Bronze ingestion freshness delay

- **WHEN** `freshness_delay` incident의 draft를 만들 때
- **THEN** `check_bronze_ingestion_freshness`와 partition backfill 검토 action을 제안해야 한다.
- **AND** upstream HMDA publication freshness를 검증한 것으로 표현해서는 안 된다.
