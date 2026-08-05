---
type: openspec-rpi
title: "HMDA EDA scope reset"
description: "현재 EDA를 reliability MVP에 필요한 최소 범위로 축소한다."
category: research
status: completed
relatedArtifacts:
  - hmda-eda-foundation-extension
  - hmda-eda-baseline
  - foundation-baseline
---

# Research: hmda-eda-scope-reset

> [!IMPORTANT]
> EDA를 **Gold mart를 설명하는 6개 core column의 descriptive profile**로 축소한다.
>
> Fixture·memory subsystem은 제거하되, 실제 HMDA source의 1회 read-only 실행 evidence는 유지한다.

## Question

Reliability MVP와 현재 Gold mart를 설명하는 데 필요한 최소 EDA는 무엇인가?

## Decision

### Responsibility

| Owner | Contract |
| --- | --- |
| Ingestion | `county_code`를 포함한 7개 required column 존재 검증과 Bronze 보존 |
| EDA | 6개 core column의 타입 호환성 검증과 descriptive metric 계산 |
| Runtime evidence | 실제 HMDA source의 1회 read-only 실행과 결과 기록 |

EDA는 입력 source file을 수정하지 않으며, 성공과 실패 모두 자신이 연 DuckDB connection을 닫는다.

### Core Evidence

| Role | Columns | Evidence |
| --- | --- | --- |
| Structural | `activity_year` | 전체·연도별 volume, mart grain |
| Categorical | `state_code`, `loan_purpose`, `action_taken` | null, count, share |
| Numeric | `loan_amount`, `income` | null, non-null count, five-number summary |

`county_code`는 source contract에 유지하지만 MVP EDA 분석에서는 제외한다.

### Scope Reset

| Keep | Remove | Defer |
| --- | --- | --- |
| `analyze_hmda_csv` | 500만 row fixture | Strict performance threshold |
| Core metric과 focused tests | Manifest·hash subsystem | County·demographic analysis |
| 최소 Notebook | 반복 memory gate | Domain-backed anomaly rule |
| Actual-source 1회 smoke | Hard-limit runner | 전체 HMDA field inventory |
| Read-only·connection close | Freshness·Profile mapping |  |

## Evidence

### Validation owner가 섞여 있다

현재 ingestion은 7개 required column의 **존재**를 검증한다. EDA는 같은 7개 column의 expected type family를 검증한다.

MVP에서는 EDA type check를 실제 계산에 사용하는 6개 core column으로 축소한다.

- **Evidence:** `src/project_pivot/hmda_data/ingestion/_common.py`, `src/project_pivot/hmda_data/eda/analysis.py`

### EDA가 resource-validation subsystem으로 커졌다

EDA package는 계산 외에도 synthetic fixture, manifest, process memory runner와 hard-limit 검증을 소유한다.

이는 descriptive EDA보다 큰 독립 capability다. Foundation 범위에서 제거하고 실제 성능 문제가 확인될 때 별도 workstream으로 다시 설계한다.

- **Evidence:** `src/project_pivot/hmda_data/eda/fixture.py`, `memory.py`, `scripts/prepare_hmda_eda_fixture.py`, `scripts/run_hmda_eda_memory.py`

### Anomaly spec과 구현이 일치하지 않는다

Canonical spec은 unknown code, `income < 0`, `loan_amount <= 0`과 configured suspicious condition을 요구한다. 현재 구현은 두 numeric rule만 계산한다.

| Output | Decision |
| --- | --- |
| Observed code distribution | Keep |
| Numeric min·max와 five-number summary | Keep |
| Unknown-code classification | Remove |
| `income < 0`, `loan_amount <= 0` observation | Defer |
| Configured suspicious threshold | Remove |
| 자동 정제·row 삭제·incident 생성 | Prohibit |

Numeric rule을 잘못된 것으로 단정하지 않는다. Domain 근거와 versioned contract가 마련될 때 재검토한다.

- **Evidence:** `openspec/specs/hmda-eda-baseline/spec.md`, `src/project_pivot/hmda_data/eda/analysis.py`, `data/references/hmda/data_fields_2025.md`

### Actual-source evidence는 memory benchmark와 다르다

무거운 resource gate를 제거해도 실제 데이터 evidence까지 없애면 안 된다.

Foundation 종료 전 실제 HMDA source를 한 번 실행하고 다음을 기록한다.

- source identifier
- 실행 시각과 환경
- row count와 activity year 범위
- duration
- 핵심 observation과 limitation

이 실행은 성능 보장이나 OOM 안전성 증명이 아니다.

- **Evidence:** `docs/references/hmda_eda.md`, `openspec/changes/hmda-eda-foundation-extension/tasks.md`

### Notebook과 OpenSpec lifecycle이 불완전하다

Notebook은 core distribution, numeric summary와 grain을 표시하지 못하며 실행 graph도 불완전하다.

또한 active extension의 일부 requirement가 canonical spec에 이미 반영돼 있다. Replacement change 하나가 EDA 축소 작업을 소유해야 한다.

- **Evidence:** `notebooks/eda_mo.py`, `openspec/changes/hmda-eda-foundation-extension/`, `openspec/specs/hmda-eda-baseline/spec.md`

## Change Plan

| Layer | Change |
| --- | --- |
| Code | Core metric만 유지하고 anomaly·freshness·schema hash와 fixture·memory module을 제거한다. |
| Public API | `analyze_hmda_csv`만 유지하고 fixture·memory export를 제거한다. |
| Tests | Core correctness와 failure boundary만 유지한다. |
| Notebook | Input, volume, null, distribution, numeric summary와 grain만 표시한다. |
| Canonical spec | Anomaly, freshness, Profile mapping과 memory requirement를 축소·제거한다. |
| Active change | Replacement 생성 후 기존 extension을 superseded 처리한다. |
| Documentation | 실행법, metric 정의, 책임 경계와 최신 evidence만 유지한다. |
| Runtime evidence | Actual-source 1회 smoke를 Foundation acceptance로 기록한다. |

## Handoff

**Replacement change:** `hmda-eda-baseline-reduce-core-scope`

```text
Research 인간 검토
→ replacement change 생성
→ 기존 extension 작업 중지·superseded 처리
→ canonical EDA/Foundation spec 수정
→ implementation
→ focused tests·Notebook smoke·actual-source observation
→ replacement change archive
```

Replacement change가 생성된 뒤 기존 extension과 병행 구현하지 않는다.

## Open Questions

- 제거되는 public API에 deprecation period가 필요한가?
- Actual-source evidence는 어디에 저장할 것인가?
- Notebook smoke는 pytest와 Marimo command 중 어디에 둘 것인가?
