---
type: openspec-rpi
category: research
title: HMDA MVP EDA Scope
description: 현재 HMDA EDA 구현과 문서 계약을 조사하여 reliability MVP에 필요한 최소 컬럼과 validation 범위를 제안한다.
status: completed
tags:
  - hmda
  - eda
  - mvp
  - data-reliability
---

> [!NOTE]
> 현재 EDA 계산 계층은 reliability MVP에 필요한 descriptive evidence를 대부분 구현했다. 문제는 분석 부족보다 계산·Notebook·문서·OpenSpec 사이의 범위 불일치다. MVP는 `activity_year`를 구조 컬럼으로 두고 `state_code`, `loan_purpose`, `action_taken`, `loan_amount`, `income`만 핵심 분석 대상으로 삼는 것이 가장 타당하다. `county_code`와 나머지 HMDA 컬럼은 포트폴리오 공개 이후 별도 iteration으로 확장한다.

## Question

- **Primary:** Project Pivot의 reliability MVP를 설명하고 검증하는 데 필요한 최소 HMDA EDA 범위는 무엇인가?
- **Scope:** `main@1c81aeed6c9305d9b7973c2761e34684fdab3669`의 EDA 계산, Notebook, tests, Gold mart, reference 문서와 활성 OpenSpec change를 조사한다. 실제 source 재실행, 코드 수정, 전체 99개 컬럼 분석과 post-MVP 분석 설계는 제외한다.
- **Stop Condition:** 현재 구현된 evidence, 범위 충돌, MVP에 필요한 컬럼과 최소 validation surface를 판단할 수 있는 근거가 확보되면 종료한다.

> [!CAUTION]
> 최신 `main`에서 tests와 Notebook runtime을 직접 실행한 근거는 없다. 과거 readiness 문서의 `Passing` 표시는 현재 커밋의 검증 결과로 간주하지 않으며, 실행 상태는 후속 validation에서 확인해야 한다.

## Findings

### F1. MVP에 필요한 계산 evidence는 대부분 구현되어 있다

`analyze_hmda_csv()`는 schema, 전체·연도별 volume, required-column null, code distribution, numeric summary, suspicious numeric observation과 mart grain coverage를 반환한다. 원천 파일을 수정하지 않고 connection을 닫으며 `activity_year` grouping cardinality도 제한한다.

- **Evidence** - `src/project_pivot/hmda_data/eda/analysis.py`
- **Implication** - 새로운 EDA engine을 설계할 필요는 없다. 현재 계산 경로를 축소된 MVP 계약에 맞추고 Notebook에 노출하는 작업이 중심이 되어야 한다.

### F2. 현재 Gold mart는 구조 컬럼 하나와 분석 컬럼 다섯 개로 설명된다

Gold mart grain은 `activity_year + state_code + loan_purpose`이며, 결과 metric은 `action_taken`, `loan_amount`, `income`에서 계산된다.

| Role | Column | MVP relevance |
| --- | --- | --- |
| Structural | `activity_year` | partition volume과 mart grain |
| Categorical | `state_code` | mart grain과 지역별 구성 |
| Categorical | `loan_purpose` | mart grain과 대출 목적 구성 |
| Categorical | `action_taken` | approval·denial metric |
| Numeric | `loan_amount` | 평균 대출 금액과 이상값 관찰 |
| Numeric | `income` | 평균 소득과 missingness·이상값 관찰 |

- **Evidence** - `dbt/models/marts/mart_hmda_loan_outcomes.sql`
- **Implication** - MVP EDA의 실질적인 분석 대상은 5개이며 `activity_year`는 구조 확인용이다. 이 범위만으로 raw data와 Gold mart의 핵심 관계를 설명할 수 있다.

### F3. `county_code`의 현재 계약은 일관되지 않는다

계산 코드와 baseline spec은 `county_code`를 required column으로 취급한다. 반면 extension spec에서는 distribution 대상을 optional로 표현하며 Gold mart의 grain이나 metric에는 사용하지 않는다.

- **Evidence** - `src/project_pivot/hmda_data/eda/analysis.py`, `openspec/specs/hmda-eda-baseline/spec.md`, `openspec/changes/hmda-eda-foundation-extension/specs/hmda-eda-foundation/spec.md`
- **Implication** - `county_code`를 MVP required field로 유지하면 mart와 직접 연결되지 않는 분석 비용이 추가된다. 후속 change에서 optional 또는 deferred field로 정리할 근거가 충분하다.

### F4. 계산과 Notebook 사이에 presentation gap이 있다

Notebook은 required schema, volume, null, freshness와 ProfileSnapshot mapping만 표시한다. 계산 계층에 구현된 code distribution, numeric summary, anomaly와 grain evidence는 렌더링하지 않는다.

정적 inspection에서는 `input_path`와 `run_eda`를 정의하는 cell도 확인되지 않았다. 해당 이름을 사용하는 cell은 존재하지만 중간에 빈 cell만 있어 Notebook dependency graph가 불완전할 가능성이 있다.

- **Evidence** - `notebooks/eda_mo.py`
- **Implication** - 현재 EDA는 코드로는 존재하지만 포트폴리오에서 핵심 분석 결과가 보이지 않는다. MVP의 우선 작업은 분석 범위 확대가 아니라 Notebook 실행 경로와 최소 출력 복구다.

### F5. 활성 OpenSpec의 field inventory가 MVP보다 넓다

`hmda-eda-foundation-extension`의 Non-Goal은 전체 99개 field 분석을 제외하지만, design은 기관, 상품, 금리, 담보, 지역 경제와 demographic을 포함한 약 22개 대표 field를 우선 관찰 대상으로 제시한다.

- **Evidence** - `openspec/changes/hmda-eda-foundation-extension/design.md`
- **Implication** - 전수 분석은 아니더라도 구현·해석·시각화 범위가 다시 커진다. reliability MVP보다 일반 HMDA 분석 프로젝트에 가까운 범위이므로 post-MVP roadmap으로 분리하는 편이 적절하다.

### F6. 현재 validation surface는 MVP 완료 조건으로는 무겁다

활성 task는 deterministic fixture, valid·malformed Notebook runtime smoke, representative memory workload, 실제 4.8 GiB source observation, 전체 regression과 문서 연결을 함께 요구한다. 현재 task는 18개 중 7개가 완료된 것으로 기록되어 있다.

- **Evidence** - `openspec/changes/hmda-eda-foundation-extension/tasks.md`, `docs/development/foundation/readiness.md`
- **Implication** - 모든 validation을 Foundation gate로 유지하면 EDA가 전체 MVP 공개를 지연시킨다. 기능 완료에 필요한 검증과 성능·회귀 조사를 분리할 필요가 있다.

### F7. 기존 readiness는 최신 실행 상태를 보장하지 않는다

Readiness 문서는 2026-08-03 snapshot과 수동 progress count를 사용한다. 최신 repository commit에 연결된 GitHub Actions workflow run은 확인되지 않았다.

- **Evidence** - `docs/development/foundation/readiness.md`, GitHub commit workflow 조회
- **Implication** - 구현 존재, 과거 실행 결과와 현재 검증 상태를 별도 신호로 관리해야 한다. 수동 progress 비율만으로 EDA 완료를 판정하면 안 된다.

## Options

| Option | Strengths | Weaknesses |
| --- | --- | --- |
| 현재 extension 범위를 유지한다 | 향후 분석 확장 기반을 한 번에 구축할 수 있다 | 약 22개 field, 여러 runtime·resource gate가 MVP 공개를 지연시킨다 |
| 구조 1개와 분석 5개로 MVP를 축소한다 | 현재 mart와 reliability story에 직접 연결되고 기존 계산을 재사용할 수 있다 | `county_code`와 broader HMDA insight는 후속 작업으로 남는다 |
| EDA를 MVP에서 제외한다 | 가장 빠르게 reliability lifecycle에 집중할 수 있다 | 데이터 이해와 mart metric의 신뢰 근거가 부족해 포트폴리오 설명력이 약해진다 |

## Conclusion

- **Answer** - reliability MVP를 위한 최소 EDA는 `activity_year` 구조 관찰과 `state_code`, `loan_purpose`, `action_taken`, `loan_amount`, `income`의 descriptive analysis다. 99개 전체 컬럼이나 약 22개 대표 field를 Foundation 완료 조건으로 둘 필요는 없다.
- **Recommendation** - 활성 `hmda-eda-foundation-extension`을 새 분석 기능 추가가 아니라 범위 정합화 change로 재구성하는 방향을 권장한다. `county_code`는 optional 또는 post-MVP로 이동하고, 기존 계산 evidence 중 categorical distribution, numeric summary, anomaly와 mart grain만 Notebook에 노출한다.
- **Next Step** - 후속 specification·design 단계에서 MVP column contract, Notebook 출력 범위와 validation gate를 확정한다. 최소 후보 gate는 focused calculation tests, deterministic fixture evidence와 valid Notebook runtime smoke다. malformed runtime, representative memory rerun, full-source rerun과 나머지 컬럼 분석은 post-MVP validation으로 분리한다.

## Evidence

| Evidence | Supports | Location |
| --- | --- | --- |
| EDA status and problem review | 전체 현황과 문제 분류 | `docs/development/eda-status-and-problems.md` 또는 세션 artifact `project-pivot-eda-status-and-problems.md` |
| Canonical EDA calculation | F1, F3 | `src/project_pivot/hmda_data/eda/analysis.py` |
| EDA component tests | F1, F6 | `tests/hmda_data/eda/test_eda.py` |
| Notebook runtime test design | F4, F6 | `tests/hmda_data/eda/test_eda_notebook.py` |
| Marimo Notebook | F4 | `notebooks/eda_mo.py` |
| Gold mart contract | F2, F3 | `dbt/models/marts/mart_hmda_loan_outcomes.sql` |
| Baseline EDA specification | F3 | `openspec/specs/hmda-eda-baseline/spec.md` |
| EDA extension specification | F3, F6 | `openspec/changes/hmda-eda-foundation-extension/specs/hmda-eda-foundation/spec.md` |
| EDA extension design | F5 | `openspec/changes/hmda-eda-foundation-extension/design.md` |
| EDA extension tasks | F6 | `openspec/changes/hmda-eda-foundation-extension/tasks.md` |
| EDA reference | F4, F6 | `docs/references/hmda_eda.md` |
| Foundation readiness snapshot | F6, F7 | `docs/development/foundation/readiness.md` |

## Open Questions

| Question | Why It Matters | Next Step |
| --- | --- | --- |
| `county_code`를 baseline schema에서도 optional로 바꿀 것인가? | 현재 baseline spec과 extension spec의 계약 충돌을 해소해야 한다 | Gold mart와 immediate portfolio use case를 기준으로 후속 requirement에서 결정한다 |
| Notebook runtime smoke를 pytest로 둘 것인가, 전용 command로 둘 것인가? | MVP gate의 재현성과 실행 비용이 달라진다 | 현재 Marimo export·run 방식 중 종료 가능하고 결과를 검사할 수 있는 최소 경로를 검증한다 |
| 기존 full-source observation을 다시 실행해야 하는가? | scope 변경 뒤 실제 데이터 evidence의 최신성을 결정한다 | MVP 기능 검증과 분리하여 공개 직전 한 번만 실행할지 판단한다 |
