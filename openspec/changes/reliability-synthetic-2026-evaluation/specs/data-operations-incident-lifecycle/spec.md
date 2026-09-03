---
type: openspec-spec-driven-tdd-spec
category: spec
title: data-operations-incident-lifecycle
description: 신규 연도(2026) 파티션의 합성 결함에 대한 결정론적 신뢰성 수명주기 평가 계약
tags:
  - "capability:data-operations-incident-lifecycle"
---

## ADDED Requirements

### Requirement: Multi-year partition synthetic evaluation

시스템은 신규 연도(2026년 등) 파티션의 합성 결함 데이터에 대해서도 지정된 기준선(Baseline)과 비교하여 사고 탐지 및 dbt 계통 영향 분석을 격리된 환경에서 결정론적으로 실행할 수 있어야 한다(SHALL).

#### Scenario: 2026 partition null spike evaluation

- **GIVEN** 2026년 파티션에 `income` 결측치가 증가된 가상 합성 데이터가 샌드박스에 적재되어 있을 때
- **WHEN** 2026년 파티션을 대상으로 baseline과 current 프로파일을 비교하는 `run_incident_lifecycle()`을 실행할 때
- **THEN** `null_spike` 사고 유형이 정확히 감지되어야 한다.
- **AND** `stg_hmda_loans` 및 `mart_hmda_loan_outcomes`가 영향받는 하위 자산으로 식별되어야 한다.
- **AND** 메인 데이터베이스 상태는 변경되지 않아야 한다.
