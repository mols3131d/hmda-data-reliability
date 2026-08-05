---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: "HMDA EDA core scope reduction"
description: "HMDA EDA를 Reliability MVP에 필요한 6개 core column의 descriptive profile로 축소한다."
tags:
  - "domain:hmda-data"
  - "subdomain:eda"
  - "capability:hmda-eda-baseline"
  - "capability:foundation-baseline"
  - "scope-reduction"
---

> [!NOTE]
> HMDA EDA를 resource-validation subsystem이 아니라 Gold mart를 설명하는 최소 read-only descriptive profile로 되돌린다. 이 change는 [`research/hmda-eda-scope-reset.md`](../../../research/hmda-eda-scope-reset.md)의 결론을 이전하며 `hmda-eda-foundation-extension`을 대체한다.

## Overview

| Why | What | Capabilities |
| --- | --- | --- |
| Foundation EDA가 fixture·memory·anomaly subsystem까지 확장되어 MVP 진입을 지연한다. | 6개 core column의 schema, volume, null, distribution, numeric summary와 mart grain만 유지한다. | `hmda-eda-baseline`, `foundation-baseline` |

> [!IMPORTANT]
> Replacement change가 생성된 뒤 `hmda-eda-foundation-extension`을 병행 Apply하지 않는다.

## Why

현재 EDA는 descriptive evidence 외에 500만 row fixture, manifest, process memory gate, freshness·Profile mapping과 근거가 확정되지 않은 anomaly rule까지 소유한다. 이 범위는 Reliability MVP가 요구하는 최소 데이터 이해보다 크며 Notebook과 Foundation acceptance를 미완료 상태로 남긴다.

## What Changes

- **Modify:** EDA type validation과 metric 계산 대상을 `activity_year`, `state_code`, `loan_purpose`, `action_taken`, `loan_amount`, `income`으로 축소한다.
- **Modify:** categorical count/share, numeric five-number summary, 전체·연도별 volume, null과 `activity_year + state_code + loan_purpose` grain만 제공한다.
- **Add:** 실제 HMDA source의 1회 read-only observation을 Foundation acceptance evidence로 기록한다.
- **Remove:** unknown-code classification, numeric anomaly rule, freshness, schema hash, `ProfileSnapshot` mapping을 EDA contract에서 제거한다.
- **Remove:** representative fixture, manifest, memory runner, hard-limit gate와 관련 public export·script·test를 제거한다.
- **BREAKING:** `project_pivot.hmda_data.eda`의 fixture·memory helper API는 별도 deprecation 없이 제거한다. `project_pivot.hmda_data.analyze_hmda_csv`는 유지한다.

## Boundaries

| In Scope | Out of Scope |
| --- | --- |
| 6개 core column descriptive profile | County·demographic 분석 |
| Read-only calculation과 connection close | Domain-backed anomaly rule |
| 최소 Notebook과 pytest smoke | Strict performance·OOM 보장 |
| Actual-source 1회 observation | 전체 HMDA field inventory |
| Canonical EDA·Foundation spec 축소 | Incident 생성·자동 정제·row 삭제 |

## Capabilities

### Modified Capabilities

#### `hmda-eda-baseline`

- EDA 입력, evidence와 validation surface를 6개 core column의 descriptive profile로 축소한다.
- `analyze_hmda_csv`의 read-only·failure boundary는 유지하고 resource-validation subsystem은 제거한다.

#### `foundation-baseline`

- Foundation EDA acceptance를 focused tests, 최소 Notebook smoke와 actual-source observation으로 정의한다.
- memory benchmark, freshness, Profile mapping과 anomaly classification을 Foundation 완료 조건에서 제외한다.

## Impact

| Area | Impact |
| --- | --- |
| Code / Systems | `hmda_data/eda/analysis.py` 단순화, fixture·memory module과 script 제거 |
| Data / Contracts | `county_code`는 ingestion required column으로 유지하되 MVP EDA metric에서는 제외 |
| Interfaces / APIs | `analyze_hmda_csv` 유지, fixture·memory export 제거 |
| Operations / Dependencies | 반복 memory gate 제거, actual-source 1회 observation 유지 |

## Appendix

### Trade-offs

| Choice | Gain | Cost |
| --- | --- | --- |
| Internal helper를 즉시 제거 | Foundation 범위와 유지보수 비용 축소 | 직접 import한 repository 내부 caller 수정 필요 |
| Actual-source observation만 유지 | 실제 데이터 근거 보존 | 성능·OOM 안전성 보장은 제공하지 않음 |
