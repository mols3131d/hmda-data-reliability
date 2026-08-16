---
type: openspec-spec-driven-tdd-spec
category: spec
title: data-operations-incident-lifecycle
description: Read-only lifecycle이 caller의 explicit detection thresholds를 그대로 사용하도록 변경한다.
tags:
  - "domain:reliability"
  - "capability:data-operations-incident-lifecycle"
  - "freshness-delay"
---

## ADDED Requirements

### Requirement: Configured detection thresholds

시스템은 caller가 incident lifecycle에 explicit detection thresholds를 제공할 수 있어야 하며 current profile detection에 같은 값을 전달해야 한다(SHALL). Caller가 thresholds를 제공하지 않으면 canonical default thresholds를 사용해야 한다(SHALL).

#### Scenario: Explicit freshness max age

- **GIVEN** caller가 `freshness_max_age_minutes`를 포함한 thresholds를 제공할 때
- **WHEN** read-only lifecycle이 current profile을 평가할 때
- **THEN** freshness detection evidence와 판정은 제공된 max age를 사용해야 한다.

#### Scenario: Default detection thresholds

- **WHEN** caller가 별도 thresholds 없이 lifecycle을 실행할 때
- **THEN** 기존 volume, null, schema와 freshness default threshold 동작을 유지해야 한다.
