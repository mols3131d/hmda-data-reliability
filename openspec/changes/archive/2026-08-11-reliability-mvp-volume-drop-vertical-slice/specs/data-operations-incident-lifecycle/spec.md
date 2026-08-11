---
type: openspec-spec-driven-tdd-spec
category: spec
title: data-operations-incident-lifecycle
description: Read-only volume-drop analysis가 recovery proposal 입력 identity를 제공하도록 변경한다.
tags:
  - "domain:reliability"
  - "capability:data-operations-incident-lifecycle"
  - "mvp"
  - "volume-drop"
---

## MODIFIED Requirements

### Requirement: Lifecycle result

시스템은 실제 관측값과 detection, impact, remediation 요약을 하나의 lifecycle result로 반환해야 한다(SHALL). Detection이 있으면 각 incident의 target partition, observed target state, remediation candidate requirement와 판단에 사용한 dbt artifact projection을 recovery proposal 입력으로 식별할 수 있어야 한다(SHALL).

#### Scenario: Return summary

- **WHEN** lifecycle이 완료될 때
- **THEN** 결과는 metadata row count, baseline/current row count, incident types, evidence refs, affected assets와 remediation actions를 포함해야 한다.

#### Scenario: Volume-drop recovery inputs

- **WHEN** target partition에서 `volume_drop` incident와 remediation draft가 생성될 때
- **THEN** 결과는 incident, target partition, observed target state, candidate requirement와 dbt artifact projection identity를 포함해야 한다.

#### Scenario: Clean baseline result

- **WHEN** detection threshold를 넘는 incident가 없을 때
- **THEN** incident, remediation draft와 recovery proposal 입력은 비어 있어야 한다.
