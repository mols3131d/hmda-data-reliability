---
type: openspec-rpi
title: "HMDA foundation EDA extension"
description: "기초 구조 EDA를 HMDA 도메인 이해와 MVP 데이터 정보 baseline으로 확장할 범위를 조사한다."
category: research
status: completed
relatedArtifacts: []
---

# Research: HMDA Foundation EDA Extension

> **결론:** 다음 작업으로 EDA 확장은 타당하다. 범위는 전체 99개 field가 아니라, MVP reliability 기능이 의존하는 핵심 field의 의미·grain·분포·결측·이상값·재현성으로 제한한다.

## Question

Foundation에서 MVP를 개발하기 전에 HMDA 데이터에 대해 어떤 정보를 EDA로 확인해야 하며, 어디까지 확인하면 충분한가?

## Decision Summary

| Decision | Result |
| --- | --- |
| EDA 목적 | 데이터를 많이 요약하는 것이 아니라 MVP의 데이터 가정을 검증하는 foundation evidence 제공 |
| 필수 관점 | row semantics, population, grain, code distribution, numeric range, missingness, downstream alignment, reproducibility |
| 핵심 field | `activity_year`, `state_code`, `county_code`, `loan_purpose`, `action_taken`, `loan_amount`, `income` |
| 책임 경계 | descriptive EDA는 `ProfileSnapshot`, detector, remediation, recovery를 대체하지 않음 |
| anomaly 처리 | 의미가 확정되지 않은 값은 삭제·정제하지 않고 `observed anomaly`로 기록 |
| 다음 단계 | 이 Research를 근거로 bounded OpenSpec change를 제안할 수 있음 |

상세한 MVP 질문과 EDA 범위는 [MVP Data Information Needs](mvp-data-information-needs.md)에 정리한다.

## Scope

| Included | Excluded |
| --- | --- |
| 현재 EDA contract와 구현·테스트 근거 검토 | 전체 99개 field의 포괄적 분석 |
| 실제 `year_2025.csv`의 핵심 field 관찰 | detector용 `ProfileSnapshot` API 재설계 |
| MVP capability별 필요한 data question 정의 | ML feature engineering, fairness, causal analysis |
| foundation EDA와 reliability profiling의 경계 정의 | production monitoring, recovery 실행, dashboard UI |

## Current Evidence

| Finding | Evidence | Class |
| --- | --- | --- |
| 현재 EDA는 schema, 전체·`activity_year` volume, required-column null, freshness boundary를 계산한다. | `src/project_pivot/hmda_data/eda.py`, `docs/references/hmda_eda.md` | Authoritative |
| EDA correctness와 fixture invariant test는 통과한다. | `uv run pytest tests/hmda_data/test_eda.py tests/hmda_data/test_eda_fixture.py tests/hmda_data/test_eda_memory_helpers.py -n 0 -q` → 26 passed | Observed |
| Notebook 구조 검사는 통과하지만 실제 runtime smoke test evidence는 부족하다. | `uv run marimo check notebooks/eda_mo.py` → exit 0; notebook 실행 test 미확인 | Observed |
| 실제 source는 99개 column이며 required field는 모두 존재한다. `observed_at`은 없다. | `data/raw/hmda/year_2025.csv` runtime scan, 2026-08-02 | Observed |
| `action_taken`은 1~8 code가 모두 관찰되고, `loan_purpose`는 1, 2, 4, 5, 31, 32가 관찰된다. | 실제 source runtime scan | Observed |
| 핵심 수치값에는 별도 의미 검토가 필요한 anomaly가 있다. | `income < 0` 8,085건, `loan_amount` max `999,000,005,000` | Observed |
| descriptive EDA와 detector profile은 별도 capability로 유지해야 한다. | `openspec/specs/profile-snapshots/spec.md`, `src/project_pivot/reliability/profiling/` | Authoritative |

## MVP Relevance

| MVP capability | EDA가 확인할 정보 |
| --- | --- |
| Profile snapshot | row count, null baseline, schema, freshness boundary, partition 후보 |
| Basic detection | volume 기준, null 대상 field, schema drift 대상, freshness 가능 여부 |
| Impact analysis | raw → staging → mart asset와 grain 관계 |
| Remediation draft | anomaly 유형과 영향을 받는 field/partition의 설명 근거 |
| Recovery validation | backfill 대상 partition과 row-count 비교 기준 |
| Evaluation | synthetic case가 재현해야 할 정상·이상 조건 |

## Risks And Open Decisions

- `income < 0`과 extreme `loan_amount`는 현재 오류로 단정하지 않고 `observed anomaly`로 유지한다.
- approval/denial grouping은 현재 dbt mart의 aggregation rule과 일치시킨다.
- 실제 source 전체 결과는 immutable test fixture가 아니라 observation evidence로 취급한다.
- notebook runtime smoke를 pytest 기반 test로 둘지 별도 command로 둘지는 OpenSpec design에서 결정한다.

## Handoff

| Field | Content |
| --- | --- |
| Problem | 현재 EDA는 구조 baseline은 제공하지만 MVP 데이터 의미와 분포를 충분히 고정하지 않는다. |
| Proposed scope | 핵심 field의 semantics, population, grain, code/count/share, numeric summary, missingness, anomaly observation, notebook smoke |
| Validation | deterministic fixture, representative resource check, actual-source observation, notebook runtime smoke |
| Boundary | raw 값 자동 삭제·정제, detector 실행, recovery 실행, ML/fairness 분석은 제외 |
| Next action | 이 Research를 근거로 `hmda-eda-foundation-extension` OpenSpec proposal 작성 |
