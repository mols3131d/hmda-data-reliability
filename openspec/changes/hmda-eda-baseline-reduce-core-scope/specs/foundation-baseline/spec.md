---
type: openspec-spec-driven-tdd-spec
category: spec
title: "foundation-baseline"
description: "Foundation EDA readiness를 최소 descriptive profile과 actual-source observation으로 축소한다."
tags:
  - "domain:hmda-data"
  - "subdomain:eda"
  - "capability:foundation-baseline"
  - "scope-reduction"
---

## MODIFIED Requirements

### Requirement: Foundational EDA readiness

Foundation 완료 전 HMDA EDA는 6개 core column의 schema와 type compatibility, 전체·`activity_year`별 volume, null, categorical distribution, numeric summary와 mart grain을 read-only evidence로 제공해야 한다(MUST). 결과와 재현 경로는 공유 Python entrypoint, 최소 Notebook, automated test와 actual-source 1회 observation으로 추적 가능해야 한다(MUST).

Memory benchmark, freshness, schema hash, `ProfileSnapshot` mapping, unknown-code classification과 numeric anomaly rule은 Foundation EDA 완료 조건에 포함하지 않아야 한다(MUST NOT).

#### Scenario: HMDA core EDA 완료 확인

- **WHEN** 사용자가 Foundation readiness를 검토할 때
- **THEN** 6개 core column의 schema 상태, row count, `activity_year`별 volume, null count·rate를 확인할 수 있어야 한다.
- **AND** `state_code`, `loan_purpose`, `action_taken`의 count·share와 `loan_amount`, `income`의 five-number summary를 확인할 수 있어야 한다.
- **AND** `activity_year + state_code + loan_purpose` grain observation을 확인할 수 있어야 한다.
- **AND** EDA가 원천 파일, Bronze table 또는 reliability lifecycle을 변경하지 않았음을 검증할 수 있어야 한다.

#### Scenario: Reproducible validation 확인

- **WHEN** 사용자가 EDA 재현 경로를 확인할 때
- **THEN** focused correctness test와 종료 가능한 Notebook smoke command를 확인할 수 있어야 한다.
- **AND** 실제 HMDA source의 identifier, 실행 시각·환경, row count, activity-year 범위, duration, observation과 limitation을 확인할 수 있어야 한다.
- **AND** actual-source observation은 strict performance 또는 OOM 보장으로 표현되어서는 안 된다.

#### Scenario: Responsibility boundary 확인

- **WHEN** 사용자가 ingestion과 EDA의 schema 책임을 비교할 때
- **THEN** ingestion은 `county_code`를 포함한 7개 required source column의 존재를 검증해야 한다.
- **AND** EDA는 6개 core column의 type compatibility와 descriptive metric만 검증해야 한다.
