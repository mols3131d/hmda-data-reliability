# HMDA EDA Status and Scope Review

> **Repository:** `mols3131d/project-pivot`  
> **Baseline:** `main@1c81aeed6c9305d9b7973c2761e34684fdab3669`  
> **Proposed location:** `docs/development/eda-status-and-problems.md`

## Summary

현재 EDA는 실패한 상태가 아니다. **공유 계산 계층은 MVP에 필요한 descriptive evidence를 대부분 구현했지만, Notebook·문서·OpenSpec이 이를 따라가지 못하고 범위도 다시 확장된 상태**다.

MVP에서는 `activity_year`를 구조 컬럼으로 두고 다음 5개 분석 컬럼만 다룬다.

- `state_code`
- `loan_purpose`
- `action_taken`
- `loan_amount`
- `income`

`county_code`와 나머지 HMDA 컬럼은 포트폴리오 공개 이후 별도 iteration으로 확장한다.

## Current State

### Calculation

`src/project_pivot/hmda_data/eda/analysis.py`의 `analyze_hmda_csv()`는 이미 다음 evidence를 생성한다.

| Evidence | Current behavior |
| --- | --- |
| Schema | 전체 inferred schema와 required-column type 검증 |
| Volume | 전체 row count와 `activity_year`별 row count |
| Missingness | required-column null count와 rate |
| Distributions | `action_taken`, `loan_purpose`, `state_code`, `county_code` count/share |
| Numeric summary | `loan_amount`, `income`의 min, p25, median, p75, max |
| Anomaly observation | `income < 0`, `loan_amount <= 0` count/share |
| Mart alignment | `activity_year + state_code + loan_purpose` grain coverage |
| Resource boundary | read-only 실행, connection close, bounded year grouping |

따라서 **MVP EDA의 핵심 계산은 거의 구현되어 있다.**

### Tests

`tests/hmda_data/eda/test_eda.py`에는 distribution, numeric summary, anomaly, grain, missing-column failure와 connection lifecycle 검증이 존재한다.

다만 다음은 완료되지 않았다.

- 공용 deterministic fixture에 모든 exact expected value를 고정하는 작업
- Notebook valid/malformed runtime smoke
- 최신 `main`에서의 전체 검증 실행 근거

GitHub Actions workflow run도 현재 커밋에서 확인되지 않았다. 과거 dashboard의 `Passing` 표시는 최신 실행 결과로 간주하지 않는다.

### Notebook

`notebooks/eda_mo.py`는 현재 다음만 표시한다.

- Required schema
- Volume baseline
- Required-column null baseline
- Freshness boundary
- Profile evidence mapping

계산 계층에 추가된 distribution, numeric summary, anomaly, grain은 아직 화면에 표시하지 않는다.

또한 source inspection 기준으로 `input_path`와 `run_eda`를 정의하는 cell이 없고 빈 cell만 존재한다. 따라서 **Notebook dependency graph가 불완전할 가능성이 높으며 실제 runtime 검증이 필요하다.**

### Documentation and OpenSpec

`docs/references/hmda_eda.md`는 기존 schema·volume·null·freshness 중심으로 작성되어 새 evidence key를 반영하지 못했다. Notebook을 일반 Marimo script가 아니라고 설명하지만 실제 파일은 `marimo.App`과 `app.run()`을 사용하는 Python notebook script이므로 설명도 충돌한다.

활성 change `hmda-eda-foundation-extension`은 18개 task 중 7개만 완료되었다. 특히 design에는 20개가 넘는 대표 field inventory가 포함되어 있어, “전체 99개 field는 분석하지 않는다”는 Non-Goal과 별개로 MVP 범위를 다시 크게 만든다.

## Problems

### Scope drift

MVP의 목적은 HMDA 전체를 이해하는 것이 아니라 reliability lifecycle에 필요한 데이터 계약과 이상 사례를 설명하는 것이다. 그러나 design은 기관, 가격, 담보 비율, 지역 경제, 인구 구성, 인종·민족·성별·연령까지 범위를 확장한다.

이 범위는 분석 프로젝트에는 적절할 수 있지만 현재 reliability MVP의 완료 조건으로 두면 안 된다.

### Contract inconsistency

현재 범위 정의가 서로 다르다.

| Surface | Column scope |
| --- | --- |
| Calculation required schema | 7개, `county_code` 포함 |
| Distribution spec | `county_code` optional |
| Gold mart | `activity_year`, `state_code`, `loan_purpose`, `action_taken`, `loan_amount`, `income` |
| Current MVP decision | 구조 1개 + 분석 5개 |
| Design field inventory | 약 22개 |

`county_code`가 required인지 optional인지부터 일치하지 않는다.

### Implementation and presentation gap

공유 계산은 이미 확장되었지만 Notebook과 reference 문서는 과거 baseline에 머물러 있다. 사용자는 코드 내부 evidence가 아니라 Notebook과 README를 통해 결과를 보므로, 현재 상태는 **구현은 있으나 포트폴리오에서 보이지 않는 상태**다.

### Validation overreach

대표 500만 row workload, hard memory limit, 세 번 반복, malformed Notebook smoke, 실제 4.8 GiB source observation을 모두 Foundation 완료 gate로 두면 EDA가 프로젝트 전체 공개를 지연시킨다.

Resource validation은 가치가 있지만 MVP 공개의 핵심 경로와 분리해야 한다. 기존 full-source observation의 peak RSS도 약 12.4 GiB로 기록되어 있으므로 별도 성능 조사 대상이지, EDA 기능 완료와 같은 gate로 묶을 문제가 아니다.

### Stale readiness evidence

`docs/development/foundation/readiness.md`는 2026-08-03 snapshot이며 수동 progress count를 사용한다. 최신 커밋에서 자동 검증된 상태를 나타내지 않는다. 현재 판단에는 task 상태와 실제 실행 근거를 분리해야 한다.

## MVP Decision

### Included

| Type | Columns | Minimum evidence |
| --- | --- | --- |
| Structural | `activity_year` | 연도별 volume, grain participation |
| Categorical | `state_code` | count, share, null |
| Categorical | `loan_purpose` | count, share, null |
| Categorical | `action_taken` | count, share, null |
| Numeric | `loan_amount` | null, five-number summary, nonpositive count |
| Numeric | `income` | null, five-number summary, negative count |

### Deferred

- `county_code`
- 기관·상품 세부 컬럼
- 금리·가격·담보 비율
- census·지역 경제
- demographic·fairness 분석
- 99개 전체 컬럼 inventory와 자동 profile
- 추가 suspicious rule과 domain interpretation

## Recommended Change

새 change를 추가하기보다 아직 활성 상태인 `hmda-eda-foundation-extension`을 축소한다.

1. `REQUIRED_EDA_COLUMNS`에서 `county_code`를 제거하거나 optional로 분리한다.
1. Design의 22개 field inventory를 post-MVP roadmap으로 이동한다.
1. Notebook의 누락된 input/run cell을 복구한다.
1. Notebook에 categorical, numeric, anomaly, grain 네 영역만 렌더링한다.
1. Reference 문서를 실제 evidence schema와 실행 방식에 맞게 갱신한다.
1. Valid fixture runtime smoke 한 개만 MVP gate로 둔다.
1. Malformed Notebook smoke, representative memory rerun, full-source rerun은 post-MVP validation으로 이동한다.
1. Readiness는 수동 test count 대신 완료 조건과 최신 실행 날짜만 기록한다.

## Completion Criteria

다음을 충족하면 MVP EDA를 완료로 판정한다.

- 6개 대상 컬럼의 schema, volume, null evidence가 생성된다.
- 범주형 3개와 수치형 2개의 최소 descriptive evidence가 생성된다.
- 현재 Gold mart grain coverage를 확인할 수 있다.
- Notebook이 valid fixture로 종료 가능하게 실행되고 모든 MVP 영역을 표시한다.
- 계산 계층의 focused tests가 통과한다.
- Notebook, reference 문서와 OpenSpec의 컬럼 범위가 일치한다.
- 나머지 HMDA 컬럼이 post-MVP roadmap으로 명시된다.

## Evidence

- `src/project_pivot/hmda_data/eda/analysis.py`
- `notebooks/eda_mo.py`
- `tests/hmda_data/eda/test_eda.py`
- `tests/hmda_data/eda/test_eda_notebook.py`
- `docs/references/hmda_eda.md`
- `docs/development/foundation/readiness.md`
- `openspec/specs/hmda-eda-baseline/spec.md`
- `openspec/changes/hmda-eda-foundation-extension/design.md`
- `openspec/changes/hmda-eda-foundation-extension/tasks.md`
- `openspec/changes/hmda-eda-foundation-extension/specs/hmda-eda-foundation/spec.md`
- `dbt/models/marts/mart_hmda_loan_outcomes.sql`
