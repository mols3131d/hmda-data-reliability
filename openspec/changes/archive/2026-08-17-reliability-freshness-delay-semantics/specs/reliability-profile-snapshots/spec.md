---
type: openspec-spec-driven-tdd-spec
category: spec
title: reliability-profile-snapshots
description: Freshness measurement를 Bronze timestamp 또는 explicit unavailable 상태로 제한한다.
tags:
  - "domain:reliability"
  - "capability:reliability-profile-snapshots"
  - "freshness-delay"
---

## MODIFIED Requirements

### Requirement: Freshness metric

시스템은 freshness column이 제공되고 partition에서 timestamp를 측정할 수 있으면 해당 column의 최대 timestamp를 `freshness_at`으로 사용하고 `freshness_status=measured`를 반환해야 한다(SHALL). Freshness column이 없거나 partition에서 값을 측정할 수 없으면 `freshness_at=null`, `freshness_status=unavailable`을 반환해야 하며 `observed_at`을 freshness timestamp로 대체해서는 안 된다(MUST NOT). 측정 timestamp가 `observed_at`보다 미래이면 성공한 profile로 반환해서는 안 된다(MUST NOT).

#### Scenario: Measured Bronze ingestion freshness

- **GIVEN** HMDA Bronze partition에 `ingested_at` 값이 있을 때
- **WHEN** `ingested_at`을 freshness column으로 profile할 때
- **THEN** `freshness_at`은 partition의 `max(ingested_at)`과 일치해야 한다.
- **AND** `freshness_status`는 `measured`여야 한다.

#### Scenario: Missing freshness measurement

- **WHEN** freshness column이 제공되지 않거나 대상 partition의 값이 모두 null일 때
- **THEN** `freshness_at`은 `null`이고 `freshness_status`는 `unavailable`이어야 한다.
- **AND** `observed_at` fallback 또는 `freshness_used_fallback` numeric metric을 생성해서는 안 된다.

#### Scenario: Future freshness measurement

- **GIVEN** partition의 최대 freshness timestamp가 profile `observed_at`보다 미래일 때
- **WHEN** profile snapshot을 계산할 때
- **THEN** 시스템은 해당 measurement를 fresh 상태로 반환하지 않고 profile failure로 종료해야 한다.
