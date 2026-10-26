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

## R6 · 2026-10-26 KST · Negative Oracle Predicate Counterexample

> [!IMPORTANT]
> **Research → Plan → Review / handoff.** R5 C6를 실제 dbt 실행 결과라고 오인하지 않고 **검사 predicate 자체의 false-green**으로 한정해 별도 Python 계산으로 재확인했습니다. PR 테스트·Spec·model은 수정하지 않았습니다.

- **Revision:** R5 reviewed pre-write `3a5271bcdcc96d37b907c3bae1dc97e6a1af6676` → authoritative pre-write `792363246ea056814d4c5cff2b7a85e9cf00cf67`: 1 Inbox-only commit. `main/base@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686` 유지; code/test/Spec unchanged, no new PR feedback.
- **Location/contract:** [changed test](../../tests/dbt/test_analytics_foundation.py) `test_dbt_quality_tests_detect_source_staging_and_mart_violations`의 `status == "fail"` 필터와 descriptor `set` equality, 동일 파일 `_run_dbt(expected_returncode=1)`; [dbt Spec](../../openspec/specs/data-platform-dbt-analytics/spec.md) `Analytics quality tests`.
- **C6 · 🟡 Minor · Keep provisional current_required (oracle predicate), real dbt reachability Not Verified:** 별도 Python에서 테스트의 동일한 `failed_nodes` 필터·descriptor set 계산을 **예상 네 `fail` + 추가 `error`**로 평가한 결과 `expected_set == observed_set`은 **True**, 추가 `error`는 여전히 결과에 남았습니다. 이는 검사 predicate의 deterministic counterexample이며, **repository pytest/dbt subprocess를 실행한 결과가 아닙니다**. 기존 `expected_returncode=1` safeguard는 유효: exit 2면 이 테스트는 먼저 실패합니다. 실제 dbt가 **exit 1 + 네 fail + error** 조합을 생성하는지는 아직 미확인입니다. 불가능하다는 dbt-version-specific 근거가 나오면 current_required disposition을 재평가해야 합니다.
- **Decision:** R4의 더 넓은 “exit code만 검사한다”는 가설은 Drop 유지. 전체 `run_results["results"]`에서 예상 외 `error`/non-success를 거부하되 정확한 네 expected `fail`의 identity를 보존하는 가장 작은 test-only 수정이 제안됨. `#277`로 내부 oracle을 넘기지 않음. 기존 C4 promotion↔consumer identity는 별도의 #277 integration handoff.

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | R5→R6 revision and ownership check | `3a5271bc..79236324` Inbox-only; changed `tests/dbt/**`와 다른 PR test 경로 비중복. |
| ✅ Pass | Standalone Python predicate reproduction | 예상 네 fail + 추가 error에서도 set equality True; **dbt exit/result runtime 실험 아님**. |
| ✅ Pass | Remote current-head prospective-merge CI | [CI Lite 40238120713](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40238120713): **43 passed, 1 fork deprecation warning in 31.40s**, 선택 Python checks 성공. 추가 error 주입 미포함. |
| ⚪ Not Verified | 실제 dbt exit=1/error 결합, repository pytest, mutation/fault injection, 독립 specialist | 수행하지 않음. |

**Next:** #271 test owner는 disposable run-results 추가-error oracle을 먼저 실패시키고 실제 dbt-version/adapter에서 `exit=1`과 `error`의 동시 발생 가능성을 확인한 뒤 보강/드랍 결정. #277은 선행 병합 후 integrated promotion↔Reliability 소비 경계를 검증. Reviewed head는 Inbox 갱신 전 SHA입니다.

## R7 · 2026-10-26 KST · dbt Artifact Provenance and Oracle Countercheck

> [!IMPORTANT]
> **Research → Plan → Review / handoff.** R6 C6의 `fail`-only predicate를 새로운 finding으로 반복하지 않고, 실제 `dbt` 실행·artifact provenance 및 공식 run-results 계약에서 반증 가능한 전제를 분리했습니다. **dbt subprocess 실행은 하지 않았습니다.**

- **Revision:** R6 pre-write `792363246ea056814d4c5cff2b7a85e9cf00cf67` → R7 authoritative pre-write `2c1876c672c2437fc2aa3bd8a03971b9a5f19c7c`: 이 Inbox만 변경한 1 commit. `main/base@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`; code/test/Spec 불변, PR comments 0.
- **Contract/locations:** [dbt analytics Spec](../../openspec/specs/data-platform-dbt-analytics/spec.md) `Analytics quality tests`; [changed test](../../tests/dbt/test_analytics_foundation.py) L87–166; [dbt 공식 run-results 문서](https://docs.getdbt.com/reference/artifacts/run-results-json) `results[*].unique_id/status` (2026-10-16 갱신). 공식 계약은 각 실행 노드의 `status`에 success/failure/error를 구별하며, artifact에는 **실행된 노드만** 포함한다고 명시합니다.

| ID | Severity | Decision / scope relation | Evidence / counterevidence | Next |
| --- | --- | --- | --- | --- |
| C6 | 🟡 Minor (conditional) | **Keep provisional `current_required` for test-only oracle; runtime reachability unresolved** | `test_dbt_quality_tests_detect_source_staging_and_mart_violations`는 `_run_dbt(..., expected_returncode=1)` 뒤 `status == 'fail'`만 descriptor set으로 비교합니다. 공식 run-results 계약은 `error`를 `fail`과 다른 status로 기록합니다. 따라서 **네 예상 fail + 추가 error + CLI exit=1**이면 추가 error가 필터에서 소실된다는 R6 반례는 유효. 그러나 현재 dbt-core/duckdb 버전에서 이 결합이 실제 생성되는지, 별도 error가 exit 2를 만드는지 직접 확인하지 못했습니다. | Disposable 실제 dbt run에서 `error` node와 네 `fail`의 공존·exit code를 관찰하고, 가능하면 모든 unexpected non-success를 거부하는 최소 test-only oracle을 설계. |
| C7 | 🔵 Note | **Drop / stale artifact false-green 가설** | `tmp_path`의 독립 DB와 `--target-path tmp_path/dbt-target`를 사용합니다. 선행 `build` artifact가 남아도 이후 `dbt test`가 실패 결과를 작성하지 않으면 이전 build의 model-success 결과로는 네 expected `fail` set equality를 충족할 수 없습니다. 따라서 **이전 run_results만으로 C6의 false-green이 성립한다**는 가설은 코드의 필터/expected set이 반박. 단, 실제 dbt artifact overwrite behavior의 runtime 검증은 아님. | 새 stale-artifact defect로 등록하지 않음. |

### R7 Validation and Continuation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | R6→R7 head 및 source/Spec/test/공식 artifact schema 정적 대조 | `79236324..2c1876c6` Inbox-only; #269/#270/#272의 변경 테스트와 경로 충돌 없음. |
| ✅ Pass | 원격 prospective-merge CI의 실제 selected test log | [CI Lite 40242540040](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40242540040), merge `44115e3` into `ea39a4fd`: **43 passed, 1 warning in 25.68s**; 예상 외 error fault 미포함. |
| ⚪ Not Verified | dbt `exit=1 + error` 실제 조합, mutation/fault injection, 로컬 pytest, 독립 specialist | 본 회차 미실행. 공식 status schema만으로 특정 CLI exit code를 확정하지 않음. |
| ⚪ Not Verified | #277 integrated promotion↔consumer | 선행 PR 미병합; 별도 cross-domain acceptance 필요. |

**Next:** #271 test owner가 dbt-core 1.12+ / DuckDB 실제 adapter에서 controlled `error` node를 만들고 exit/result artifact를 함께 기록해 C6의 `current_required` admission을 확정/기각. `error`를 무시하는 predicate는 이미 정적 반례가 있으나 exit 조건을 생략해 실제 false green이라고 단정하지 않습니다. #277에는 내부 oracle 변경을 넘기지 않음. 이 절의 head는 **Inbox 갱신 전** SHA입니다.

## R8 · 2026-10-26 KST · In-Repository Fifth-Error Falsifier

> [!IMPORTANT]
> **Research → Plan → Review / handoff.** R7의 임의 `run_results` record 가설을 실제 dbt project의 **다섯 번째 test node**와 연결해 반증 가능성을 높였습니다. dbt 실행이나 CLI exit-code 관측은 하지 않았습니다.

- **Revision:** R7 reviewed pre-write `2c1876c672c2437fc2aa3bd8a03971b9a5f19c7c` → authoritative R8 pre-write `dd46719155bfdd33ea90e9b5aa3caba3a81ec03a`; 비교는 이 Inbox만 바뀐 1 commit. `main/base@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`, tests/models/Spec 불변, PR comments 0.
- **Contract/locations:** [changed quality test](../../tests/dbt/test_analytics_foundation.py) `test_dbt_quality_tests_detect_source_staging_and_mart_violations` / `_run_dbt`; [source tests](../../dbt/models/sources.yml), [staging tests](../../dbt/models/staging/schema.yml), [mart tests](../../dbt/models/marts/schema.yml); [dbt analytics Spec](../../openspec/specs/data-platform-dbt-analytics/spec.md).

| ID | Severity | Decision / scope relation | Evidence / disconfirmation | Next |
| --- | --- | --- | --- | --- |
| C6 refined | 🟡 Minor (conditional) | **Keep provisional `current_required` test-oracle candidate; real CLI reachability unresolved** | 정본 dbt YAML에는 source **5**, staging **5**, mart **8**개의 선언된 data test가 있습니다. 따라서 예상 네 `fail`만 실행 가능한 전부라는 반론은 **Drop**입니다. 구체적인 반례 fixture: 기존 raw `source_year=NULL` 및 mart `mart_grain_key=NULL`/NY 중복을 만든 **다음**, mart의 독립 `application_count` column을 `ALTER TABLE marts.mart_hmda_loan_outcomes DROP COLUMN application_count`로 제거합니다. 기존 네 not-null/unique 검사는 다른 column에 의존하므로 유지될 것으로 예상되지만 `application_count`의 `not_null` 검사는 SQL error를 낼 수 있습니다. Test는 `status == 'fail'` 네 descriptor만 비교하므로 **CLI exit=1 + 추가 error result**라면 여전히 false green입니다. 실제 dbt-core/duckdb adapter가 이 조합을 `run_results`에 남기고 exit 1을 반환하는지 미실행; 이 전제가 반박되면 disposition 재평가. | Disposable DB에서 기존 3 mutations 뒤 위 `DROP COLUMN`을 추가해 `dbt test`의 exact exit/status/unique_id를 기록. `error`와 네 `fail` 공존·exit 1이면 #271-owned test oracle을 전체 unexpected non-success 거부로 보강하고 mutant red→green 확인. |
| C8 | 🔵 Note | **Drop / only-four-tests objection** | 실제 YAML inventory가 18개 test node를 선언합니다. 다른 14개가 있으므로 네 실패 descriptor가 모든 node를 망라한다고 해석할 수 없습니다. 다만 선언 수만으로 extra-error runtime 도달성을 증명하지는 않습니다. | 중복 blocker 등록 금지. |

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | R7→R8 head, YAML node inventory, test predicate 정적 대조 | 한 Inbox-only commit; 5+5+8 declared tests, 기존 네 실패와 별개 `not_null(application_count)` 확인. |
| ✅ Pass | 최신 **원격** prospective-merge CI | [CI Lite 40247127374](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40247127374): merge `17dbf2f1e9e1a00119d19487090035e9de046969`, `tests/data_platform tests/dbt` **43 passed, 1 fork deprecation warning in 25.33s**. 다섯 번째 error는 주입되지 않음. |
| ⚪ Not Verified | `DROP COLUMN` 실제 DuckDB/dbt test 실행, exit 1+error 결합, 원본 pytest, 독립 specialist | 로컬 dbt/duckdb 설치·repository checkout 없이 직접 실행하지 못함. |
| ⚪ Not Verified | #277 integrated promotion↔consumer | 선행 PR 미병합. 내부 quality oracle은 #271 owner, integration identity는 #277 owner. |

**Next:** 제시한 SQL corruption을 격리 DB에서 실행해 C6의 도달성을 결정하고, exit/status가 반례를 거부하면 C6의 `current_required` 분류를 낮추거나 Drop. 정본 Spec·dbt model/공용 설정은 수정하지 않으며 갱신 후 head/CI를 재확인합니다.

## R9 · 2026-10-26 KST · dbt Error Oracle Admission Recheck

> [!IMPORTANT]
> **Research → Plan → Review / handoff.** R8 C6의 추가 error 반례를 dbt model materialization과 공식 artifact contract로 재검토했습니다. 실제 dbt 실행 결과가 없으므로 기존의 **provisional current_required**는 확정 finding이 아닌 **unknown (runtime reachability 미확인)**으로 정정합니다. 후보 기각은 아닙니다.

- **Revision:** R8 pre-write dd46719155bfdd33ea90e9b5aa3caba3a81ec03a → authoritative pre-write 4357a6838966e0129e16b305aa96ab9e404d5ba5: GitHub compare 결과 Inbox 한 파일만 변경한 1 commit. main/base ea39a4fd6c8f483509cf00a1d1114feb4ef3b686 유지, changed tests/models/Spec 불변, PR feedback 0.
- **Research:** [변경 quality test](../../tests/dbt/test_analytics_foundation.py) L87–166는 build 이후 raw/mart를 오염시키고 **dbt test만** 재실행하며 status == "fail"인 네 descriptor만 set으로 비교합니다. [dbt project](../../dbt/dbt_project.yml)는 staging을 view, mart를 **table**로 materialize합니다. 따라서 R8의 ALTER TABLE marts.mart_hmda_loan_outcomes DROP COLUMN application_count가 dbt test 시 자동으로 복구된다는 반론은 현 helper/config와 맞지 않습니다. [mart YAML](../../dbt/models/marts/schema.yml) L20–22에는 독립 not_null(application_count) node가 있습니다. [정본 Spec](../../openspec/specs/data-platform-dbt-analytics/spec.md) L46–53는 model contract 위반을 성공으로 보고하지 않도록 요구합니다.
- **Plan:** 네 기존 fail 유지 + 다섯 번째 error + CLI exit=1을 격리 dbt/DuckDB에서 **동시에** 관측할 때만 실제 false green으로 인정합니다. 제품/Spec/YAML 및 다른 PR 테스트는 수정하지 않습니다.

| ID | Severity | Disposition / ownership | Evidence / falsifier | Next |
| --- | --- | --- | --- | --- |
| C6 | 🟡 Minor **if reachable** | **Unknown; not confirmed current_required** / #271 test owner | [dbt 공식 run-results 계약](https://docs.getdbt.com/reference/artifacts/run-results-json?version=1.12)은 fail과 error를 구별합니다. 현 predicate는 error를 버리므로 **가정된 exit=1**에서는 네 fail + 추가 error가 있어도 set equality가 참입니다. 하지만 실제 dbt-core/duckdb가 해당 조합을 반환하는지 미실행입니다. CLI exit=2이거나 네 fail 중 하나가 사라지면 현재 test가 이미 거부할 수 있습니다. | 실제 DROP COLUMN fault 후 returncode, results[*].status/unique_id, 네 fail 존재를 함께 기록. False green 재현 시 unexpected non-pass 거부하는 test-only oracle 수정과 red→green; 불가능하면 C6 Drop/하향. |
| C9 | 🔵 Note | **Drop / mart auto-rebuild objection** | test helper는 build 재실행 없이 test만 호출하고 mart는 table입니다. 따라서 자동 재생성으로 반례가 사라진다는 가설은 반박되나 exit/error 조합은 여전히 미증명입니다. | 중복 결함으로 등록하지 않음. |

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | R8→head compare 및 test→dbt materialization→YAML→Spec 정적 대조 | Inbox-only, test command, mart table, error filter 확인. |
| ✅ Pass | **원격** prospective-merge CI | [CI Lite 40251455386](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40251455386): merge f13ee134971b7b4cb5533d477d3c57890b954458, **43 passed, 1 warning in 33.53s**; 추가 error 미주입. |
| ⚪ Not Verified | 실제 dbt error+exit 결합, 로컬 pytest, 독립 specialist | 원본 checkout 및 dbt/duckdb 실행 환경이 없어 미실행. 정적 근거를 runtime pass로 표시하지 않음. |
| ⚪ Not Verified | #277 통합 | #269–#276 미병합 Draft, #277 최초 base 81fe44b2, 통합 미실행. |

**Next:** C6의 unknown을 실제 dbt CLI returncode + node status 실험으로 먼저 닫습니다. #277에는 promotion→Reliability consumer identity와 공용 CI 경계만 인계하고 내부 predicate 변경은 #271 test owner가 결정합니다. 이 절의 SHA는 갱신 전; 갱신 후 head/CI 별도 확인. 승인·Ready·merge 변경 없음.

## R10 · 2026-10-26 KST · SQL Parser Negative Controls and Scope

> [!NOTE]
> **Research → Plan → Review / continuation.** R9의 dbt extra-error 미확정 후보를 재서술하지 않고, 변경된 SQL quoting test가 단순 escape 문자열 비교를 넘어 실제 parser 결과로 injection 회귀를 구별하는지 반증했습니다.

- **Revision:** R9 reviewed pre-write `4357a6838966e0129e16b305aa96ab9e404d5ba5` → authoritative R10 pre-write `b8aa35575bf85573130d8a0316d3d2bc5fb4a653`: GitHub compare는 이 Inbox만 변경한 1 commit. `main/base@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`; test/source/Spec 불변, PR discussion 0.
- **Research / implementation:** [변경 SQL test](../../tests/data_platform/test_sql.py) L16–78은 `quote_identifier`/literal의 quote escaping과 empty/NUL identifier 거부를 확인하며, `@example('loan"; SELECT 99; --')` 및 `@example("borrower's file'; SELECT 99; --")`와 Hypothesis generated text를 **실제 DuckDB parser**에 전달합니다. Column name/row value가 입력 원문과 같고 query 결과가 정확히 `(7,)` 또는 `(value,)`인지 검사합니다. [구현](../../src/hmda_reliability/data_platform/sql.py)에서 identifier는 double quote, literal은 single quote를 escape합니다.
- **Plan / challenge:** `quote_identifier`에서 double-quote escape를 빼거나 `quote_string_literal`에서 single-quote escape를 빼는 mutant는 명시적 injection payload의 parser/value oracle을 깨야 합니다. 단순 `startswith('"')` 같은 약한 assertion만 있다는 가설은 반박됩니다. **동적 사용자 값의 parameter binding**은 source docstring이 별도로 요구하는 호출자 계약이며 이 helper의 고정 literal test가 이를 전체 검증한다고 주장하지 않습니다.

| ID | Severity | Disposition / scope relation | Evidence / counterevidence | Next |
| --- | --- | --- | --- | --- |
| C10 | 🔵 Note | **Drop / SQL quoting test가 문자열 형태만 확인한다는 가설** | 실제 DuckDB parser 및 반환된 식별자/원문 값·row assertion이 있고 명시적 injection payload 두 종류를 포함합니다. | 같은 quote-escape negative test 중복 추가 없음. |
| C6 | 🟡 Minor if reachable | **Keep prior unknown / #271 test owner, not confirmed current_required** | R9의 dbt `fail` 네 개 외 추가 `error`를 무시할 가능성은 별개. CLI exit=1+네 fail+추가 error의 **동시 도달성은 미실행**입니다. | 격리 DB의 mart column corruption 후 dbt CLI returncode와 전체 node status를 기록해 검출 여부를 판정. |

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | R9→R10 head, SQL test→implementation 정적 반증 | Inbox-only 1 commit; property/example와 실제 parser oracle 확인. |
| ✅ Pass | **원격** R10 pre-write prospective-merge CI | [CI Lite 40256208247](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40256208247), job `121358482295`: `TARGETS=tests/data_platform tests/dbt` **43 passed, 1 fork warning in 31.78s**; 선택 Python checks 성공. dbt extra-error는 미주입. |
| ⚪ Not Verified | 이번 회차 로컬 DuckDB/dbt/pytest, SQL mutant 실행, extra-error 조합, 독립 specialist | 미실행. |
| ⚪ Not Verified | #277 promotion↔Reliability consumer 및 공용 hook/CI 통합 | 선행 PR 미병합, #277 Draft. |

**Next:** C10 Drop. C6은 실행 가능한 dbt status/exit 반례가 확보될 때만 분류를 높이거나 Drop합니다. #277은 내부 dbt quality predicate가 아니라 cross-domain promotion/consumer identity를 소유합니다. 이 절의 SHA는 **Inbox 갱신 전** head이며 Ready·approval·merge는 변경하지 않습니다.

## R11 · 2026-10-26 KST · Projection Lock Symlink Truncation Counterexample

> [!IMPORTANT]
> **Research → Plan → Review / continuation.** R10 SQL parser 및 기존 dbt C6와 독립적인 **lock-file path contamination**을 발견했습니다. 원본 package 실행 없이 표준 라이브러리의 같은 파일 open 동작만 임시 경로에서 재현했으므로 실제 end-to-end 결함으로 과장하지 않습니다.

- **Revision:** R10 reviewed pre-write `b8aa35575bf85573130d8a0316d3d2bc5fb4a653` → authoritative R11 pre-write `209ee9842dfb9c7543aab1f7c1c23f4f8a5c65dc`; GitHub compare Inbox-only 1 commit. `main/base@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`, source/test/Spec 불변, PR discussion 0.
- **Locations:** [primitive](../../src/hmda_reliability/data_platform/artifacts.py) `artifact_projection_lock` (around L55–90) uses `(directory / ".artifact-promotion.lock").open("w")` **before** `fcntl.flock`. [변경 테스트](../../tests/data_platform/test_artifacts.py) (L83–200)는 real OS shared/exclusive contention, mkdir/unlock error, body-error priority를 검증하지만 pre-existing lock-file symlink는 주입하지 않습니다. [consumer](../../src/hmda_reliability/data_operations/incident_lifecycle.py)도 no-detection case에서 shared lock을 엽니다.
- **Counterexample and impact:** `directory/.artifact-promotion.lock -> unrelated-evidence.txt` symlink와 대상 파일 `DO-NOT-MODIFY` bytes를 준비하고 **별도 disposable Python 표준 라이브러리 probe**에서 `Path.open("w")`를 호출하니 외부 파일 bytes가 `b""`로 변했습니다. 이는 `flock` 성공 여부와 무관하게 open 시점에 발생합니다. 따라서 symlink가 이미 존재한다면 read-only consumer도 외부 파일을 손상시킬 수 있습니다. **원본 repository module/pytest는 실행하지 않았고**, 실제 배포 경로에서 공격자 또는 다른 프로세스가 lock symlink를 배치할 수 있는지는 확인되지 않았습니다.
- **Counterevidence:** 정상 임시 directory에서 기존 OS lock test가 확인하는 cooperative reader/writer 직렬화는 여전히 유효합니다. Symlink 위험은 해당 정상 lock contention의 실패를 의미하지 않습니다. 현재 정본 [Data Platform DuckDB Spec](../../openspec/specs/data-platform-duckdb-access/spec.md)의 DB mutation lock과 artifact projection lock을 혼동하지 않습니다.

| ID | Severity | Disposition / scope relation | Evidence and next |
| --- | --- | --- | --- |
| C11 | 🟠 Major **if contaminated path is reachable** | **Accept as conditional pre-existing source integrity risk / follow_up; not #271 test-only current_required** | Symlink-following `open("w")`가 외부 파일을 truncate. Data Platform source owner가 trust model과 lock-file creation policy를 결정한 뒤, disposable external sentinel의 exact bytes를 검증하는 component negative test 및 consumer integration oracle을 선택. 무조건적인 symlink rejection이 기존 contract를 깨는지도 확인. |
| C6 | 🟡 Minor if reachable | **Keep prior unknown / #271 test owner** | dbt 네 `fail` 외 추가 `error` + exit=1의 실제 조합은 여전히 미실행; 이 finding으로 대체하지 않음. |

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | R10→R11 head, primitive/test/consumer 및 Spec 정적 대조 | Inbox-only 1 commit; 네 PR 변경 test 경로 비중복. |
| ✅ Pass | **로컬 disposable stdlib-only symlink open probe** | `Path.open("w")` 후 unrelated sentinel bytes `b"DO-NOT-MODIFY" → b""` 관측. **원본 `artifact_projection_lock` 또는 pytest 미실행**. |
| ✅ Pass | **원격** 현재 head prospective-merge CI | [CI Lite 40261545409](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40261545409): `tests/data_platform tests/dbt` **43 passed, 1 fork warning in 32.12s**, selected Python 및 Markdown checks 성공; 2026-10-26 02:57 UTC 완료. |
| ⚪ Not Verified | 원본 primitive symlink fault, 로컬 DuckDB/dbt/pytest, extra-error C6, 독립 specialist, #277 통합 | 미실행. CI Markdown 검사는 PR의 non-Inbox `test_analytics_foundation.design.md` 때문이며 `inbox/**`는 classifier에서 제외. |

**Next:** C11은 Data Platform source owner에게 좁게 인계하고 #270 lifecycle consumer oracle과 동일 root cause로 연결. 현재 PR의 test-only scope를 source 수정으로 임의 확장하지 않습니다. C6은 dbt CLI status/exit 실험이 우선이며 #277은 실제 projection→consumer integration만 담당. 승인·Ready·merge 미수행.

## R12 · 2026-10-26 KST · Current Projection Self-Corruption via Lock Symlink

> [!IMPORTANT]
> **Research → Plan → Review / strengthened C11 impact.** R11의 unrelated external sentinel truncation을 반복하지 않고, **lock symlink가 보호 대상인 current manifest 자체를 가리키는 반례**로 영향 범위를 좁혔습니다. 새 root cause를 추가하지 않습니다.

- **Revision:** R11 reviewed pre-write `209ee9842dfb9c7543aab1f7c1c23f4f8a5c65dc` → authoritative R12 pre-write `15fc014fa3e53f555a42da9d20fe03e5f38f848f`; GitHub compare Inbox-only 1 commit. `main/base@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`, tests/source/Spec 불변, PR feedback 0.
- **Contract / code:** [primitive](../../src/hmda_reliability/data_platform/artifacts.py) `artifact_projection_lock` (around L55–90)는 `directory.mkdir` 후 `.artifact-promotion.lock.open("w")`를 **flock 전** 수행합니다. 같은 모듈 `artifact_projection_id`는 manifest/results bytes를 하나의 current pair identity로 해시합니다. [changed lock tests](../../tests/data_platform/test_artifacts.py) L81–200은 정상 OS shared/exclusive contention과 typed errors를 검증하지만 pre-existing symlink는 주입하지 않습니다. DB mutation lock과 projection lock은 다른 primitive입니다.
- **Disposable falsifier (actually executed):** 임시 디렉터리에 `manifest.json` 58 bytes와 `run_results.json`을 쓰고 `.artifact-promotion.lock -> manifest.json` symlink를 생성했습니다. Python stdlib `with lock.open("w"): pass` 후 **manifest 58→0 bytes**, results unchanged, length-prefixed pair SHA-256 identity **변경**을 관측했습니다. 이는 정상 read lock의 성공 여부와 무관한 open side effect입니다. **원본 repository 모듈/pytest 실행 아님**; 실제 공격자·외부 프로세스의 symlink 배치 가능성은 미확인입니다.
- **Counterevidence:** 현재 정상 경로의 lock 파일은 일반 파일로 생성되며, R11의 정상 reader/writer lock CI 성공은 여전히 유효합니다. 따라서 임의 운영 환경에서 발생한다고 단정하지 않고 path trust boundary가 먼저 결정되어야 합니다.

| ID | Severity | Disposition / scope relation | Evidence and next |
| --- | --- | --- | --- |
| C11 refined | 🟠 Major **if contaminated path reachable** | **Keep conditional pre-existing source integrity risk / `follow_up`; not #271 test-only `current_required`** | 외부 파일 손상뿐 아니라 **current last-known-good projection 자체가 손상**될 수 있습니다. Data Platform source owner가 lock file symlink/no-follow 및 existing-lock compatibility 정책을 결정하고, 실제 primitive를 임시 manifest pair로 호출해 both-file bytes·pair identity·error/lock semantics를 확인. 정책이 승인되면 component negative test. #270 lifecycle consumer는 같은 root의 integration oracle만 소유. |
| C6 | 🟡 Minor if reachable | **Keep prior `unknown` / #271 test owner** | dbt `exit=1` + 네 `fail` + 추가 `error` 동시 도달성은 여전히 미실행; CI green으로 Drop/Accept하지 않음. |

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | R11→R12 revision 및 primitive/test/consumer/ownership 정적 대조 | Inbox-only 1 commit, 네 PR exclusive test 경로 교집합 없음. |
| ✅ Pass | Disposable **stdlib-only** manifest-symlink + pair hash probe | Manifest 58→0 bytes, results unchanged, identity changed; 원본 모듈 검증 아님. |
| ✅ Pass | **원격** current-head prospective-merge CI | [CI Lite 40266178841](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40266178841): merge `ee2b34b8` (base `ea39a4fd` + head `15fc014f`), `tests/data_platform tests/dbt` **43 passed, 1 warning in 31.21s**. Symlink/extra-error fault 미포함. |
| ⚪ Not Verified | 원본 artifact primitive fault, dbt C6 CLI status/exit, local pytest, 독립 specialist, #277 integration | 이번 회차 미실행. |

**Next:** C11을 조건부 source risk로 유지하고 Data Platform owner가 실제 lock-path threat model을 판정할 때만 수정 범위를 결정합니다. #270에는 no-incident consumer sentinel oracle을 연결하고 #277에는 promotion→consumer identity만 인계. Ready·approval·merge 변경 없음.
