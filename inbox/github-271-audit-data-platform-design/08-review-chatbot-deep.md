---
type: review
title: Data Platform Chatbot Deep Review
description: PR #271 테스트 변경의 챗봇 심층 리뷰와 세션 간 지속 검토 상태를 기록합니다.
tags:
  - "capability:test-design"
  - "multi-perspective"
---

# Data Platform Chatbot Deep Review

> [!IMPORTANT]
> **Blocked (independent review gate pending; R2 source/CI revalidated)** — 새 `current_required` 결함은 아직 확정하지 않았습니다. 이는 머지 불가 판정이 아니라 이번 챗봇 리뷰의 검토 범위와 독립 재검증이 아직 닫히지 않았다는 뜻입니다. 로컬 테스트를 직접 실행하지 않았으므로 기존 CI·독립 리뷰 기록을 본 검토의 재현 결과로 간주하지 않습니다.

- **Target** — [PR #271](https://github.com/mols3131d/hmda-data-reliability/pull/271), owning branch의 Inbox.
- **Revision** — base `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`; reviewed code/head `8ef30680eea1c9b6265545f7e913d2e6972ffa36` (2026-10-26 KST 1차 확인). 직전 코드 검토 후 현재 head `f4d09358302a35f46ec85c1cfeb306889be930ed`까지의 차이는 이 리뷰 문서 추가 1건뿐임을 commit compare로 확인했습니다. 이후에도 code/Spec/CI 변경은 다시 비교합니다.
- **Scope** — 변경 test/design 5파일 및 전체 5개 baseline tracked 파일의 감사 보고서, 실제 dbt mart fixture의 결과와 `data-platform-dbt-analytics` 정본 계약을 직접 대조.

## Findings

현재 직접 확인한 범위에서 **확정된 신규 finding 없음**. 이는 PR 전체의 `clear` 또는 merge readiness 검증 완료를 의미하지 않습니다.

## Perspectives

| Perspective | Reviewer / Method | Focus | Assessment and Evidence |
| --- | --- | --- | --- |
| 숫자·Spec 독립성 | 동일 세션 고정값 재계산 | 전체 mart grain·metric | dbt Spec상 action 1/2 승인, 3/7 거절, 6자리 반올림. TX actions 1/2/4 → 3 applications, 2 approvals, rate 0.666667, 유효 numeric 2개 평균 150000/75는 고정 fixture와 일치. `tests/dbt/test_analytics_foundation.py` |
| 실제 경계 | 동일 세션 test diff 검토 | dbt build/test, DuckDB read-only·parser | fake 호출 대신 실제 DuckDB parser와 실제 dbt CLI 실패 노드 집합을 확인하는 경계가 추가됨. `tests/data_platform/test_sql.py`, `tests/dbt/test_analytics_foundation.py` |
| 오류·격리 | 동일 세션 반증 점검 | lock cleanup, artifact identity | 독립 pair bytes와 shared/exclusive lock 테스트가 추가됨. 구현 의존 test assertions의 충분성은 추후 확인 필요 |

## Candidate Decisions

| ID | Perspectives | Candidate | Decision | Rationale | Finding |
| --- | --- | --- | --- | --- | --- |
| C1 | Oracle | approval rate와 numeric-null 기대값이 Spec과 불일치 | Drop | source-independent fixture 산술과 [Spec](../../openspec/specs/data-platform-dbt-analytics/spec.md)의 의미가 일치 | — |
| C2 | 테스트 경계 | SQL escape property가 생산 알고리즘 복사만 검사함 | Drop | 변경된 property는 DuckDB에서 실행해 원래 identifier/literal을 관찰 | — |
| C3 | 결함 검출력 | `dbt test` 실패 노드 4종은 특정 fixture 결합으로 false green 가능 | Open | returncode 1과 unique_id·test metadata 집합을 비교하므로 단순 exit-1 false green은 억제. manifest 결과가 실제 오염을 반영하는지 구현·dbt schema 추가 trace 필요 | — |

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | 정본 dbt analytics Spec 비교 | `openspec/specs/data-platform-dbt-analytics/spec.md`를 현재 main에서 직접 읽고 TX fixture의 수치·null·grain expected를 대조 |
| ✅ Pass | Diff/path 소유권 정적 대조 | test/design 변경 5파일은 `tests/data_platform/**`와 `tests/dbt/**`에 한정. 타 PR의 변경 경로와 중복 없음 |
| ⚪ Not Verified | 현재 source/dbt model의 직접 전체 검토 | 실 구현으로부터의 독립 oracle 및 모델 선언을 추가 추적해야 함 |
| ⚪ Not Verified | dbt CLI/pytest/CI 재실행 | PR의 43 passed / 1 warning 및 CI 주장은 기존 증거이며 이번 세션에서 직접 실행하지 않음 |

## Risks and Limits

- dbt quality test 결과는 `run_results.json`과 manifest node metadata를 전제로 합니다. target/log isolation을 포함한 실제 재실행은 이후 회차에서 확인합니다.
- 공용 Git hook 환경 문제와 cross-domain build/promotion은 #277에서 순차 취합이 필요합니다.

## Continuation

- **State:** `mols-loops deep`; Prepare → RPI Research/Plan/Work/Review 1차(동일 세션의 순차 관점) 완료, 독립 신규 specialist 게이트 및 완전한 contract trace 미완료. 이 기록은 제품/테스트를 수정한 증거가 아니라 리뷰 checkpoint입니다.
- **Next:** `dbt/models`와 schema.yml의 실제 quality configuration을 고정 fixture/4 failure node와 대조하고, DuckDB lock/artifact primitive의 구현 예외 우선순위 및 error context를 점검. 다른 domain 소비자와 연결은 #277로 유지.
- **Revalidation trigger:** main/base, head의 test/source/Spec blob, CI 상태, 새로운 feedback이 바뀌면 기존 판단을 stale로 표시하고 영향을 받는 영역을 다시 조사합니다. 전수 파일 수나 이전 에이전트가 표시한 `clear`를 독립 검증으로 대체하지 않습니다.
- **Boundary:** 이 문서는 비정본입니다. 공유 CI/Git fixture와 교차 도메인 계약은 [#277](https://github.com/mols3131d/hmda-data-reliability/pull/277)에서 선행 PR을 취합한 뒤 검증합니다. 승인·merge·thread resolution은 수행하지 않습니다.

## R2 · 2026-10-26 KST · Source and CI Revalidation

> [!NOTE]
> **이 절은 위 R1의 Open 후보·Not Verified 항목 중 직접 재검증한 부분을 갱신합니다.** 신규 `current_required` 확정 없음. 별도 subagent context의 DualVantage는 이번 runtime에서 수행하지 못했으므로 project-level independent review gate는 여전히 `blocked`이며, 사람의 Ready/approval/merge 판단을 대체하지 않습니다.

- **Research:** `main@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`은 유지. R1 code revision → 현재 head `f4d09358302a35f46ec85c1cfeb306889be930ed` compare는 **Inbox review 1파일 추가만** 포함; test/source/Spec blob은 그대로다. 원래 CI를 현재 코드 검증으로 일반화하기 전, 최신 head의 실제 workflow와 log를 새로 확인했다.
- **Plan:** R1 Open 후보를 실제 source, normative Spec, fixture·oracle에 교차 대조하고 반례가 반박되면 Drop, 별개 ownership/계약 판단이 필요하면 Open으로 유지. 제품·Spec·공용 파일 변경 금지.
- **Review:** 동일 세션에서 oracle/실패·오염/ownership/CI를 순차 관점으로 반증했다. 독립 reviewer가 수행했다고 주장하지 않는다.

### R2 · Data Platform

- **C3 → Drop (bounded):** [실제 dbt failure test](https://github.com/mols3131d/hmda-data-reliability/blob/8ef30680eea1c9b6265545f7e913d2e6972ffa36/tests/dbt/test_analytics_foundation.py#L87-L140)는 raw `source_year=NULL`, mart duplicate grain 및 null grain key를 주입한 뒤 `dbt test`의 returncode=1과 manifest의 실패 node `test_metadata.name`·`column_name`·dependency set을 exact 비교한다. [`dbt_project.yml`](https://github.com/mols3131d/hmda-data-reliability/blob/ea39a4fd6c8f483509cf00a1d1114feb4ef3b686/dbt/dbt_project.yml)는 staging=view, marts=table이다. 따라서 raw 변경은 staging view의 `not_null`을 실제로 오염시키고, mart 직접 변경은 mart `unique/not_null`을 오염시킨다. [source/staging/mart YAML](https://github.com/mols3131d/hmda-data-reliability/tree/ea39a4fd6c8f483509cf00a1d1114feb4ef3b686/dbt/models)은 4개 예상 실패 검사의 선언을 확인시킨다. 단순 exit-code false green 가설은 반박되었다.
- **C4 → Open / follow_up (verification boundary):** 테스트는 현재 모델/YAML 조합의 **정확한 네 실패 node**를 구별하지만, 다른 도메인의 runner가 생성한 run-scoped artifact를 promotion하고 Reliability reader가 동일 pair를 읽는지까지는 관찰하지 않는다. [정본 dbt analytics Spec](https://github.com/mols3131d/hmda-data-reliability/blob/ea39a4fd6c8f483509cf00a1d1114feb4ef3b686/openspec/specs/data-platform-dbt-analytics/spec.md)의 lineage와 현재 dbt grain/metric oracle은 이 PR이 소유하고, **cross-domain adoption/identity**는 #277 소유다. PR #270의 result-only drift 검증과 혼동하지 않는다.
- **Ownership:** 이 PR의 변경 test/design은 `tests/data_platform/**`, `tests/dbt/**` 5개이며 #269/#270/#272와 직접 경로 충돌이 없다. DB·dbt subprocess를 이번 회차 로컬에서 다시 실행하지 않았다.

### Validation and Continuation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | R1→current SHA 및 소유권 정적 비교 | `git compare`의 1 commit, 이 PR의 `review-chatbot-deep.md` 추가만 존재. 최신 main/base `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686` |
| ✅ Pass | 원격 CI Lite 최신 head의 실제 실행 로그 | [Run 40218907289](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40218907289) — **43 passed, 1 warning in 23.98s**; prospective merge checkout, selected tests·Python validation 성공. 이는 GitHub runner의 실행이며 로컬 재실행이 아니다. |
| ⚪ Not Verified | 이번 회차 로컬 pytest·mutant·integration 재실행 | GitHub connector 정적 조회 및 원격 CI log 검토만 수행; 독립 실행 증거 없음 |
| ⚪ Not Verified | 별도 컨텍스트의 독립 DualVantage gate | 별도 reviewer/subagent 실행을 수행하지 못함. 동일 세션의 다관점 대조를 독립 리뷰로 승격하지 않음 |
| ⚪ Not Verified | #277 최종 통합 및 공용 Git hook 영구 수정 | [#277](https://github.com/mols3131d/hmda-data-reliability/pull/277)은 `74ac659d084fadd5e93900b132ef5b995ef8d919`, base `81fe44b2...`의 Draft; #269–#276은 아직 모두 병합 전. 순차 통합 후 재검증 필요 |

**Next transition:** 신규 `current_required`를 만들기 위해 기존 finding을 반복하지 않는다. 다음 Run은 현 PR head와 source/test/Spec blob, CI run을 먼저 비교하고, 독립 specialist 검토가 실제 가능할 때만 independent gate를 진행한다. #277 owner는 기존 감사의 H/F 항목을 참조해 선행 PR이 main에 통합된 **한 revision**에서 current/candidate artifact·approval/recovery·dbt log·Git fixture isolation의 부정 경로를 검증한다. 이 문서 수정 commit은 Inbox-only이며 이 절의 `reviewed head`는 수정 **직전** SHA다. 변경 후 head는 PR에서 다시 확인한다.

## R3 · 2026-10-26 KST · Fresh-Head Challenge and Handoff

> [!NOTE]
> **Research → Plan → Review:** Compared previous R2 head `f4d09358302a35f46ec85c1cfeb306889be930ed` to authoritative head `a06c6093f3ae2afda232d649755987a504cc05c0` and main/base `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`: only this Inbox review changed, so earlier code/Spec/test findings remain revision-applicable. No new PR conversation feedback. The plan was to challenge one unresolved inference against a separate source/test path, keep test-only PR ownership, and validate latest remote CI without claiming local execution. This is same-session multi-perspective analysis, **not** isolated independent review.


### R3 · Data Platform · Lock Oracle Countercheck

- **Candidate C5 — 🔵 Note / Drop:** The conjecture that artifact lock tests use only a fake lock is refuted by [test_artifacts.py](../../tests/data_platform/test_artifacts.py), `test_projection_lock_enforces_shared_and_exclusive_access`: it calls the real [`fcntl.flock` implementation](../../src/hmda_reliability/data_platform/artifacts.py) and changes only the contender to `LOCK_NB` to observe reader/reader and conflicting writer combinations. The source also preserves body failure over unlock failure; separate tests exercise setup/release error translation. These are direct code/test inspections, **not a new local runtime reproduction**.
- **C4 stays Open / follow_up:** Pair-byte identity and real primitive locking do not prove the #270 candidate-to-current promotion plus Reliability consumer sees one consistent integrated state. The existing [#277 interface plan](../github-277-audit-cross-domain-design/00-plan-cross-domain-tests.md) owns that integration after upstream merges. The existing one-warning CI is a Python fork deprecation warning, not a failed test; no evidence here that it causes flakiness.
- **Disposition:** No new confirmed `current_required`; independent specialist gate still **blocked**. Do not promote the 43 scoped dbt/data-platform cases to a cross-domain acceptance claim.

### R3 Validation and Next Transition

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Remote revision and changed-path comparison | `f4d09358302a..a06c6093f3ae` is one Inbox-only commit; no new test/source/Spec diff; domain test file paths do not overlap #269/#270/#271/#272. |
| ✅ Pass | Latest remote CI selected-suite log | [CI Lite 40223438251](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40223438251), job `121259738359`: **43 passed, 1 warning in 24.34s** with selected Python checks success on prospective merge. GitHub runner evidence only. |
| ⚪ Not Verified | This session's local pytest, targeted fault injection, and independent specialist | No local execution or isolated reviewer; earlier run reports are historical evidence, not this run's result. |
| ⚪ Not Verified | [#277](https://github.com/mols3131d/hmda-data-reliability/pull/277) integrated contract test | Still Draft at `74ac659d084fadd5e93900b132ef5b995ef8d919`, initial base `81fe44b2`; prerequisite domain PRs remain unmerged. |

**Next:** Re-check exact head/base/CI before reuse. Follow the candidate-specific owner and counterexample above; run only the narrow relevant fault/alias/integration test in a disposable isolated environment if authorized. Preserve the difference between remote CI success, static inference and independent review. Do not modify shared code/Spec or approve/merge. This reviewed head is the **pre-Inbox-update** SHA; verify the resulting commit changed only this document.


## R4 · 2026-10-26 KST · Negative dbt-Result Oracle Challenge

> [!IMPORTANT]
> **Assessment: blocked for this continuation's independent specialist gate; one new in-scope test-oracle candidate admitted from static evidence, execution pending.** No approval/merge/readiness state was changed. This does not overturn the historical independent review at its earlier revision; it narrows a missed false-green condition for human/test-owner review.

- **Target** — PR #271, `agent/test/audit-data-platform-design`, this Inbox review only.
- **Revision** — prior R3 reviewed head `a06c6093f3ae2afda232d649755987a504cc05c0` → authoritative pre-write head `bf616f2af0272e8b8db61786570f0cb0cef7e37e`; compare shows exactly one Inbox-only commit. `main@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686` remains current. Test/source/Spec changes since R3: none.
- **Scope** — new negative oracle of the changed dbt quality test, canonical dbt quality contracts, other PR lane ownership and prospective-merge CI. No test/source/Spec/shared files edited.

### R4 Candidate Decision

| ID | Severity | Scope relation / disposition | Evidence and counterevidence | Action |
| --- | --- | --- | --- | --- |
| C6 | 🟡 Minor | `acceptance_gap` / **Accept as current_required test-oracle correction (static proof; runtime not verified)** | [Changed quality test](../../tests/dbt/test_analytics_foundation.py), `test_dbt_quality_tests_detect_source_staging_and_mart_violations` (around lines 100–140), requires `dbt test` returncode 1, then selects **only** `status == "fail"` results and compares a **set** of four known failure-node descriptors. If those four `fail` records coexist with an unexpected `status == "error"` result for another dbt node, the set and expected returncode remain unchanged: the test still passes while an unrelated dbt execution error is hidden. This is a deterministic predicate counterexample, **not** a reproduced dbt run or an observed production failure. Existing real dbt subprocess and exact four-node matching refute the broader claim that the test merely checks exit code, but do **not** refute this narrower extra-error case. | Within #271 test ownership, assert no unexpected `error`/unanticipated non-success status in all `run_results["results"]`, preserving the four intended `fail` descriptors. Negative control: inject one additional `error` record into a disposable result artifact and require the test to fail for this reason; rerun real dbt quality test and scoped suite. Do not edit the model/Spec or move this internal oracle to #277. |

**Research → Plan → Review:** Cross-checked the new test diff, actual `_run_dbt(... expected_returncode=1)` boundary and the prior R2/R3 four-node declaration review. The plan was to falsify “exact four failures” by adding an orthogonal `error` status; the actual filter ignores that status. This is a same-context logic inspection, not an isolated specialist or fault-injection execution. The canonical [dbt analytics Spec](../../openspec/specs/data-platform-dbt-analytics/spec.md) defines model/quality semantics; it does not authorize treating an unrelated dbt execution error as a passing negative test.

### R4 Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Revision/ownership static comparison | `a06c6093..bf616f2a`: only this Inbox artifact changed; #269/#270/#272 modified test paths remain disjoint. |
| ✅ Pass | Remote prospective-merge CI log inspection | [CI Lite 40228402935](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40228402935), job `121274696484`, checkout merge `c66a77a3e3f81387e218c4b1d78a85fd35a07eba` of head `bf616f2a` into base `ea39a4fd`: **43 passed, 1 warning in 28.36s**; Python checks succeeded. The warning is a multiprocessing `fork` deprecation warning. This CI does not inject C6's extra-error counterexample. |
| ⚪ Not Verified | Local pytest, extra-error artifact injection, mutation experiment, independent DualVantage gate | None executed in this continuation; the predicate counterexample is static, not a test-run result. |
| ⚪ Not Verified | #277 integrated contract gate | #277 remains Draft at `74ac659d084fadd5e93900b132ef5b995ef8d919`; its initial base `81fe44b2` is one commit behind current main `ea39a4fd`, and upstream PRs are not integrated. |

**Next:** Test owner should challenge C6 with a disposable extra-`error` `run_results` case and, if confirmed, strengthen only the #271-owned negative oracle. Retain prior C1–C3/C5 Drop and C4 cross-domain follow-up. Recompare the resulting Inbox-only commit/head and CI; no human review, approval, merge or thread resolution is implied.

## R5 · 2026-10-26 KST · Extra-Error Counterexample Reachability Check

> [!NOTE]
> **Handoff / independent review pending.** R4 C6의 정적 false-green 논리는 유지하되, dbt CLI의 exit-code 조건을 명시해 실제 실행 가능성에 관한 과잉 확신을 제거합니다. 제품·테스트·Spec은 수정하지 않았습니다.

- **Revision:** R4 pre-write `bf616f2af0272e8b8db61786570f0cb0cef7e37e` → authoritative pre-write `3a5271bcdcc96d37b907c3bae1dc97e6a1af6676`: 이 Inbox만 변경된 단일 commit. `main/base@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`; test/source/Spec 변경 없음.
- **Research → Plan → Review:** [실제 dbt quality test](../../tests/dbt/test_analytics_foundation.py)와 같은 파일의 `_run_dbt` helper를 함께 확인. 이전 C6가 제시한 `run_results`의 예상 네 `fail` + 추가 `error`가 **returncode=1일 때만** assertion을 통과한다는 필요조건을 재확인했습니다. `_run_dbt`는 exit 1이 아닌 경우 먼저 실패시키므로 모든 dbt error가 무조건 false green이라는 주장은 **Drop**입니다.

| ID | Severity | Decision / Evidence | Next |
| --- | --- | --- | --- |
| C6 narrowed | 🟡 Minor | **Keep current_required test-oracle gap (static), runtime reachability unresolved.** `result["status"] == "fail"` 필터와 descriptor **set** equality는 추가 `error`를 무시합니다. 다만 helper가 `result.returncode == 1`을 먼저 요구하므로 **CLI exit=1 + 예상 네 fail + 추가 error**의 결합이 필요합니다. Exit 2 등 다른 코드면 test가 실패한다는 safeguard를 반영. 실제 dbt가 이 조합을 반환하는지는 검증하지 않았습니다. | #271 test owner: artifact 수준에서 exit=1 전제의 추가 error를 주입해 oracle false green을 검증하고, 전체 result의 예상 외 error/non-success를 거부하도록 강화. 실제 dbt 실행에서 해당 결합의 reachability도 별도 확인; 불가능하다는 근거가 나오면 disposition 재평가. |
| C4 | 🔵 Note | **Keep cross-domain follow_up:** run-scoped candidate → current promotion → Reliability consumer의 동일 identity는 domain test 결과만으로 증명되지 않음. | 선행 병합 후 #277 E2E owner. |

### R5 Validation and Continuation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | R4→head, helper/quality-oracle 정적 대조 | 단일 Inbox-only commit; changed tests `tests/data_platform/**`, `tests/dbt/**`로 다른 세 PR와 비중복. |
| ✅ Pass | 최신 **원격** prospective-merge CI log | [CI Lite 40232562483](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40232562483), job `121287205029`: **43 passed, 1 warning in 25.20s**, Python checks 성공. Extra-error injection은 수행하지 않음. |
| ⚪ Not Verified | 로컬 dbt fault injection, mutant, 독립 specialist | 이번 회차 미실행. Exit-code 조합은 실험 전 조건부 반례. |
| ⚪ Not Verified | #277 통합·승인 | #277은 prerequisite-blocked Draft. |

**Next:** C6를 실제 dbt exit/result 조합으로 반증하거나 수용하고, 현 PR 소유 테스트만 보강할지 owner가 결정. 원격 CI success를 통합 성공으로 확대하지 않음. Reviewed head는 Inbox 갱신 전 SHA입니다.
