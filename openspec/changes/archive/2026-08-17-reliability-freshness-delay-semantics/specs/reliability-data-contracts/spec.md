---
type: openspec-spec-driven-tdd-spec
category: spec
title: reliability-data-contracts
description: ProfileSnapshot이 측정된 freshness와 unavailable 상태를 명시적으로 교환하도록 변경한다.
tags:
  - "domain:reliability"
  - "capability:reliability-data-contracts"
  - "freshness-delay"
---

## MODIFIED Requirements

### Requirement: ProfileSnapshot contract

시스템은 incident detection 입력 지표를 `ProfileSnapshot`으로 표현해야 한다(SHALL). Snapshot은 `row_count`, `null_rates`, `schema_hash`, nullable `freshness_at`, `freshness_status`와 `metric_values`를 포함하고 JSON으로 직렬화 가능해야 한다(SHALL). `freshness_status=measured`이면 `freshness_at`이 반드시 존재하고, `freshness_status=unavailable`이면 `freshness_at`은 반드시 `null`이어야 한다(MUST).

#### Scenario: Measured profile input

- **GIVEN** partition freshness timestamp가 측정되었을 때
- **WHEN** `ProfileSnapshot`을 생성하고 JSON으로 직렬화할 때
- **THEN** `freshness_status`는 `measured`이고 `freshness_at`은 측정 timestamp여야 한다.

#### Scenario: Unavailable profile input

- **GIVEN** partition freshness timestamp를 측정할 수 없을 때
- **WHEN** `ProfileSnapshot`을 생성하고 JSON으로 직렬화할 때
- **THEN** `freshness_status`는 `unavailable`이고 `freshness_at`은 `null`이어야 한다.

#### Scenario: Inconsistent freshness fields

- **WHEN** measurement status와 nullable timestamp가 서로 일치하지 않는 snapshot을 생성할 때
- **THEN** contract validation은 해당 snapshot을 거부해야 한다.
