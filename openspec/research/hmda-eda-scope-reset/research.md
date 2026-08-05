---
type: openspec-rpi
title: "HMDA EDA scope reset"
description: "현재 EDA 구현과 계약을 재검토하여 reliability MVP에 남길 최소 evidence와 제거·유예할 surface를 결정한다."
category: research
status: completed
relatedArtifacts:
  - hmda-eda-foundation-extension
  - hmda-eda-baseline
  - foundation-baseline
---

# Research: hmda-eda-scope-reset

> [!IMPORTANT]
> EDA를 **현재 Gold mart를 설명하는 6개 column의 descriptive profile**로 재설정한다. Ingestion은 `county_code`를 포함한 7개 required source column의 존재를 검증하고, EDA는 계산에 사용하는 6개 core column의 타입 호환성과 descriptive metric을 소유한다. 무거운 fixture·memory subsystem은 제거하되 실제 HMDA source의 1회 read-only 실행 evidence는 Foundation 종료 근거로 유지한다.

## Question

Project Pivot의 reliability MVP와 현재 Gold mart를 설명하는 데 필요한 최소 EDA는 무엇이며, 이미 구현된 EDA surface 중 무엇을 유지·단순화·제거·유예해야 하는가?

## Scope

| Included | Excluded |
| --- | --- |
| 현재 `main`의 EDA code, tests, notebook, scripts, 문서와 OpenSpec | 이번 Research에서 실제 code·spec 삭제 또는 수정 |
| Gold mart와 직접 연결되는 column·metric | 99개 전체 HMDA field 분석 |
| Foundation 종료를 위한 최소 runtime evidence | 반복 성능 benchmark 또는 장기 운영 SLO |
| 제공된 EDA 현황·MVP 범위 문서의 재검증 | demographic·fairness·causal analysis |

## Source Basis

제공된 두 문서는 다음 판단을 공통으로 지원한다.

- 계산 계층에는 schema, volume, null, distribution, numeric summary, anomaly observation과 mart grain evidence가 이미 구현되어 있다.
- 주요 문제는 분석 부족보다 계산·Notebook·문서·OpenSpec 사이의 범위 불일치다.
- MVP 분석 대상은 `activity_year`와 `state_code`, `loan_purpose`, `action_taken`, `loan_amount`, `income`으로 축소한다.
- `county_code`, 약 22개 대표 field, 전체 99개 field 분석과 무거운 validation은 후속 iteration으로 미룬다.

Repository 재검증을 통해 다음 경계를 추가한다. 이는 제공 문서의 직접 결론이 아니라 이 Research의 권고다.

- `county_code`는 ingestion source contract에서 유지하고 descriptive EDA에서만 제외한다.
- Ingestion의 required-column 존재 검증과 EDA의 type compatibility 검증을 분리한다.
- Canonical anomaly requirement의 존재를 인정하되, 근거 수준과 구현 불일치를 이유로 MVP output에서 축소한다.
- EDA 전용 fixture·memory subsystem은 제거하지만 actual-source read-only observation은 유지한다.
- EDA freshness와 `ProfileSnapshot` mapping은 각 ingestion·reliability contract로 되돌린다.

## Review Resolution

| Review point | Decision | Resolution |
| --- | --- | --- |
| 7개 column 존재·타입 owner | Accept | Ingestion은 7개 존재, EDA는 6개 type compatibility를 소유하도록 분리 |
| anomaly contract 부재 진단 | Accept with correction | Canonical requirement는 존재하며, 문제는 근거가 약하고 구현과 불일치한다는 점으로 수정 |
| memory와 actual-source evidence 분리 | Accept | resource subsystem은 Drop, 1회 actual-source observation은 Keep |
| artifact layer별 Disposition | Accept | Code, API, Tests, Notebook, Spec, Active change, Docs, Runtime evidence로 재구성 |
| Target Contract 책임 분리 | Accept | Source Integrity, Descriptive EDA, Runtime Evidence로 분리 |
| replacement lifecycle 순서 | Accept | 기존 active change와 병행하지 않는 순서를 Handoff에 고정 |
| `source byte 보존` 표현 | Accept | `입력 source file을 수정하지 않음`으로 명확화 |

## Findings

### F1. 현재 EDA는 descriptive analysis보다 큰 resource-validation subsystem으로 확장됐다

`src/project_pivot/hmda_data/eda/`는 calculation 외에 500만 row fixture, manifest·hash·Pydantic contract와 process memory runner를 소유한다. 별도 scripts와 여러 fixture·memory tests가 이를 유지한다. 이 surface는 EDA 결과를 이해하는 데 필요한 범위를 넘어 독립적인 성능 검증 capability에 가깝다.

- **Evidence:** `src/project_pivot/hmda_data/eda/fixture.py`, `memory.py`, `scripts/prepare_hmda_eda_fixture.py`, `scripts/run_hmda_eda_memory.py`, `tests/hmda_data/eda/test_eda_fixture.py`, `test_eda_memory.py`, `test_eda_memory_helpers.py`
- **Implication:** Representative fixture, hard memory gate와 반복 측정은 Foundation EDA에서 제거한다. 단, 실제 HMDA source에서 shared entrypoint가 동작했다는 최소 observation은 별도 runtime evidence로 유지한다.

### F2. Source integrity와 descriptive EDA의 validation owner가 다르다

현재 ingestion의 `validate_required_columns`는 다음 7개 column의 **존재**만 확인한다.

- `activity_year`
- `state_code`
- `county_code`
- `loan_purpose`
- `action_taken`
- `loan_amount`
- `income`

반면 `analysis.py`는 같은 7개 column에 `EXPECTED_TYPE_FAMILIES`를 적용한다. Gold mart grain과 metric에 직접 연결되는 descriptive EDA 대상은 `county_code`를 제외한 6개다.

| Responsibility | Current owner | Target owner |
| --- | --- | --- |
| 7개 required column 존재 검증 | HMDA ingestion | HMDA ingestion 유지 |
| 7개 expected type family 검증 | EDA `analysis.py` | 6개 core column type compatibility로 축소 |
| 6개 core column descriptive metric | EDA | EDA 유지 |
| `county_code` 원천 보존 | ingestion·staging | 유지 |
| `county_code` 기본 분포 분석 | EDA | MVP에서 제거 |

- **Evidence:** `src/project_pivot/hmda_data/ingestion/_common.py`, `src/project_pivot/hmda_data/eda/analysis.py`, `dbt/models/staging/stg_hmda_loans.sql`, `dbt/models/marts/mart_hmda_loan_outcomes.sql`
- **Implication:** EDA 범위 축소는 ingestion source contract를 변경하지 않는다. EDA는 자신이 계산하는 6개 column에 대해서만 fail-fast type compatibility를 검증한다.

### F3. Canonical anomaly requirement는 존재하지만 근거 수준과 구현이 일치하지 않는다

Canonical `hmda-eda-baseline` spec은 다음을 요구한다.

- 허용 code 밖의 값을 unknown 또는 anomaly observation으로 기록
- `income < 0`
- `loan_amount <= 0`
- configured suspicious condition
- anomaly를 자동 정제나 incident 생성으로 연결하지 않음

실제 `analysis.py`는 `income < 0`과 `loan_amount <= 0`만 hard-coded observation으로 계산한다. Observed code distribution은 제공하지만 공식 code set과 대조해 unknown 값을 분류하지는 않는다.

따라서 문제는 anomaly contract의 부재가 아니다.

1. Canonical requirement는 존재한다.
1. 일부 numeric rule의 domain 근거가 spec에 충분히 기록되지 않았다.
1. Unknown-code requirement와 실제 구현이 일치하지 않는다.
1. External guidance의 upper-tail outlier 주의는 음수·0 규칙을 직접 부정하는 근거가 아니다.

| Rule or output | MVP decision | Reason |
| --- | --- | --- |
| Observed code distribution | Keep | 해석 전 원천 분포 evidence |
| Numeric min·max와 five-number summary | Keep | 값을 삭제하거나 clipping하지 않는 descriptive evidence |
| Unknown-code anomaly classification | Drop from MVP | versioned dictionary와 판정 정책을 함께 고정해야 함 |
| `income < 0`, `loan_amount <= 0` observation | Defer | domain 근거 확인 전 오류 또는 anomaly로 확정하지 않음 |
| Configured suspicious threshold | Drop from MVP | Foundation EDA의 필수 descriptive output이 아님 |
| 자동 정제·row 삭제·incident 생성 | Prohibit | EDA observation의 책임 밖 |

- **Evidence:** `openspec/specs/hmda-eda-baseline/spec.md`, `src/project_pivot/hmda_data/eda/analysis.py`, `data/references/hmda/data_fields_2025.md`
- **External evidence:** FFIEC/CFPB, `Snapshot National Loan-Level Dataset`, 확인일 2026-08-05 — `https://ffiec.cfpb.gov/data-publication/snapshot-national-loan-level-dataset/`
- **Implication:** MVP에서는 heuristic `anomalies` output을 제거하고 raw distribution과 numeric summary만 유지한다. Numeric rule은 별도 domain research와 versioned contract가 생길 때 재도입한다.

### F4. Actual-source observation은 memory benchmark와 별개의 Foundation evidence다

현재 reference 문서에는 4.8 GiB 실제 source의 1회 full scan 결과가 기록돼 있고 active change의 task 5.4도 actual-source observation report를 요구한다. 이 evidence는 representative fixture, 3회 반복 memory gate 또는 hard process limit과 목적이 다르다.

| Evidence | Purpose | Decision |
| --- | --- | --- |
| 500만 row synthetic fixture | 대표 workload 재현 | Drop |
| fixture manifest·hash contract | synthetic workload 동일성 | Drop |
| 3회 process memory gate | 반복 resource threshold | Drop |
| systemd/cgroup hard limit | process budget enforcement | Drop |
| strict memory·performance threshold | 운영 성능 판단 | Defer |
| 실제 HMDA source 1회 read-only smoke | shared entrypoint의 실제 데이터 실행 확인 | Keep |
| source identity·row count·duration·관찰 결과 | provenance와 재검토 가능성 | Keep |

Actual-source smoke는 성능 보장이나 OOM 안전성 증명이 아니다. Foundation 종료 시점에 한 번 실행하고 다음을 기록한다.

- source path
- source checksum 또는 동등한 immutable identifier
- 실행 시각과 tool version
- row count와 activity year 범위
- duration
- 핵심 null·distribution·numeric observation
- 실행 실패 또는 해석상 주의점

- **Evidence:** `docs/references/hmda_eda.md`, `openspec/changes/hmda-eda-foundation-extension/tasks.md`
- **Implication:** 작은 deterministic test만으로 Foundation EDA를 완료하지 않는다. 실제 source smoke를 focused validation의 acceptance evidence로 남긴다.

### F5. EDA freshness와 ProfileSnapshot mapping은 중복 책임이다

현재 full-source observation에는 `observed_at`이 없어 EDA freshness가 `unmeasured`로 끝난다. Reliability의 `DuckDBProfileSnapshotBuilder`는 table schema hash와 optional freshness column을 독립적으로 계산한다. Notebook의 EDA → `ProfileSnapshot` mapping은 display-only이며 실제 profile 생성 경로가 아니다.

- **Evidence:** `docs/references/hmda_eda.md`, `notebooks/eda_mo.py`, `src/project_pivot/reliability/profiling/profile_snapshot_builder.py`
- **Implication:** EDA-specific source freshness, schema hash와 `ProfileSnapshot` mapping을 core output에서 제거한다. Bronze ingestion time과 reliability profile freshness는 각 소유 contract에서 유지한다.

### F6. Notebook은 core descriptive evidence를 보여주지 못하며 실행 graph도 불완전하다

Notebook은 schema, volume, null, freshness와 `ProfileSnapshot` mapping만 렌더링한다. Distribution, numeric summary와 grain은 표시하지 않으며 `input_path`와 `run_eda`를 정의할 cell이 비어 있다.

- **Evidence:** `notebooks/eda_mo.py`
- **Implication:** 기존 화면을 확장하지 말고 입력·실행 경로를 복구한 뒤 네 영역만 남긴다: input baseline, categorical distributions, numeric summaries, mart grain.

### F7. Active change와 canonical spec lifecycle이 일치하지 않는다

`hmda-eda-foundation-extension`은 active 상태이고 task 대부분이 미완료지만, canonical `hmda-eda-baseline` spec에는 extension requirement와 heavy memory contract가 이미 반영돼 있다. 반면 canonical `foundation-baseline`은 이전 최소 EDA 계약을 유지한다.

- **Evidence:** `openspec/changes/hmda-eda-foundation-extension/`, `openspec/specs/hmda-eda-baseline/spec.md`, `openspec/specs/foundation-baseline/spec.md`
- **Implication:** Replacement change를 생성한 뒤 기존 active change의 추가 작업을 중지하고 superseded 상태를 명시한다. 두 change가 같은 EDA surface를 병행 소유해서는 안 된다.

## Target Contract

### Source Integrity

Ingestion이 다음을 소유한다.

1. `county_code`를 포함한 7개 required source column의 존재 검증.
1. 원천 column과 값을 Bronze에 그대로 보존.
1. EDA 범위 축소와 무관하게 현재 ingestion source contract 유지.

7개 column 전체의 expected type family를 공통 source contract로 승격하지 않는다. 필요성이 확인되면 별도 change에서 다룬다.

### Descriptive EDA

EDA가 다음을 소유한다.

1. 유효한 HMDA CSV에 대한 fail-fast, read-only calculation.
1. 계산에 사용하는 6개 core column의 type compatibility 검증.
1. 전체·`activity_year`별 volume과 6개 core column의 null evidence.
1. `state_code`, `loan_purpose`, `action_taken`의 observed count와 share.
1. `loan_amount`, `income`의 non-null count와 five-number summary.
1. 현재 mart grain의 distinct group count와 null-key coverage.
1. 동일 entrypoint를 사용하는 최소 Notebook과 focused automated tests.
1. 입력 source file을 수정하지 않고 자신이 연 DuckDB connection을 항상 닫는 execution boundary.

EDA는 unknown code나 suspicious numeric value를 자동 정제하거나 incident로 전환하지 않는다.

### Runtime Evidence

Foundation acceptance는 다음 1회성 evidence를 포함한다.

1. 실제 HMDA source를 shared entrypoint로 read-only 실행.
1. Source identity, 실행 시각, row count, duration과 주요 observation 기록.
1. 작은 deterministic test와 actual-source smoke를 명확히 분리.
1. 해당 실행을 일반적인 memory·performance 보장으로 해석하지 않음.

## Disposition By Layer

### Code

| Action | Surface | Target |
| --- | --- | --- |
| Keep | `analyze_hmda_csv` | Notebook과 test가 공유하는 read-only entrypoint |
| Keep | volume, null, distribution, numeric summary, grain | 6개 core column의 descriptive evidence |
| Simplify | required validation | 7개 존재 검증은 ingestion에 두고 EDA type check는 6개로 축소 |
| Drop | `county_code` distribution | source에는 보존하되 MVP 분석에서 제외 |
| Drop | `_collect_anomalies`와 `anomalies` output | heuristic output을 MVP contract에서 제거 |
| Drop | EDA `freshness`, `schema_hash`, Profile mapping | ingestion·reliability 책임으로 이동 |
| Drop | `fixture.py`, `memory.py` | EDA보다 큰 resource-validation subsystem |
| Keep | connection close와 read-only behavior | execution safety boundary |

### Public API

| Action | Surface | Target |
| --- | --- | --- |
| Keep | `analyze_hmda_csv` export | 단일 EDA public entrypoint |
| Drop | fixture·memory 관련 exports | 제거되는 subsystem과 함께 public surface 축소 |
| Review | removed evidence keys | repository consumer search 후 deprecation 필요성 결정 |

### Tests

| Action | Surface | Target |
| --- | --- | --- |
| Keep | small deterministic correctness test | core metric과 6개 type compatibility 검증 |
| Keep | parse failure, partial result 금지, connection close, source read-only | failure boundary 검증 |
| Drop | fixture·memory resource-specific suite | 제거되는 subsystem 전용 test |
| Replace | malformed Notebook plan file | 실제로 종료 가능한 최소 runtime smoke |
| Separate | actual-source smoke | unit test가 아닌 acceptance evidence command |

### Notebook

| Action | Surface | Target |
| --- | --- | --- |
| Repair | input과 execution cell | `input_path`와 shared entrypoint 연결 복구 |
| Keep | input, volume, null | baseline view |
| Add | categorical, numeric, grain | core descriptive view |
| Drop | freshness와 ProfileSnapshot mapping | EDA 책임 밖 |
| Exclude | county-level view와 anomaly dashboard | 후속 domain work |

### Canonical Spec

| Action | Requirement | Target |
| --- | --- | --- |
| Keep | fail-fast, read-only, reusable calculation | execution contract 유지 |
| Reduce | required schema baseline | ingestion 존재 검증과 EDA 6개 type check로 책임 분리 |
| Keep | volume, null, distribution, numeric summary, grain | MVP descriptive contract |
| Remove | unknown-code anomaly와 suspicious numeric output | domain 근거 확정 전 canonical MVP에서 제외 |
| Remove | freshness와 Profile mapping | 각 소유 spec으로 이동 |
| Remove | representative fixture와 process memory gate | Foundation EDA contract에서 폐기 |
| Add | actual-source 1회 observation | focused acceptance evidence로 명시 |

### Active Change

| Action | Surface | Target |
| --- | --- | --- |
| Create | `hmda-eda-baseline-reduce-core-scope` | 축소·정리 목적의 replacement change |
| Stop | `hmda-eda-foundation-extension` 추가 구현 | replacement 생성 후 병행 작업 금지 |
| Supersede | 기존 active change | tooling이 지원하는 방식으로 대체 관계 명시 |
| Reconcile | canonical EDA·Foundation spec | replacement delta에서 현재 lifecycle drift 수정 |

### Documentation

| Action | Surface | Target |
| --- | --- | --- |
| Rewrite | `docs/references/hmda_eda.md` | 실행법, metric definition, responsibility boundary, latest evidence |
| Update | Foundation readiness | EDA capability와 acceptance evidence를 하나의 최신 상태로 표현 |
| Remove | fixture·memory 운영 절차 | 제거되는 subsystem 문서 정리 |
| Keep | actual-source observation | 환경과 한계를 포함한 evidence 기록 |

### Runtime Evidence

| Action | Surface | Target |
| --- | --- | --- |
| Keep | actual-source read-only smoke | Foundation 종료 전 1회 실행 |
| Record | path, checksum/identifier, timestamp, row count, duration | 재현 가능한 provenance |
| Record | key observation와 known limitation | 결과 해석 경계 |
| Drop | 3회 memory gate와 hard-limit probe | Foundation acceptance에서 제거 |
| Defer | strict performance threshold | 실제 요구가 생길 때 별도 workstream |

## Impact

| Area | Impact or risk |
| --- | --- |
| Public API | `analyze_hmda_csv`는 유지하지만 일부 evidence key와 helper export가 제거될 수 있음 |
| Source contract | Ingestion의 7개 required column 존재 검증과 Bronze 보존은 변경하지 않음 |
| EDA validation | Type compatibility 범위가 7개에서 6개 core column으로 축소됨 |
| Notebook | 기존 화면보다 작아지지만 실제 MVP metric을 직접 보여줌 |
| Tests | resource-specific suite는 제거되고 core correctness와 failure boundary만 남음 |
| Runtime evidence | 작은 fixture 외에 actual-source 1회 observation을 유지함 |
| OpenSpec | canonical EDA·Foundation spec과 기존 active change를 함께 정리해야 함 |

## Conflicts

| Sources | Conflict | Required resolution |
| --- | --- | --- |
| Ingestion vs EDA implementation | 존재 검증과 7개 type 검증이 서로 다른 owner에 있음 | ingestion 7개 존재, EDA 6개 type으로 분리 |
| Canonical anomaly spec vs implementation | unknown-code 요구는 미구현이고 numeric rule만 hard-coded | heuristic output 제거와 spec 축소 |
| Human intent vs active extension | 확장 계획 대신 적극적인 축소·삭제가 필요함 | replacement OpenSpec change |
| Active change vs canonical EDA spec | 미완료 change requirement가 canonical spec에 이미 포함됨 | spec delta와 lifecycle 정리 |
| Resource subsystem vs evidence-first goal | 무거운 gate 제거 시 실제 데이터 evidence까지 사라질 위험 | actual-source smoke를 별도 acceptance evidence로 유지 |
| Reference doc vs Notebook | 문서는 full-source 결과를 기록하지만 Notebook graph는 불완전함 | Notebook 재작성과 최신 evidence 갱신 |

## Assumptions

| Assumption | Validation or containment |
| --- | --- |
| 제거 대상 evidence key와 helper의 repository 외부 consumer가 없다 | implementation 전에 repository reference search와 public API diff를 확인한다 |
| EDA의 목적은 mart와 reliability MVP를 설명하는 descriptive evidence다 | replacement proposal에 목적과 non-goal을 명시한다 |
| 6개 core column type compatibility로 metric 계산을 안전하게 보호할 수 있다 | focused invalid-type fixture로 검증한다 |
| actual-source smoke는 Foundation 종료에 한 번이면 충분하다 | 반복 실행은 release 또는 회귀 요구가 생길 때 별도 결정한다 |

## Open Questions

- 제거되는 evidence key와 public export에 deprecation period가 필요한지는 repository reference 확인 후 Design에서 결정한다.
- 기존 change를 superseded로 기록하는 정확한 command와 archive 방식은 현재 OpenSpec tooling에 맞춰 결정한다.
- Actual-source evidence의 canonical 저장 경로와 checksum 생성 방식은 replacement Design에서 고정한다.
- Valid Notebook smoke를 pytest로 둘지 dedicated Marimo command로 둘지는 Design에서 결정한다.

## Handoff

| Field | Content |
| --- | --- |
| Problem | EDA가 mart-facing descriptive analysis보다 큰 fixture·memory subsystem으로 확장됐고 validation owner, Notebook과 OpenSpec lifecycle도 불일치한다. |
| Decision | Ingestion의 7개 존재 검증을 유지하고 EDA를 6개 core column의 type compatibility·descriptive metric으로 축소한다. Heavy resource gate는 제거하되 actual-source 1회 smoke는 유지한다. |
| Replacement change | `hmda-eda-baseline-reduce-core-scope` |
| In scope | EDA calculation·API·tests·Notebook·canonical spec·active change·docs·runtime evidence 정리 |
| Out of scope | ingestion schema 변경, county·demographic 확장, anomaly domain rule 설계, 운영 성능 SLO |
| Validation | focused correctness·failure test, valid Notebook smoke, actual-source read-only observation, repository-wide regression |

### Lifecycle Sequence

```text
scope-reset Research 인간 검토
→ replacement change 생성
→ 기존 hmda-eda-foundation-extension 추가 작업 중지 및 superseded 명시
→ canonical EDA/Foundation spec delta 작성
→ implementation
→ focused validation과 actual-source read-only observation
→ replacement change archive
```

Replacement change가 생성된 뒤 기존 `hmda-eda-foundation-extension`과 병행 구현하지 않는다. 정확한 supersede·archive command는 tooling에 맞추되, 동일 EDA surface의 ownership은 replacement change 하나로 제한한다.

## Conclusion

Foundation EDA는 **6개 core column의 descriptive evidence와 실제 source의 1회 실행 증거**로 닫는다. Ingestion은 7개 required column의 존재와 원천 보존을 계속 소유한다. EDA는 6개 core column의 타입 호환성, volume, null, distribution, numeric summary와 mart grain만 계산한다.

500만 row fixture, manifest·hash, 반복 memory gate, hard-limit runner, freshness, EDA schema hash, Profile mapping과 heuristic anomaly output은 Foundation 범위에서 제거한다. Strict performance validation, county·demographic 분석과 domain-backed anomaly rule은 별도 필요가 확인될 때 독립 change로 재도입한다.
