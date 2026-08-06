# HMDA EDA Deep Review

> **Verdict:** Changes requested — 현재 EDA는 실행 가능한 분석 유틸리티의 형태는 갖췄지만, 계약·증거·Notebook·readiness가 서로 일치하지 않아 Foundation 완료 근거로 사용할 수 없다.

## Review Metadata

| Field | Value |
| --- | --- |
| Repository | `mols3131d/project-pivot` |
| Baseline | `main` @ `f08c2fb7a71aecd6659b77dcab5d0026e5d9ee93` |
| Related delivery | PR #18, `hmda-eda-baseline-reduce-core-scope` |
| Review date | 2026-08-06 (Asia/Seoul) |
| Method | Static repository review |
| Execution status | Tests, Notebook, actual-source analysis were not rerun |

## Executive Assessment

EDA의 핵심 문제는 개별 함수의 구현 결함보다 **신뢰 체계가 분리된 것**이다.

```mermaid
flowchart LR
    A[Canonical OpenSpec<br/>기존 광범위 계약]
    B[Active Change<br/>6-core 축소 계약]
    C[Runtime + Tests<br/>7-column 혼합 계약]
    D[Notebook<br/>일부 결과만 렌더링]
    E[Evidence MD / JSON<br/>서로 다른 수치]
    F[Readiness<br/>완료로 표시]

    A -. 불일치 .-> B
    B -. 미반영 .-> C
    C -. 누락 .-> D
    D -. 검증 공백 .-> E
    E -. 근거 불충분 .-> F
```

| Dimension | Assessment |
| --- | --- |
| Runtime structure | 보통 |
| Contract consistency | 낮음 |
| Test assurance | 낮음 |
| Actual-source evidence | 신뢰 불가 |
| Notebook completeness | 미완료 |
| Foundation readiness | 차단 필요 |

현재 데이터셋에서는 EDA가 동작할 수 있다. 그러나 다른 적법한 입력에 대한 계약, 결과 재현성, 증거 일관성은 보장되지 않는다. 따라서 **Foundation gate를 닫을 수 있는 상태가 아니다.**

---

## Scope

검토 대상은 다음 관계를 포함한다.

- OpenSpec의 canonical spec과 scope-reduction change
- `src/project_pivot/hmda_data/eda/`
- `tests/hmda_data/eda/`
- `notebooks/eda_mo.py`
- `docs/references/hmda_eda*`
- Foundation readiness 문서
- HMDA domain grain 계약
- PR #18의 완료 주장

Foundation 문서는 canonical policy가 아닌 active design draft로 취급했다. 다만 변경 작업이 해당 문서의 정렬을 완료했다고 주장하므로, 실제 불일치는 delivery defect로 평가했다.

---

## Contract Map

| Layer | Effective contract |
| --- | --- |
| Canonical spec | `county_code`, freshness, anomaly/outlier, resource tracking을 포함한 기존 범위 |
| Active change | 정확히 6개 core column, freshness/outlier/resource-heavy 제거 |
| Runtime | `county_code`를 포함한 7개 required column |
| Unit tests | 7-column fixture를 정상 입력으로 고정 |
| Notebook | schema/null과 raw JSON 중심; retained section의 명시적 렌더링 누락 |
| Evidence | Markdown과 JSON의 핵심 지표가 상충 |
| Readiness | YAML은 EDA gate 통과, Markdown은 EDA gate를 표시하지 않음 |

이 상태에서는 “어느 계약을 통과했는가?”에 단일 답을 줄 수 없다.

---

# Findings

## 🔴 F-01 — Actual-source evidence가 내부적으로 모순된다

**Severity:** Blocker  
**Type:** Evidence integrity

동일한 EDA baseline을 설명하는 두 artifact가 핵심 수치에서 일치하지 않는다.

| Metric | Markdown | JSON | Difference |
| --- | ---: | ---: | ---: |
| `income` null count | 647,212 | 2,189,834 | 1,542,622 |
| `income` null ratio | 4.78% | 16.17% | 11.39%p |
| Business-grain distinct groups | 335 | 327 | 8 |

**Evidence**

- `docs/references/hmda_eda.md`
- `docs/references/hmda_eda_reference.json`

**Impact**

- 실제 source baseline을 재현할 수 없다.
- null profile과 business grain에 기반한 후속 판단이 서로 달라진다.
- readiness와 Foundation 완료 주장의 근거가 무효화된다.

**Required correction**

1. 동일 source, 동일 revision, 동일 실행에서 JSON을 다시 생성한다.
1. Markdown summary를 JSON에서 기계적으로 파생하거나 invariants로 대조한다.
1. 생성 시점, source fingerprint, code revision을 evidence에 기록한다.
1. 불일치가 해소될 때까지 EDA readiness를 false로 둔다.

---

## 🔴 F-02 — Canonical spec, active change, runtime이 서로 다른 계약을 유지한다

**Severity:** Blocker  
**Type:** Governance / contract drift

Scope-reduction change는 EDA 입력 계약을 정확히 6개 core column으로 축소한다. 그러나 현재 canonical spec은 이전 광범위 범위를 유지하고 runtime은 `county_code`를 여전히 required로 취급한다.

**Evidence**

- `openspec/specs/hmda-eda-baseline/spec.md`
- `openspec/changes/hmda-eda-baseline-reduce-core-scope/specs/hmda-eda-baseline/spec.md`
- `src/project_pivot/hmda_data/eda/analysis.py`
  - `REQUIRED_EDA_COLUMNS`
  - `EXPECTED_REQUIRED_TYPES`
  - `NULL_BASELINE_COLUMNS`

**Impact**

- 구현이 change를 완료했는지 판정할 수 없다.
- `county_code`가 없는 6-core 적법 입력이 거부된다.
- 후속 개발자가 canonical spec만 읽으면 이미 제거하기로 한 기능을 다시 구현할 수 있다.

**Required correction**

6-core 계약을 authoritative contract로 확정한다면 다음을 하나의 delivery에서 정렬해야 한다.

- runtime constants와 validation
- unit-test fixtures와 compatibility tests
- Notebook 설명과 출력
- actual-source evidence
- canonical spec 반영 및 change lifecycle 정리

---

## 🟠 F-03 — Notebook이 retained EDA sections를 명시적으로 렌더링하지 않는다

**Severity:** Major  
**Type:** Product completeness

변경 계약은 다음 retained evidence의 Notebook 표현을 요구한다.

- categorical distributions
- numeric summaries
- business-grain evidence

현재 Notebook은 schema/null table과 raw result JSON을 제공하지만, 위 결과를 사람이 바로 검토할 수 있는 독립 section으로 렌더링하지 않는다.

**Evidence**

- `notebooks/eda_mo.py`
- `openspec/changes/hmda-eda-baseline-reduce-core-scope/design.md`
- `openspec/changes/hmda-eda-baseline-reduce-core-scope/tasks.md`

**Impact**

- Notebook의 목적이 “결과 객체 확인”으로 축소된다.
- 분포·수치·grain 판단을 위해 raw JSON을 직접 해석해야 한다.
- 완료된 task와 실제 사용자 경험이 일치하지 않는다.

**Required correction**

각 retained output에 대해 제목, 표 또는 간결한 chart, empty-state를 독립적으로 제공한다. Raw JSON은 diagnostics로만 남긴다.

---

## 🟠 F-04 — Notebook test가 semantic completeness를 검증하지 않아 false green을 허용한다

**Severity:** Major  
**Type:** Test assurance

Notebook test는 HTML 생성과 runtime error 부재만 확인한다. 따라서 distribution, numeric summary, grain section이 전혀 없어도 통과할 수 있다.

**Evidence**

- `tests/hmda_data/eda/test_eda_notebook.py`
- `notebooks/eda_mo.py`

**Impact**

- 변경 계약의 가장 중요한 사용자-facing 요구가 자동 검증되지 않는다.
- 현재 누락 상태가 이미 test suite에서 탐지되지 않았다.

**Required correction**

HTML 또는 Notebook output에서 다음 semantic marker를 검증한다.

- categorical distribution section
- numeric summary section
- business grain section
- valid-source success state
- invalid-source error state

Notebook 파일이 없으면 skip하지 말고 실패시키는 것이 계약 검증에 적합하다.

---

## 🟠 F-05 — `duration_seconds`가 전체 EDA 실행 시간을 나타내지 않는다

**Severity:** Major  
**Type:** Metric correctness

타이머는 main metric query 직전에 시작하고 직후 종료된다. 이후 수행되는 categorical distribution, numeric summary, grain query 시간은 제외된다.

**Evidence**

- `src/project_pivot/hmda_data/eda/analysis.py`
  - `started_at`
  - `duration_seconds`
  - 후속 distribution/numeric/grain queries

**Impact**

- 사용자는 반환된 duration을 전체 EDA 비용으로 오해할 수 있다.
- 대용량 CSV에서 가장 비싼 후속 scan이 측정에서 빠진다.
- 성능 회귀 또는 resource 판단에 사용할 수 없다.

**Required correction**

둘 중 하나를 선택한다.

- 전체 함수 종료 시점까지 측정해 `duration_seconds`를 유지
- 현재 범위가 의도라면 `baseline_query_duration_seconds`처럼 의미를 제한

---

## 🟠 F-06 — Readiness 표현이 서로 다르며 EDA gate가 조기에 통과했다

**Severity:** Major  
**Type:** Release readiness

`readiness.yml`은 EDA 관련 gate들을 true로 표시한다. 반면 `readiness.md`는 해당 gate들을 표에 노출하지 않으며 전체 readiness를 완료로 표현한다.

**Evidence**

- `docs/development/foundation/readiness.yml`
- `docs/development/foundation/readiness.md`

**Impact**

- 기계 판독 source와 인간용 summary가 다른 readiness를 전달한다.
- evidence 불일치와 Notebook 누락이 있는 상태에서도 Foundation이 완료로 보인다.

**Required correction**

readiness의 authoritative source를 하나로 정하고 human summary를 생성한다. F-01부터 F-04가 해결되기 전에는 다음 gate를 false 또는 blocked로 둔다.

- EDA Quality Baseline
- Domain Observation
- Notebook Runtime

---

## 🟠 F-07 — Complete-key business grain 계약이 구현·테스트로 보호되지 않는다

**Severity:** Major  
**Type:** Data semantics

설계는 `activity_year × state_code × loan_purpose`의 complete-key distinct count를 요구한다. 현재 query에는 key null row를 명시적으로 제외하는 조건이 없고, null key fixture도 없다.

**Evidence**

- `docs/domains/hmda-data.md`
- `openspec/changes/hmda-eda-baseline-reduce-core-scope/design.md`
- `src/project_pivot/hmda_data/eda/analysis.py`
- `tests/hmda_data/eda/test_eda.py`

**Impact**

- missing key가 있는 source에서 grain count 의미가 불명확해진다.
- domain grain collapse 또는 key-quality 문제를 잘못 해석할 수 있다.

**Required correction**

- complete-key predicate를 query에 명시한다.
- 일부 또는 전체 grain key가 null인 fixture를 추가한다.
- total rows, complete-key rows, distinct complete-key groups의 관계를 검증한다.

---

## 🟡 F-08 — 제거된 freshness 계산이 query에 잔존한다

**Severity:** Minor  
**Type:** Dead behavior

`observed_at`이 존재하면 `MAX(observed_at)`을 계산하지만 반환 결과나 retained evidence에는 사용하지 않는다.

**Evidence**

- `src/project_pivot/hmda_data/eda/analysis.py`
  - `metric_select`
  - `freshness_value`

**Impact**

- 제거된 계약이 runtime에 흔적으로 남아 의도를 흐린다.
- 불필요한 aggregation과 유지보수 비용이 발생한다.

**Required correction**

freshness가 scope에서 제거되었다면 query에서도 제거한다. 향후 기능을 위한 placeholder라면 현재 runtime이 아니라 별도 change에서 도입한다.

---

## 🟡 F-09 — EDA가 동일 CSV를 여러 번 scan하며 측정은 이를 숨긴다

**Severity:** Minor  
**Type:** Performance risk

현재 구조는 main metrics, categorical distributions, numeric summaries, grain evidence를 별도 query로 실행한다. CSV-backed view에서는 반복 scan 가능성이 높다.

**Evidence**

- `src/project_pivot/hmda_data/eda/analysis.py`

**Impact**

- 1,300만 행 수준 source에서 Notebook 반응성이 악화될 수 있다.
- F-05의 timing 범위 때문에 비용이 보고되지 않는다.

**Recommendation**

MVP 단계에서 즉시 복잡한 최적화를 도입할 필요는 없다. 먼저 전체 duration과 query별 duration을 정확히 측정하고, 실제 병목이 확인되면 temporary materialization 또는 aggregate consolidation을 검토한다.

---

## 🟡 F-10 — Notebook 실행 기본값과 전역 side effect가 탐색 안정성을 낮춘다

**Severity:** Minor  
**Type:** Operational safety

Notebook은 실행 제어가 활성화된 상태로 시작할 수 있고 repository root로 `chdir`한다.

**Evidence**

- `notebooks/eda_mo.py`

**Impact**

- 환경 변수에 full source가 연결된 경우 열기만 해도 고비용 scan이 시작될 수 있다.
- process-wide working directory 변경이 다른 cell 또는 library 동작에 영향을 준다.

**Recommendation**

- 기본은 명시적 Run action 또는 sample mode로 둔다.
- path는 절대 경로로 전달하고 `chdir` 의존을 제거한다.
- full-source 실행은 예상 비용과 source를 UI에 표시한다.

---

## 🟡 F-11 — Evidence JSON에 로컬 절대 경로가 남아 있다

**Severity:** Minor  
**Type:** Reproducibility / portability

JSON은 `/home/mols/...` 및 `/tmp/...` 형태의 환경 종속 경로를 포함한다.

**Evidence**

- `docs/references/hmda_eda_reference.json`

**Impact**

- 다른 환경에서 source identity를 재구성할 수 없다.
- evidence diff에 의미 없는 환경 noise가 포함된다.

**Recommendation**

repository-relative logical source ID, source filename, fingerprint를 보존하고 machine-specific absolute path는 제거하거나 별도 non-canonical runtime log로 분리한다.

---

## 🟡 F-12 — Delivery 상태 메타데이터가 완료 주장과 모순된다

**Severity:** Minor  
**Type:** Traceability

`tasks.md` 본문의 모든 task는 완료 표시지만 frontmatter progress는 `0/21`이다. PR #18의 설명도 “six core columns”라고 하면서 `county_code`를 포함한 7개를 나열한다.

**Evidence**

- `openspec/changes/hmda-eda-baseline-reduce-core-scope/tasks.md`
- PR #18

**Impact**

- 자동화와 인간이 서로 다른 완료 상태를 읽는다.
- 핵심 scope를 delivery 설명만으로 판정하기 어렵다.

**Required correction**

progress metadata를 실제 checklist와 동기화하고, PR description의 column count와 목록을 authoritative contract에 맞춘다.

---

# Test Gap Matrix

| Contract | Current coverage | Gap |
| --- | --- | --- |
| Exactly six required columns | 7-column valid fixture | `county_code` 없는 성공 case |
| Missing required column | 일부 실패 case | 6개 각각의 contract mapping |
| Type compatibility | 기본 fixture 중심 | accepted/rejected type matrix |
| Categorical distribution | 일부 payload assertion | Notebook rendering |
| Numeric summary | 일부 값 확인 | null-only/edge numeric behavior |
| Complete-key grain | 정상 key fixture | null-key exclusion |
| Removed outputs | 일부 absence assertion | stale query behavior |
| Notebook validity | no runtime error | semantic sections |
| Actual-source evidence | artifact 존재 | MD↔JSON invariants |
| Readiness | 수동 true | evidence-linked gate |

---

# Remediation Sequence

## Phase 0 — Freeze the gate

- EDA 관련 readiness를 `blocked` 또는 false로 전환한다.
- 현재 Markdown/JSON evidence를 “invalidated”로 명시한다.
- Foundation 완료 판정에 이 evidence를 사용하지 않는다.

## Phase 1 — Reconcile the contract

- authoritative EDA scope를 6-core로 확정한다.
- runtime, unit tests, Notebook, docs를 같은 change에 맞춘다.
- canonical spec을 반영하고 active change lifecycle을 정리한다.

## Phase 2 — Restore test confidence

필수 regression tests:

1. `county_code` 없이 성공
1. six core 중 하나라도 없으면 실패
1. 각 core column의 accepted/rejected type
1. null grain keys가 distinct grain에서 제외됨
1. Notebook이 retained 3개 section을 렌더링
1. Notebook source invalidity가 명시적 error state로 표시됨

## Phase 3 — Regenerate evidence

한 번의 controlled run에서 다음을 생성한다.

- machine-readable JSON
- JSON-derived Markdown summary
- source fingerprint
- repository revision
- execution timestamp
- total duration

생성 후 invariants를 검증한다.

```text
markdown.income_null_count == json.income.null_count
markdown.grain_distinct_count == json.business_grain.distinct_count
sum(distribution.count) == row_count
null_count + non_null_count == row_count
```

## Phase 4 — Reopen readiness

- targeted EDA tests
- Notebook render test
- full test suite
- static checks required by repository
- strict OpenSpec validation
- actual-source rerun
- Markdown↔JSON invariant check

각 결과는 실행 command, revision, outcome을 남긴다. 검증하지 못한 항목은 gate에서 분리해 명시한다.

---

# Completion Gate

EDA는 다음 조건을 모두 만족할 때만 Foundation-ready로 간주할 수 있다.

- [ ] canonical spec과 runtime required columns가 일치한다.
- [ ] `county_code` 없는 6-core input regression test가 통과한다.
- [ ] Notebook이 retained evidence를 사람이 검토 가능한 형태로 렌더링한다.
- [ ] Notebook test가 section 존재를 검증한다.
- [ ] complete-key grain semantics가 query와 test에 명시된다.
- [ ] duration metric의 범위가 이름과 일치한다.
- [ ] Markdown과 JSON actual-source evidence가 동일하다.
- [ ] readiness YAML과 Markdown이 동일한 gate 상태를 표현한다.
- [ ] OpenSpec change lifecycle과 progress metadata가 정리된다.
- [ ] 실행한 검증과 미실행 검증이 구분되어 기록된다.

---

# Final Verdict

**Changes requested.**

현재 EDA는 폐기하거나 전면 재작성할 수준은 아니다. 분석 함수의 기본 구조와 retained output model은 재사용할 가치가 있다. 그러나 다음 세 항목이 해소되기 전에는 신뢰 가능한 Foundation artifact로 취급해서는 안 된다.

1. 6-core 계약의 전 계층 정렬
1. Notebook semantic completeness와 false-green test 해소
1. actual-source evidence 재생성 및 MD/JSON 일치

우선순위는 기능 추가가 아니라 **계약과 증거의 단일화**다.

---

## Reviewed Paths

- `openspec/specs/hmda-eda-baseline/spec.md`
- `openspec/changes/hmda-eda-baseline-reduce-core-scope/`
- `src/project_pivot/hmda_data/eda/analysis.py`
- `src/project_pivot/hmda_data/eda/__init__.py`
- `tests/hmda_data/eda/test_eda.py`
- `tests/hmda_data/eda/test_eda_notebook.py`
- `notebooks/eda_mo.py`
- `docs/references/hmda_eda.md`
- `docs/references/hmda_eda_reference.json`
- `docs/development/foundation/eda.md`
- `docs/development/foundation/readiness.md`
- `docs/development/foundation/readiness.yml`
- `docs/domains/hmda-data.md`

## Validation Limits

이 검토는 repository의 현재 `main`에 대한 정적 분석이다. 로컬 source data, DuckDB query, pytest, marimo render, lint/type checks는 실행하지 않았다. 따라서 runtime failure를 단정하지 않으며, 발견 사항은 계약·코드·artifact 간의 확인 가능한 불일치를 기준으로 한다.
