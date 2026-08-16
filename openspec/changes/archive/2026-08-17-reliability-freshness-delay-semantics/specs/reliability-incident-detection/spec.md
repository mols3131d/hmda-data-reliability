---
type: openspec-spec-driven-tdd-spec
category: spec
title: reliability-incident-detection
description: Freshness delay를 current observation의 measured age와 max-age threshold로 판정한다.
tags:
  - "domain:reliability"
  - "capability:reliability-incident-detection"
  - "freshness-delay"
---

## MODIFIED Requirements

### Requirement: Freshness delay detection

시스템은 current profile의 freshness measurement가 `measured`이면 `freshness_age = current.observed_at - current.freshness_at`을 계산하고 configured `freshness_max_age_minutes` 이상일 때 `freshness_delay` incident를 생성해야 한다(SHALL). 판정은 baseline freshness 차이가 아니라 current age를 사용해야 한다(MUST). Current measurement가 `unavailable`이면 freshness incident를 생성해서는 안 되지만 다른 detection rule의 실행을 막아서도 안 된다(MUST NOT). Evidence는 `observed_at`, `freshness_at`, `freshness_status`, `freshness_age_minutes`와 `max_age_minutes`를 포함해야 한다(SHALL).

#### Scenario: Age at exact max-age boundary

- **GIVEN** current freshness timestamp가 `observed_at`보다 configured max age만큼 과거일 때
- **WHEN** profile detection을 실행할 때
- **THEN** `freshness_delay` incident와 exact age/threshold evidence를 생성해야 한다.

#### Scenario: Age below max-age boundary

- **GIVEN** current freshness age가 configured max age보다 작을 때
- **WHEN** profile detection을 실행할 때
- **THEN** `freshness_delay` incident를 생성해서는 안 된다.

#### Scenario: Unchanged timestamp becomes stale

- **GIVEN** baseline과 current의 `freshness_at`이 같지만 current `observed_at` 기준 age가 max age 이상일 때
- **WHEN** profile detection을 실행할 때
- **THEN** baseline과의 timestamp 차이가 없어도 `freshness_delay` incident를 생성해야 한다.

#### Scenario: Unavailable freshness measurement

- **GIVEN** current profile의 freshness status가 `unavailable`일 때
- **WHEN** profile detection을 실행할 때
- **THEN** freshness measurement가 fresh하다고 보고하거나 `freshness_delay` incident를 생성해서는 안 된다.
- **AND** row count, null rate와 schema detection은 정상적으로 계속되어야 한다.
