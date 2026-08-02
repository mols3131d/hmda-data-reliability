---
type: openspec-rpi
category: spec
relatedArtifacts:
  - hmda-eda-foundation-extension
title: "Foundation baseline EDA readiness delta"
description: "foundation baseline의 EDA 완료 evidence 범위를 MVP 데이터 정보까지 확장한다."
---

## MODIFIED Requirements

### Requirement: Foundational EDA readiness

다루는 데이터의 기초 EDA는 foundation 완료 전에 수행되어야 한다(SHALL). EDA는 원천 데이터의 schema, 전체 및 주요 partition별 volume, required column null baseline, freshness boundary, MVP reliability 개발에 필요한 핵심 field의 의미·code distribution·numeric summary·suspicious value observation·분석 grain alignment를 read-only evidence로 확인해야 한다(MUST). EDA 결과와 재현 경로는 domain 문서, 실행 가능한 notebook 또는 script, automated test command로 추적 가능해야 한다(MUST).

#### Scenario: HMDA 기초 EDA 완료 확인

- **WHEN** 사용자가 foundation readiness를 검토할 때
- **THEN** HMDA 원천 CSV에 대한 schema, row count, `activity_year`별 row count, required-column null rate, freshness boundary evidence를 확인할 수 있어야 한다.
- **AND** 핵심 field의 code/count/share, `loan_amount`와 `income`의 numeric summary와 suspicious value observation을 확인할 수 있어야 한다.
- **AND** `activity_year + state_code + loan_purpose` grain과 raw → staging → mart alignment evidence를 확인할 수 있어야 한다.
- **AND** EDA는 원천 파일, Bronze table, incident lifecycle을 변경하지 않는 read-only 실행이어야 한다.
- **AND** EDA correctness와 notebook smoke를 검증하는 test 또는 command가 문서에 제공되어야 한다.

#### Scenario: Contract 기준 확인

- **WHEN** 사용자가 foundation EDA contract 범위를 확인할 때
- **THEN** descriptive EDA가 `ProfileSnapshot`, detector, remediation, recovery를 대체하지 않는다는 경계를 확인할 수 있어야 한다.
- **AND** 의미가 확정되지 않은 suspicious value는 raw 보존과 observation flag 방식으로 처리되어야 한다.
