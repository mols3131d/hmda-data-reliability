---
type: openspec-rpi
category: proposal
relatedArtifacts:
  - hmda-eda-foundation-extension
title: "HMDA foundation EDA extension"
description: "MVP reliability 개발에 필요한 HMDA 데이터 정보와 descriptive EDA evidence를 확장한다."
---

> [!CAUTION]
> **Superseded by `hmda-eda-baseline-reduce-core-scope`.** 이 change를 추가 Apply하지 않는다. 이미 구현된 내용은 replacement planning의 현재 상태 근거로만 사용한다.

## Why

현재 HMDA EDA는 schema, volume, required-column null, freshness boundary를 확인하지만 MVP reliability 기능이 의존하는 row semantics, code distribution, numeric anomaly, analysis grain과 downstream alignment를 충분히 고정하지 않는다. Foundation에서 MVP 개발을 안전하게 시작하려면 데이터의 의미와 품질 경계를 먼저 재현 가능한 evidence로 남겨야 한다.

## What Changes

- HMDA 핵심 field 중심의 descriptive EDA capability를 추가한다.
- `action_taken`, `loan_purpose`, `state_code`, `loan_amount`, `income`의 code/count/share와 numeric summary를 제공한다.
- `activity_year + state_code + loan_purpose` grain과 raw → staging → mart 관계를 확인한다.
- null coverage, suspicious value와 unknown code를 관찰하되 raw 값을 자동 정제하거나 삭제하지 않는다.
- deterministic fixture, representative resource check, actual-source observation, notebook runtime smoke를 구분한다.
- EDA analysis, fixture, resource helper를 `project_pivot.hmda_data.eda` subpackage가 소유하도록 정리한다.
- foundation readiness가 MVP 개발에 필요한 EDA evidence를 포함하도록 기준을 보강한다.

## Capabilities

### New Capabilities

- `hmda-eda-foundation`: HMDA 핵심 field의 descriptive EDA, anomaly observation, grain alignment과 재현성 검증을 정의한다.

### Modified Capabilities

- `foundation-baseline`: foundation 완료 evidence에 MVP 데이터 정보와 descriptive EDA readiness를 포함한다.

## Impact

- `src/project_pivot/hmda_data/eda/` subpackage의 analysis, fixture, resource helper
- `notebooks/eda_mo.py`와 EDA reference 문서
- `tests/hmda_data/`의 fixture, correctness, notebook smoke test
- foundation readiness와 domain contract 문서
- 기존 `ProfileSnapshot`, detector, remediation, recovery API의 책임 경계는 유지
- 새로운 runtime dependency나 외부 service는 추가하지 않음
