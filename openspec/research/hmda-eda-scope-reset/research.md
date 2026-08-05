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
> EDA를 **현재 Gold mart를 설명하는 6개 core column의 descriptive profile**로 축소한다.
>
> 무거운 fixture·memory subsystem은 제거하되, 실제 HMDA source의 1회 read-only 실행 evidence는 Foundation 종료 근거로 유지한다.

## Question

Reliability MVP와 현재 Gold mart를 설명하는 데 필요한 최소 EDA는 무엇인가?

## Decision

| Area | Decision |
| --- | --- |
| Source integrity | Ingestion이 7개 required column의 존재를 검증한다. |
| Descriptive EDA | EDA가 6개 core column의 타입 호환성과 metric을 검증한다. |
| Runtime evidence | 실제 HMDA source를 1회 read-only로 실행하고 결과를 기록한다. |
| Resource validation | 500만 row fixture, 반복 memory gate와 hard-limit runner를 제거한다. |

### Core Columns

| Role | Columns | Evidence |
| --- | --- | --- |
| Structural | `activity_year` | 전체·연도별 volume, mart grain |
| Categorical | `state_code`, `loan_purpose`, `action_taken` | null, count, share |
| Numeric | `loan_amount`, `income` | null, non-null count, five-number summary |

`county_code`는 ingestion과 staging에서 보존하지만 MVP EDA 분석에서는 제외한다.

## Findings

### F1. Validation owner가 섞여 있다

현재 ingestion은 7개 required column의 **존재**를 검증한다. EDA는 같은 7개 column의 expected type family를 검증한다.

MVP에서는 책임을 다음처럼 단순화한다.

```text
Ingestion
- 7개 required column 존재 검증

EDA
- 6개 core column type compatibility 검증
- descriptive metric 계산
```

- **Evidence:** `src/project_pivot/hmda_data/ingestion/_common.py`, `src/project_pivot/hmda_data/eda/analysis.py`

### F2. EDA가 resource-validation subsystem으로 커졌다

EDA package는 계산 외에도 다음을 소유한다.

- 500만 row synthetic fixture
- manifest와 hash contract
- process memory runner
- hard memory limit과 반복 측정
- 전용 scripts와 tests

이 surface는 descriptive EDA보다 크다. Foundation 완료 조건에서 제거하고, 실제 성능 문제가 확인될 때 별도 workstream으로 다시 설계한다.

- **Evidence:** `src/project_pivot/hmda_data/eda/fixture.py`, `memory.py`, `scripts/prepare_hmda_eda_fixture.py`, `scripts/run_hmda_eda_memory.py`

### F3. Anomaly spec과 구현이 일치하지 않는다

Canonical spec에는 다음 anomaly observation 요구가 있다.

- unknown code
- `income < 0`
- `loan_amount <= 0`
- configured suspicious condition

현재 구현은 두 numeric rule만 계산하며 unknown code를 분류하지 않는다. 일부 rule의 domain 근거도 spec에 충분히 기록되지 않았다.

| Output | MVP decision |
| --- | --- |
| Observed code distribution | Keep |
| Numeric min·max와 five-number summary | Keep |
| Unknown-code classification | Drop |
| `income < 0`, `loan_amount <= 0` observation | Defer |
| Configured suspicious threshold | Drop |
| 자동 정제·row 삭제·incident 생성 | Prohibit |

Numeric rule을 잘못된 것으로 단정하지 않는다. Domain 근거와 versioned contract가 마련될 때 재검토한다.

- **Evidence:** `openspec/specs/hmda-eda-baseline/spec.md`, `src/project_pivot/hmda_data/eda/analysis.py`, `data/references/hmda/data_fields_2025.md`

### F4. Actual-source evidence는 memory benchmark와 다르다

무거운 resource gate를 제거해도 실제 데이터 evidence까지 없애면 안 된다.

Foundation 종료 전 실제 HMDA source를 한 번 실행하고 다음을 기록한다.

- source path와 checksum 또는 동등한 identifier
- 실행 시각과 tool version
- row count와 activity year 범위
- duration
- 핵심 null·distribution·numeric observation
- 실패와 해석상 주의점

이 실행은 성능 보장이나 OOM 안전성 증명이 아니다.

- **Evidence:** `docs/references/hmda_eda.md`, `openspec/changes/hmda-eda-foundation-extension/tasks.md`

### F5. Notebook과 OpenSpec 상태가 현재 구현과 맞지 않는다

Notebook은 core distribution, numeric summary와 grain을 보여주지 못하며 실행 graph도 불완전하다.

또한 `hmda-eda-foundation-extension`은 active 상태지만 일부 requirement는 canonical spec에 이미 반영돼 있다.

따라서 Notebook을 최소 화면으로 다시 작성하고, replacement change 하나가 EDA 축소 작업을 소유해야 한다.

- **Evidence:** `notebooks/eda_mo.py`, `openspec/changes/hmda-eda-foundation-extension/`, `openspec/specs/hmda-eda-baseline/spec.md`

## Target Contract

### Source Integrity

Ingestion은 다음을 소유한다.

1. `county_code`를 포함한 7개 required column의 존재 검증.
2. 원천 column과 값을 Bronze에 보존.
3. EDA 범위와 무관한 현재 source contract 유지.

### Descriptive EDA

EDA는 다음을 소유한다.

1. HMDA CSV의 fail-fast, read-only 계산.
2. 6개 core column의 type compatibility 검증.
3. 전체·연도별 volume과 null evidence.
4. 세 categorical column의 count와 share.
5. 두 numeric column의 non-null count와 five-number summary.
6. 현재 mart grain의 distinct group count와 null-key coverage.
7. 공유 entrypoint를 사용하는 Notebook과 focused tests.
8. 입력 source file을 수정하지 않고 DuckDB connection을 항상 닫는 것.

### Runtime Evidence

Foundation acceptance에는 다음을 포함한다.

1. 실제 HMDA source의 1회 read-only 실행.
2. Source identity, 실행 환경과 주요 결과 기록.
3. Deterministic test와 actual-source observation의 구분.

## Change Scope

| Layer | Change |
| --- | --- |
| Code | `analyze_hmda_csv`와 core metric을 유지하고 anomaly·freshness·schema hash를 제거한다. |
| Public API | EDA entrypoint만 유지하고 fixture·memory export를 제거한다. |
| Tests | Core correctness와 failure boundary를 유지하고 resource-specific suite를 제거한다. |
| Notebook | Input, volume, null, distribution, numeric summary와 grain만 표시한다. |
| Canonical spec | Anomaly, freshness, Profile mapping과 memory requirement를 축소·제거한다. |
| Active change | Replacement change 생성 후 기존 extension 작업을 중지하고 superseded 처리한다. |
| Documentation | 실행법, metric 정의, 책임 경계와 최신 evidence만 유지한다. |
| Runtime evidence | Actual-source smoke는 유지하고 반복 성능 gate는 제거한다. |

## Risks

| Risk | Control |
| --- | --- |
| 제거되는 API의 외부 consumer | 구현 전 repository reference와 public API diff 확인 |
| Anomaly rule의 성급한 폐기 | Rule은 Defer하고 descriptive output만 제거 |
| 작은 fixture만으로 Foundation 완료 | Actual-source smoke를 acceptance evidence로 유지 |
| 두 OpenSpec change의 중복 소유 | Replacement 생성 후 기존 change의 추가 작업 중지 |

## Handoff

**Replacement change:** `hmda-eda-baseline-reduce-core-scope`

```text
Research 인간 검토
→ replacement change 생성
→ 기존 hmda-eda-foundation-extension 작업 중지·superseded 처리
→ canonical EDA/Foundation spec 수정
→ implementation
→ focused tests·Notebook smoke·actual-source observation
→ replacement change archive
```

Replacement change가 생성된 뒤 기존 extension과 병행 구현하지 않는다.

## Open Questions

- 제거되는 public API에 deprecation period가 필요한가?
- Actual-source evidence의 저장 경로와 checksum 방식은 무엇인가?
- Notebook smoke를 pytest와 Marimo command 중 어디에 둘 것인가?

## Conclusion

Foundation EDA는 **6개 core column의 descriptive evidence와 실제 source의 1회 실행 증거**로 닫는다.

Ingestion은 7개 required column의 존재와 원천 보존을 유지한다. EDA는 6개 core column의 타입 호환성, volume, null, distribution, numeric summary와 mart grain만 소유한다.

Fixture·memory subsystem, freshness, EDA schema hash, Profile mapping과 heuristic anomaly output은 Foundation 범위에서 제거한다.