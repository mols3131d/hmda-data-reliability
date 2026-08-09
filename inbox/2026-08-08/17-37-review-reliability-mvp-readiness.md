---
type: review
title: Reliability MVP Readiness Review
description: PR #14의 volume_drop MVP Research를 현재 main과 대조해 MVP 진입과 planning handoff readiness를 검토한다.
status: completed
tags:
  - "domain:reliability"
  - "phase:mvp"
  - "capability:recovery"
---

> [!NOTE]
> **Project의 MVP 진입은 Pass, PR #14의 planning handoff는 Revise다.** Foundation canonical readiness는 `GO`이고 audit 이후 source/spec/test 변경도 없다. 다만 PR #14는 현재 `main`보다 84 commits 뒤처져 Foundation gate가 낡았으며, MVP가 요구하는 `dbt build`의 artifact isolation/last-known-good 보존 계약이 빠져 있다. 두 항목을 Research 또는 후속 OpenSpec planning에 반영한 뒤 `volume_drop` vertical slice로 진행하는 것이 적절하다.

## Overview

| Target | Revision | Scope | Verdict |
| --- | --- | --- | --- |
| PR #14 `Reliability MVP Volume-Drop Vertical Slice` | head `acc2733`, current `main` `22fdfd0` | MVP 선택, Foundation gate, approval/recovery, dbt evidence | **Revise** |
| MVP entry | Foundation readiness audited `feea63f` | Foundation → MVP phase transition | **Pass** |

## Findings

### F1. PR #14의 Foundation gate와 revision 근거가 현재 상태와 불일치한다

- **Severity** - Major
- **Location** - PR #14 NOTE, Conclusion/Next Step, Validation
- **Evidence** - PR #14는 Foundation completion 전 Apply를 차단하고 branch가 current `main`보다 뒤처지지 않았다고 기록한다. 현재 비교 결과는 PR head가 `main`보다 **84 commits behind / 1 ahead**다. 반면 `docs/development/foundation/readiness.md`는 2026-08-08 snapshot에서 **GO**, `147/147` implementation coverage, `111/111` verification checklist, blocker 없음으로 판정한다. Audited revision `feea63f` 이후 current `main`까지는 readiness 문서와 inbox artifact만 변경됐고 source/spec/test 변경은 없다.
- **Impact** - Research를 그대로 planning input으로 쓰면 이미 닫힌 Foundation gate가 MVP Apply를 불필요하게 막고, 검토 revision에 대한 신뢰도도 떨어진다.
- **Required Change** - PR #14를 current `main`에 맞춰 재검증하고 Foundation completion block을 제거한다. Foundation의 non-gating inventory는 MVP 구현·검증 입력으로 다루되 phase-entry blocker로 되돌리지 않는다.

### F2. Isolated candidate validation이 shared dbt artifact를 보호하지 못한다

- **Severity** - Major
- **Location** - PR #14 F2/F3/F4, Required Acceptance; `src/project_pivot/data_operations/runner.py`; `DataOperationRequest`
- **Evidence** - Research는 candidate validation과 approved recovery에서 full `dbt build`, post-mutation failure evidence와 replay를 요구한다. 현재 `run_dbt_build()`는 실행 전에 `manifest.json`과 `run_results.json`을 삭제하며, 기본 artifact 경로는 공용 `dbt/target/`이다. Foundation readiness도 `dbt last-known-good evidence retention`을 blocked non-gating risk로 기록한다.
- **Impact** - candidate validation 또는 recovery build가 실패하면 이전 artifact가 소실되거나 candidate run artifact로 교체될 수 있다. 그러면 Research가 요구하는 isolated validation, impact evidence, failure reconciliation과 replay의 근거가 흔들린다.
- **Required Change** - MVP OpenSpec contract에 **run/phase별 dbt artifact isolation 또는 last-known-good의 원자적 보존**을 포함한다. 실패한 `dbt build`가 이전 유효 artifact를 훼손하지 않는 acceptance case와, validation/approval/recovery evidence가 어떤 artifact projection에 결합되는지도 명시한다. Exact path와 구현 방식은 Design에서 결정한다.

## Validation

| Check | Evidence | Result |
| --- | --- | --- |
| Foundation phase gate | `docs/development/foundation/readiness.md` | Pass |
| Readiness audit 이후 behavioral drift | `feea63f...main` compare: source/spec/test 변경 없음 | Pass |
| Research revision currency | `main...chatbot/docs/reliability-mvp-research` compare | Fail — 84 behind |
| Existing approval binding | `contracts/approval.py`, `recovery/executor.py` | MVP gap confirmed |
| Partition replacement atomicity | `hmda_data/ingestion/partition.py` transaction | Pass |
| dbt artifact preservation | `data_operations/runner.py`, readiness non-gating inventory | Fail |
| Existing reliability runtime execution | readiness non-gating inventory | Not Verified |

검토는 repository content와 GitHub revision 비교로 수행했다. pytest, dbt build, OpenSpec CLI는 이 Review에서 실행하지 않았다.

## Remaining Risks

- Profile/incident/impact/remediation lifecycle과 approval backfill은 구현되어 있으나 current execution은 canonical readiness에서 아직 unverified다. MVP의 첫 integration baseline에서 검증해야 한다.
- `data-operations-refactor-runner` OpenSpec change는 plan approved, tasks `4/4`이며 현재 코드에 반영돼 있지만 아직 active다. MVP change가 같은 runner/capability를 수정한다면 먼저 archive하거나 변경 순서를 명확히 해 overlapping ownership을 피한다.
- Dagster orchestration blocker와 freshness semantics는 PR #14의 `volume_drop` recovery slice 범위 밖이므로 MVP entry blocker로 승격하지 않는다.

## Verdict

| Decision | Rationale | Route |
| --- | --- | --- |
| **MVP Entry: Pass** | Foundation gate는 닫혔고 research가 선택한 단일 `volume_drop` slice는 현재 architecture boundary와 맞는다. | Reliability MVP OpenSpec planning 시작 |
| **PR #14: Revise** | stale Foundation gate와 dbt artifact safety contract 누락을 수정해야 current planning input이 된다. | PR #14 재검증·수정 후 planning handoff |

MVP의 핵심은 새 기능 폭을 넓히는 것이 아니라 **`volume_drop` 하나에서 detection → validation → approval → recovery → verification evidence를 안전하게 닫는 것**이다. 위 두 finding 외에 MVP 진입을 막아야 할 추가 blocker는 이번 검토에서 확인되지 않았다.
