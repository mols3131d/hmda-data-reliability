---
type: review
title: Reliability MVP Readiness Review
description: PR #14의 acc2733 volume_drop MVP Research를 review snapshot main@22fdfd0과 대조해 MVP 진입과 planning handoff readiness를 검토한다.
status: completed
tags:
  - "domain:reliability"
  - "phase:mvp"
  - "capability:recovery"
---

> [!NOTE]
> **Review snapshot 기준 Project의 MVP 진입은 Pass, PR #14 `acc2733`의 planning handoff는 Revise다.** Foundation canonical readiness는 `GO`이고 audited revision부터 `main@22fdfd0`까지 source/spec/test behavioral change는 없다. 다만 PR #14는 snapshot `main`보다 84 commits 뒤처져 Foundation gate가 낡았고, dbt artifact safety, reconciliation의 stale approval 차단, Research artifact contract 정렬이 부족하다. 이 항목들은 MVP phase-entry blocker가 아니라 Research를 Planning input으로 사용하기 전에 닫아야 할 handoff 문제다.

## Overview

| Target | Revision | Scope | Verdict |
| --- | --- | --- | --- |
| PR #14 `Reliability MVP Volume-Drop Vertical Slice` | head `acc2733`, review snapshot `main@22fdfd0` | MVP 선택, Foundation gate, approval/recovery, dbt evidence, Research contract | **Revise** |
| MVP entry | Foundation readiness audited `feea63f` | Foundation → MVP phase transition | **Pass** |

이 Review의 repository-state 판단은 `main@22fdfd0`에 고정한다. 이후 `main`의 변경을 이 결과에 소급해 적용하지 않는다.

## Findings

### F1. PR #14의 Foundation gate와 revision 근거가 review snapshot과 불일치한다

- **Severity** - Major
- **Location** - PR #14 NOTE, Conclusion/Next Step, Validation
- **Evidence** - PR #14는 Foundation completion 전 Apply를 차단하고 branch가 당시 `main`보다 뒤처지지 않았다고 기록한다. Snapshot 비교 결과는 PR head가 `main@22fdfd0`보다 **84 commits behind / 1 ahead**다. 반면 `docs/development/foundation/readiness.md`는 2026-08-08 snapshot에서 **GO**, `147/147` implementation coverage, `111/111` verification checklist, blocker 없음으로 판정한다. Audited revision `feea63f`부터 `main@22fdfd0`까지 변경은 readiness 문서와 inbox artifact에 한정되며 source/spec/test 변경은 없다.
- **Impact** - Research를 그대로 Planning input으로 사용하면 이미 닫힌 Foundation gate가 MVP Apply를 불필요하게 막고, 검토 revision에 대한 신뢰도도 떨어진다.
- **Required Change** - PR #14를 snapshot `main`에 맞춰 재검증하고 Foundation completion block을 제거한다. Foundation non-gating inventory는 MVP 구현·검증 입력으로 다루되 phase-entry blocker로 되돌리지 않는다.

### F2. Isolated candidate validation이 shared dbt artifact를 보호하지 못한다

- **Severity** - Major
- **Location** - PR #14 F3-F5, Required Acceptance; `src/project_pivot/data_operations/runner.py`; `DataOperationRequest`
- **Evidence** - Research는 candidate validation과 approved recovery에서 full `dbt build`, post-mutation failure evidence와 replay를 요구한다. Snapshot의 `run_dbt_build()`는 실행 전에 `manifest.json`과 `run_results.json`을 삭제하며 `DataOperationRequest` 기본 artifact 경로는 공용 `dbt/target/`이다. Foundation readiness도 `dbt last-known-good evidence retention`을 blocked non-gating risk로 기록한다.
- **Impact** - Candidate validation 또는 recovery build가 실패하면 이전 artifact가 소실되거나 candidate run artifact로 교체될 수 있다. 그러면 isolated validation, impact evidence, failure reconciliation과 replay의 근거가 흔들린다.
- **Required Change** - Candidate validation은 **run-scoped dbt artifact workspace로 shared current artifact와 격리**한다. Target recovery build는 실패해도 **prior last-known-good artifact를 보존**하고, 성공·검증된 build만 current artifact projection으로 승격한다. Validation/approval/recovery evidence가 판단에 사용한 artifact projection을 식별하는 acceptance case도 포함한다. Exact path, promotion 방식과 retention은 Design에서 결정한다.

### F3. Reconciliation이 diverged target에 old approval을 재사용할 수 있다

- **Severity** - Major
- **Location** - PR #14 F4, Required Acceptance `Recovery reconciliation`
- **Evidence** - Research는 `verification_failed` 이후 같은 run, approval과 candidate로 reconciliation을 허용하고 partition fingerprint를 확인해 필요할 때 overwrite를 반복하도록 한다. 그러나 current partition이 **승인 당시 pre-recovery state와 expected recovered state 어느 쪽에도 일치하지 않는 경우**의 fail-closed behavior는 명시하지 않는다. PR #14 F3의 stale-state rule은 최초 approved recovery 진입에는 적용되지만 post-mutation reconciliation의 diverged state까지 닫지 않는다.
- **Impact** - Recovery 실패 뒤 다른 writer나 별도 작업이 target을 변경하면 과거 approval이 새로운 target state를 덮어쓰는 권한처럼 재사용될 수 있다. 이는 candidate-bound approval과 stale-state protection을 우회한다.
- **Required Change** - Reconciliation에서 current partition identity를 구분한다. Expected recovered state면 overwrite를 생략하고 verification을 재개한다. Approved pre-recovery state면 기존 approval의 binding 범위 안에서 recovery를 재개할 수 있다. 둘 다 아니면 target mutation 전에 중단하고 새 candidate validation과 approval을 요구한다. `Diverged reconciliation target` acceptance case를 추가한다.

### F4. Research artifact contract가 snapshot repository 규칙과 어긋난다

- **Severity** - Minor
- **Location** - PR #14 frontmatter, F7 Evidence/Research lifecycle references
- **Evidence** - Reviewed Research는 `type: openspec-rpi`, `category: research`를 사용하고 `research/templates/research.md`를 참조한다. Snapshot의 `research/AGENTS.md`는 shared `inbox/_templates/research.md`를 사용하고 local `research/templates/` copy를 두지 않도록 하며, shared template의 artifact type은 `research`다.
- **Impact** - Runtime safety 문제는 아니지만 Research ownership과 lifecycle 기준을 벗어나고 stale path를 Planning evidence로 남긴다. Artifact 검색·유지보수와 후속 handoff의 해석 비용이 증가한다.
- **Required Change** - Frontmatter를 snapshot Research contract에 맞춰 `type: research`로 정렬하고 legacy `category`를 제거한다. Template/evidence reference는 shared `inbox/_templates/research.md`와 snapshot Research lifecycle owner를 사용한다.

## Validation

| Check | Evidence | Result |
| --- | --- | --- |
| Review snapshot boundary | PR head `acc2733`, `main@22fdfd0` | Pass |
| Foundation phase gate | `docs/development/foundation/readiness.md` | Pass |
| Readiness audit → snapshot behavioral drift | `feea63f...22fdfd0`: source/spec/test 변경 없음 | Pass |
| Research revision currency | `main@22fdfd0` ↔ PR head `acc2733` | Fail — PR head 84 behind / 1 ahead |
| Existing approval binding | `contracts/approval.py`, `recovery/executor.py` | MVP gap confirmed |
| Partition replacement atomicity | `hmda_data/ingestion/partition.py` transaction | Pass |
| dbt artifact preservation | `data_operations/runner.py`, readiness non-gating inventory | Fail |
| Reconciliation diverged-target safety | PR #14 F4, Required Acceptance | Fail — explicit fail-closed rule 없음 |
| Research artifact contract | `research/AGENTS.md`, `inbox/_templates/research.md` | Fail |
| Existing reliability runtime execution | readiness non-gating inventory | Not Verified |

검토는 repository content와 GitHub revision 비교로 수행했다. pytest, dbt build, OpenSpec CLI는 이 Review에서 실행하지 않았다.

## Remaining Risks

- Profile/incident/impact/remediation lifecycle과 approval backfill은 snapshot에서 구현되어 있으나 canonical readiness에서 snapshot execution은 unverified다. MVP의 첫 integration baseline에서 검증해야 한다.
- `data-operations-refactor-runner` OpenSpec change는 snapshot에서 plan approved, tasks `4/4`이며 코드에 반영돼 있지만 active다. MVP change가 같은 runner/capability를 수정한다면 archive하거나 변경 순서를 명확히 해 overlapping ownership을 피한다.
- Dagster orchestration blocker와 freshness semantics는 PR #14의 `volume_drop` recovery slice 범위 밖이므로 MVP entry blocker로 승격하지 않는다.
- 이 Review는 `main@22fdfd0` 이후 runtime drift를 재검증하지 않는다. 후속 Planning은 최신 owning evidence에서 다시 확인해야 한다.

## Follow-up

이 section은 original review verdict를 변경하지 않고 이후 lifecycle만 기록한다.

- PR #14는 stale gate와 dbt artifact safety, 추가 safety/contract 보강을 반영한 뒤 2026-08-08 merge됐다. 따라서 **`PR #14: Revise`는 reviewed head `acc2733`에만 적용**한다.
- Revised Research에는 diverged reconciliation target에서 old approval mutation을 차단하는 rule, run-scoped dbt artifact workspace와 last-known-good 보존, current Research frontmatter/template 정렬이 포함됐다.
- Active Research는 이후 lifecycle에 따라 제거됐고 현재 후속 Research evidence는 `inbox/archive/2026-08-08/reliability-mvp-volume-drop-vertical-slice.md`에 보존돼 있다. 현재 Planning 판단은 이 Review가 아니라 최신 canonical/owning artifact와 재검증된 repository state를 사용한다.

## Verdict

| Decision | Rationale | Route |
| --- | --- | --- |
| **MVP Entry: Pass** | Snapshot에서 Foundation gate는 닫혔고 단일 `volume_drop` slice는 architecture boundary와 맞는다. | Reliability MVP OpenSpec Planning 시작 |
| **PR #14 `acc2733`: Revise** | Stale Foundation gate, dbt artifact safety, reconciliation stale-state gap과 Research contract drift를 수정해야 snapshot 기준 Planning input이 된다. | PR #14 재검증·수정 후 Planning handoff |

MVP의 핵심은 기능 폭을 넓히는 것이 아니라 **`volume_drop` 하나에서 detection → validation → approval → recovery → verification evidence를 안전하게 닫는 것**이다. Snapshot에서 MVP phase-entry를 막는 추가 blocker는 확인되지 않았다. F1~F3은 Planning handoff 전에 닫아야 하는 required finding이며, F2~F3은 recovery correctness safety와 직접 관련된다. F4는 handoff 품질과 artifact lifecycle을 위한 maintenance finding이다.
