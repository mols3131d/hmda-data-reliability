---
type: review
title: Reliability Chatbot Deep Review
description: PR #272 테스트 변경의 챗봇 심층 리뷰와 세션 간 지속 검토 상태를 기록합니다.
tags:
  - "capability:test-design"
  - "multi-perspective"
---

# Reliability Chatbot Deep Review

2026-10-27 원격 동기화 후 현재 판정·리뷰 출처·후속 owner는 [통합 대조표](02-review-current/README.md#review-reconciliation)에서 확인한다. 아래 R15와 R1–R13의 판정·실행 한계는 당시 revision의 기록으로 보존한다. 이번 정리는 새 독립 리뷰나 runtime 재현을 추가하지 않는다.

> [!IMPORTANT]
> **Current adjudication · R15 (2026-10-27 04 KST): 확인한 범위의 새 `current_required` 없음.** Normal-case 역명제는 정본 요구가 아니며, Markdown cell 오염은 **기존 reporter의 조건부 위험**으로 분리한다. 새 독립 specialist·원본 renderer 실행은 **Not Verified**; `clear`/Ready/approval/merge 판단이 아니다.

- **Target** — [PR #272](https://github.com/mols3131d/hmda-data-reliability/pull/272), owner `agent/test/audit-reliability-design`.
- **Revision** — reviewed pre-write head `61187fce00e33568acc0f2ad9abb7834b3ff23bf`; test-code `22660aba530ec79a82deec2b12e3cc757cd5fd5f`; `main@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`. Code→head 16 commits의 유일한 변경 경로는 **이 Inbox 리뷰 1개**; PR feedback 0.
- **Method** — Research: R1–R13·[현재 감사](02-review-current/README.md), [evaluation Spec](../../openspec/specs/reliability-evaluation-report/spec.md), [reporter](../../src/hmda_reliability/reliability/evaluation/reporter.py), [replay test](../../tests/reliability/test_schema_recovery_executor.py) 대조 → Plan: MUST/기존 oracle/조건부 renderer/Spec owner 분리 → Review: 과장된 필수 test gap 반증.

## Current Findings

현재 test-only 변경의 **확정 필수 수정 없음**.

| ID | Severity / Disposition | Decisive evidence / next |
| --- | --- | --- |
| C14–C15 | 🔵 Note · **drop** | [Evaluation Spec](../../openspec/specs/reliability-evaluation-report/spec.md)은 `expected=[] AND detected=[] ⇒ pass`만 요구. 역명제나 모든 extra detection 금지를 MUST로 만들 수 없음. |
| C16 | 🔵 Note · **follow_up, source conditional** | [`reporter.py::_case_line`](../../src/hmda_reliability/reliability/evaluation/reporter.py)은 `case_name`/refs를 Markdown table cell에 그대로 보간. 이전 R11/R12는 문자열 조립 반례일 뿐 원본 reporter→renderer·허용 입력 경계 실행은 미확인. Reporter source owner가 escaping/이름 정책 확정 후 재현. |
| H2 / R13 C18 | 🔵 Note · **scope_decision, 기존 Spec gap** | [Evaluation Spec](../../openspec/specs/reliability-evaluation-report/spec.md)의 existing/aliased DB scenario는 THEN 누락. 기존 `test_schema_drift_evaluation.py`가 DB bytes·callback 무변경 거부를 이미 검사하므로 test 무보호 주장 기각. `openspec/**`는 [#277 계획](https://github.com/mols3131d/hmda-data-reliability/blob/agent/test/audit-cross-domain-design/inbox/github-277-audit-cross-domain-design/00-plan-cross-domain-tests.md)의 쓰기 범위 밖; Spec owner 결정 필요. |
| C9 | 🔵 Note · **Spec-owner follow_up** | 거절 시 `rejected_by/at` 필수 조건은 구현·변경 test에 있지만 [Approval Spec](../../openspec/specs/reliability-data-contracts/spec.md)에는 승인 metadata만 명시. 구현 결함 확정 아님; Spec owner가 공개 계약 여부 결정. |
| C11 | 🟡 Minor · **test-owner follow_up / mutant 미실행** | [schema hash test](../../tests/reliability/test_profile_snapshots.py)는 name/type 변경을 검출하지만 row-only UPDATE/INSERT 시 hash 불변을 별도로 고정하지 않음. 현재 구현은 schema-only; `hash(schema,row_count)` 반례의 실행은 **Not Verified**. Reliability test owner가 검출력 필요성 결정. |
| C1–C4, C6–C8, C10, C12–C13 | 🔵 Note · **drop** | Targeted freshness, 승인 거부, after-state replay, incompatible pair, schema drift/cleanup 및 post-promotion evidence가 해당 가설을 반박. C9·C11의 별도 후속을 이 행에 포함하지 않음. |
| H4 / R13 C17 | 🟠 Major **underlying F3** · **deduplicate / scope_decision** | 실제 Git hook 환경 오염은 [#270 F3](https://github.com/mols3131d/hmda-data-reliability/blob/agent/test/audit-data-operations-design/inbox/github-270-audit-data-operations-design/02-review-data-operations-tests.md#f3--major-hook-git-environment-escapes-temporary-repositories)에서 추적. 현재 Reliability 변경이 도입한 별도 결함 아님. |

## Current Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Head/base/test blob·source/Spec·PR feedback 대조 | Code→head 변경은 이 Inbox 하나; 5개 Reliability 테스트 변경은 타 도메인과 비중복. |
| ✅ Pass | **원격** 최신 exact-head CI | [CI Lite 40337627154](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40337627154): prospective merge, `tests/reliability` **268 passed / 28.82s**, 선택 Python 검사 성공. Markdown 단계 **skipped**. |
| ⚪ Not Verified | 이번 실행의 local pytest·원본 reporter 렌더링 fault·독립 specialist·post-write CI | 과거 CI/검증과 새 실행을 구별. |

**Next:** H2는 정본 Spec owner가 누락 THEN을 결정; C16은 reporter 입력·출력 경계 재현 뒤 정책 판단. #277은 선행 PR 병합 후 approval→recovery→revalidation의 실제 통합만 소유한다. 공유 hook/source/Spec 변경은 담당자·범위의 명시적 승인 없이 수행하지 않음. 아래 R1–R13은 역사적 증거로 보존.

---

## Historical Review Evidence (R1–R13; superseded dispositions)

> [!IMPORTANT]
> **Blocked (independent review gate pending; R2 source/CI revalidated)** — 새 `current_required` 결함은 아직 확정하지 않았습니다. 이는 머지 불가 판정이 아니라 이번 챗봇 리뷰의 검토 범위와 독립 재검증이 아직 닫히지 않았다는 뜻입니다. 로컬 테스트를 직접 실행하지 않았으므로 기존 CI·독립 리뷰 기록을 본 검토의 재현 결과로 간주하지 않습니다.

- **Target** — [PR #272](https://github.com/mols3131d/hmda-data-reliability/pull/272), owning branch의 Inbox.
- **Revision** — base `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`; reviewed code/head `22660aba530ec79a82deec2b12e3cc757cd5fd5f` (2026-10-26 KST 1차 확인). 직전 코드 검토 후 현재 head `2e1daa1dd6a144bb816dd82f86bc09ce209671b5`까지의 차이는 이 리뷰 문서 추가 1건뿐임을 commit compare로 확인했습니다. 이후에도 code/Spec/CI 변경은 다시 비교합니다.
- **Scope** — 변경 5개 Reliability 테스트 모듈 diff, 도메인 28파일 전수 감사 기록, `reliability-evaluation-report` 정본 Spec과 평가 expected/actual 판정을 직접 비교.

## Findings

현재 직접 확인한 범위에서 **확정된 신규 finding 없음**. 이는 PR 전체의 `clear` 또는 merge readiness 검증 완료를 의미하지 않습니다.

## Perspectives

| Perspective | Reviewer / Method | Focus | Assessment and Evidence |
| --- | --- | --- | --- |
| 평가·정본 | 동일 세션 Spec 대조 | 다중 incident/action 및 empty case | 모든 expected와 required action이 포함되어야 한다는 Spec에 맞춰 partial-failure와 complete-success, 빈 목록 0.0 기대값을 검사함. `tests/reliability/test_evaluation_report.py` |
| 승인·복구 안전 | 동일 세션 정적 반증 | rejected approval, schema exact after replay | rejected reviewer/time 부재 오류, 실행 gate 거부, replacement 진입 차단·실제 after-state 재관측을 함께 검증. `contracts/test_approval.py`, `test_schema_recovery_executor.py` |
| fixture·원본 관측 | 동일 세션 반례 점검 | schema hash rename/type, freshness all-null | `test_profile_snapshots.py`가 해당 partition만 timestamps null로 갱신; observed_at fallback 검출력과 다른 연도 보존 주장은 구현과 추가 대조 필요 |

## Candidate Decisions

| ID | Perspectives | Candidate | Decision | Rationale | Finding |
| --- | --- | --- | --- | --- | --- |
| C1 | 정본 | extra detected incident/action이 자동 실패가 아닌 것은 테스트 오류 | Drop | Spec은 모든 expected/required 값의 포함을 요구; extra를 금지하는 contract 없음. 새 과잉 요구 불가 | — |
| C2 | 복구 안전 | replay가 label만 검사해 replacement를 숨길 수 있음 | Drop | 변경 테스트에 `_replace_table` fail guard와 실제 `create_table_state_identity` 재관측 존재 | — |
| C3 | fixture | all-null freshness 생성이 다른 partition을 손상할 수 있음 | Open | 대상 partition 조건이 diff에 보이나 실제 fixture/비대상 불변 assertion의 충분성은 재확인 필요 | — |

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Evaluation 정본 Spec 비교 | `openspec/specs/reliability-evaluation-report/spec.md`의 subset 요구와 empty 0.0 규칙 직접 확인 |
| ✅ Pass | Diff/path 소유권 정적 대조 | 변경 21파일 중 test는 `tests/reliability/**` 5개. 다른 세 PR와 변경 파일 충돌 없음 |
| ⚪ Not Verified | Recovery/profile implementation과 전체 28-file audit의 독립 재검토 | [existing audit](02-review-current/README.md)와 [기존 independent](02-review-current/independent.md)는 수집된 evidence, 이번 리뷰의 독립 재현은 아님 |
| ⚪ Not Verified | pytest/negative control/CI 재실행 | PR의 268 passed와 변형 테스트 주장은 이 세션에서 직접 실행하지 않음 |

## Risks and Limits

- 정본 Evaluation Spec의 `Existing or aliased evaluation database` 시나리오에 THEN 누락이 실제로 존재합니다. 이는 현행 PR 테스트 변경이 만든 결함이 아니라 #277의 Spec owner 결정 대상입니다.
- data operations와 recovery의 actual E2E, Git fixture 공유 hook 변경도 #277 소유입니다.

## Continuation

- **State:** `mols-loops deep`; Prepare → RPI Research/Plan/Work/Review 1차(동일 세션의 순차 관점) 완료, 독립 신규 specialist 게이트 및 완전한 contract trace 미완료. 이 기록은 제품/테스트를 수정한 증거가 아니라 리뷰 checkpoint입니다.
- **Next:** schema recovery replay code에서 `_replace_table` guard와 expected after identity의 독립성을 추적하고, profile fixture의 비대상 연도 영향과 mutation detection evidence를 검토. 평가 Spec의 missing THEN은 #277 scope decision으로 분리.
- **Revalidation trigger:** main/base, head의 test/source/Spec blob, CI 상태, 새로운 feedback이 바뀌면 기존 판단을 stale로 표시하고 영향을 받는 영역을 다시 조사합니다. 전수 파일 수나 이전 에이전트가 표시한 `clear`를 독립 검증으로 대체하지 않습니다.
- **Boundary:** 이 문서는 비정본입니다. 공유 CI/Git fixture와 교차 도메인 계약은 [#277](https://github.com/mols3131d/hmda-data-reliability/pull/277)에서 선행 PR을 취합한 뒤 검증합니다. 승인·merge·thread resolution은 수행하지 않습니다.

## R2 · 2026-10-26 KST · Source and CI Revalidation

> [!NOTE]
> **이 절은 위 R1의 Open 후보·Not Verified 항목 중 직접 재검증한 부분을 갱신합니다.** 신규 `current_required` 확정 없음. 별도 subagent context의 DualVantage는 이번 runtime에서 수행하지 못했으므로 project-level independent review gate는 여전히 `blocked`이며, 사람의 Ready/approval/merge 판단을 대체하지 않습니다.

- **Research:** `main@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`은 유지. R1 code revision → 현재 head `2e1daa1dd6a144bb816dd82f86bc09ce209671b5` compare는 **Inbox review 1파일 추가만** 포함; test/source/Spec blob은 그대로다. 원래 CI를 현재 코드 검증으로 일반화하기 전, 최신 head의 실제 workflow와 log를 새로 확인했다.
- **Plan:** R1 Open 후보를 실제 source, normative Spec, fixture·oracle에 교차 대조하고 반례가 반박되면 Drop, 별개 ownership/계약 판단이 필요하면 Open으로 유지. 제품·Spec·공용 파일 변경 금지.
- **Review:** 동일 세션에서 oracle/실패·오염/ownership/CI를 순차 관점으로 반증했다. 독립 reviewer가 수행했다고 주장하지 않는다.

### R2 · Reliability

- **C3 → Drop (bounded):** [`test_unmeasurable_profile_reports_unavailable_freshness`](https://github.com/mols3131d/hmda-data-reliability/blob/22660aba530ec79a82deec2b12e3cc757cd5fd5f/tests/reliability/test_profile_snapshots.py#L109-L145)는 `WHERE CAST(partition_at AS DATE) = ?`로 선택 partition만 NULL화한다. [`_calculate_partition_metrics`](https://github.com/mols3131d/hmda-data-reliability/blob/ea39a4fd6c8f483509cf00a1d1114feb4ef3b686/src/hmda_reliability/reliability/profiling/profile_snapshot_builder.py#L136-L199)는 같은 partition filter에서 `max(freshness_column)`을 읽고 None이면 `UNAVAILABLE`로 반환한다. empty/all-null/unconfigured 세 입력은 `observed_at` fallback mutant를 구별한다. 비대상 partition을 변경하는 fixture 오염 가설은 SQL predicate상 반박되지만, 비대상 행 bytes의 실행 후 독립 assertion은 없다.
- **C4 → Drop (bounded):** [schema replay test](https://github.com/mols3131d/hmda-data-reliability/blob/22660aba530ec79a82deec2b12e3cc757cd5fd5f/tests/reliability/test_schema_recovery_executor.py#L204-L231)는 `_replace_table` 호출을 즉시 실패시키고 실제 target `create_table_state_identity`를 `expected_after_state`와 비교한다. [executor](https://github.com/mols3131d/hmda-data-reliability/blob/ea39a4fd6c8f483509cf00a1d1114feb4ef3b686/src/hmda_reliability/reliability/recovery/schema_executor.py#L75-L124)의 exact after 분기는 profile 재검증만 수행한다. Label-only oracle 가설은 반박되었으며 임의의 다른 mutation 경로까지 부재 증명한 것은 아니다.
- **C5 → Open / scope_decision (pre-existing Spec):** [evaluation 정본](https://github.com/mols3131d/hmda-data-reliability/blob/ea39a4fd6c8f483509cf00a1d1114feb4ef3b686/openspec/specs/reliability-evaluation-report/spec.md)의 `Scenario: Existing or aliased evaluation database`는 GIVEN/WHEN만 있고 THEN이 없다. 이 PR의 `tests/reliability/**` 수정만으로 기대 거부 시점·무변경 oracle을 새로 확정할 수 없다. [기존 감사](02-review-current/README.md)의 H1–H4 인계와 합쳐 #277 또는 정본 소유자의 명시적 scope 결정을 기다린다. 이 PR이 새로 도입한 결함으로 기록하지 않는다.
- **Ownership:** 변경된 5개 test module은 `tests/reliability/**` 전용이다. approval→recovery→data-operations E2E와 공유 hook은 #277의 통합·공용 경계이며 현 PR의 추가 테스트 PASS로 대체할 수 없다.

### Validation and Continuation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | R1→current SHA 및 소유권 정적 비교 | `git compare`의 1 commit, 이 PR의 `review-chatbot-deep.md` 추가만 존재. 최신 main/base `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686` |
| ✅ Pass | 원격 CI Lite 최신 head의 실제 실행 로그 | [Run 40218909695](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40218909695) — **268 passed in 24.87s**; prospective merge checkout, selected tests·Python validation 성공. 이는 GitHub runner의 실행이며 로컬 재실행이 아니다. |
| ⚪ Not Verified | 이번 회차 로컬 pytest·mutant·integration 재실행 | GitHub connector 정적 조회 및 원격 CI log 검토만 수행; 독립 실행 증거 없음 |
| ⚪ Not Verified | 별도 컨텍스트의 독립 DualVantage gate | 별도 reviewer/subagent 실행을 수행하지 못함. 동일 세션의 다관점 대조를 독립 리뷰로 승격하지 않음 |
| ⚪ Not Verified | #277 최종 통합 및 공용 Git hook 영구 수정 | [#277](https://github.com/mols3131d/hmda-data-reliability/pull/277)은 `74ac659d084fadd5e93900b132ef5b995ef8d919`, base `81fe44b2...`의 Draft; #269–#276은 아직 모두 병합 전. 순차 통합 후 재검증 필요 |

**Next transition:** 신규 `current_required`를 만들기 위해 기존 finding을 반복하지 않는다. 다음 Run은 현 PR head와 source/test/Spec blob, CI run을 먼저 비교하고, 독립 specialist 검토가 실제 가능할 때만 independent gate를 진행한다. #277 owner는 기존 감사의 H/F 항목을 참조해 선행 PR이 main에 통합된 **한 revision**에서 current/candidate artifact·approval/recovery·dbt log·Git fixture isolation의 부정 경로를 검증한다. 이 문서 수정 commit은 Inbox-only이며 이 절의 `reviewed head`는 수정 **직전** SHA다. 변경 후 head는 PR에서 다시 확인한다.

## R3 · 2026-10-26 KST · Fresh-Head Challenge and Handoff

> [!NOTE]
> **Research → Plan → Review:** Compared previous R2 head `2e1daa1dd6a144bb816dd82f86bc09ce209671b5` to authoritative head `07e0a26436ff4196b916f86ab3cd07e1619406fd` and main/base `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`: only this Inbox review changed, so earlier code/Spec/test findings remain revision-applicable. No new PR conversation feedback. The plan was to challenge one unresolved inference against a separate source/test path, keep test-only PR ownership, and validate latest remote CI without claiming local execution. This is same-session multi-perspective analysis, **not** isolated independent review.

### R3 · Reliability · Missing-THEN Impact Reassessment

- **C5 → 🔵 Note / follow_up (pre-existing Spec wording), not a current test defect:** [Canonical evaluation Spec](../../openspec/specs/reliability-evaluation-report/spec.md) still has `Scenario: Existing or aliased evaluation database` with GIVEN/WHEN and **no THEN** (lines 193–196). However [existing schema-drift integration tests](../../tests/reliability/test_schema_drift_evaluation.py), lines 40–126, already exercise all three existing DB paths with exact original database bytes and no callback/new entries, plus canonical path aliases with no workspace/callback. This directly refutes the stronger R2 implication that the missing THEN entails an unprotected current test/implementation path. The missing normative wording remains a Spec-owner documentation decision, outside this test-only PR; do not make #277 invent acceptance semantics or call this a new regression.
- **Counterexample limit:** Those tests do not prove all symlink/hardlink aliases or all platform-specific physical path cases; no new runtime mutation experiment was performed. A distinct alias mode should be promoted to a finding only with an authorized physical-path contract and reproducible counterexample.
- **Disposition:** R2 C3/C4 stay Drop; C5 is bounded follow_up, not an independent-review clearance. No confirmed new `current_required`; independent specialist gate remains **blocked**.

### R3 Validation and Next Transition

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Remote revision and changed-path comparison | `2e1daa1dd6a1..07e0a26436ff` is one Inbox-only commit; no new test/source/Spec diff; domain test file paths do not overlap #269/#270/#271/#272. |
| ✅ Pass | Latest remote CI selected-suite log | [CI Lite 40223434550](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40223434550), job `121259726551`: **268 passed in 24.01s** with selected Python checks success on prospective merge. GitHub runner evidence only. |
| ⚪ Not Verified | This session's local pytest, targeted fault injection, and independent specialist | No local execution or isolated reviewer; earlier run reports are historical evidence, not this run's result. |
| ⚪ Not Verified | [#277](https://github.com/mols3131d/hmda-data-reliability/pull/277) integrated contract test | Still Draft at `74ac659d084fadd5e93900b132ef5b995ef8d919`, initial base `81fe44b2`; prerequisite domain PRs remain unmerged. |

**Next:** Re-check exact head/base/CI before reuse. Follow the candidate-specific owner and counterexample above; run only the narrow relevant fault/alias/integration test in a disposable isolated environment if authorized. Preserve the difference between remote CI success, static inference and independent review. Do not modify shared code/Spec or approve/merge. This reviewed head is the **pre-Inbox-update** SHA; verify the resulting commit changed only this document.

## R4 · 2026-10-26 KST · Schema Replay Preflight and No-Write Countercheck

> [!NOTE]
> **Assessment: blocked for the independent specialist gate; no new confirmed `current_required`.** This loop examines the approved replay path separately from R3's evaluation-Spec missing-THEN wording.

- **Target** — PR #272, `agent/test/audit-reliability-design`, existing review artifact only.
- **Revision** — R3 reviewed head `07e0a26436ff4196b916f86ab3cd07e1619406fd` → authoritative pre-write head `ed62cb64397e23b20fcf6605792e53cd7d8678e8`; compare shows one Inbox-only commit. Current `main@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`, no intervening test/source/Spec changes; no PR discussion feedback.
- **Scope** — changed schema replay regression test, canonical schema-recovery contract, actual executor branch and staged-candidate preflight, other PR ownership and remote CI. No production/Spec/shared edits.

### R4 Candidate Decision

| ID | Severity | Scope relation / disposition | Evidence and counterevidence | Action |
| --- | --- | --- | --- | --- |
| C6 | 🔵 Note | `contract_dependency` / **Drop** | [Schema executor](../../src/hmda_reliability/reliability/recovery/schema_executor.py), `execute_approved_schema_recovery`, validates the exact approval, stages/verifies the approved candidate, takes the mutation lock, then branches on `current_state == expected_after_state` **before** calling `_replace_table`. [Changed replay test](../../tests/reliability/test_schema_recovery_executor.py), `test_schema_recovery_replays_exact_after_without_replacement` (around lines 207–241), replaces that mutation entry with a failing sentinel and independently reopens DuckDB to compare complete state, profile population and `already_restored/resume_verification` evidence. [Canonical schema-recovery Spec](../../openspec/specs/reliability-schema-recovery/spec.md), `Table-recovery reconciliation`, requires no repeated replacement on exact after-state. The stronger conjecture that the replay test accepts an unnecessary replacement merely because returned labels match is refuted. | Retain existing R3/R4 Drop. The sentinel guards this actual implementation entry, not hypothetical new mutation entrypoints; require a concrete bypass to reopen. |

**Research → Plan → Review:** Rechecked the exact code path and independent table-state oracle, including the adversarial possibility of replay with an unavailable candidate. The executor intentionally stages the approved candidate **before** target-state reconciliation, and the Spec also requires approved staged-candidate identity; absence of the candidate is not, by itself, an authorized “replay must succeed” contract. Do not invent a missing-candidate success oracle or mark the code defective without an explicit owning contract. R3 C5 remains a pre-existing evaluation-Spec wording follow-up; no inferred current test failure.

### R4 Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Revision/ownership static comparison | `07e0a264..ed62cb64` is this Inbox file only; five changed tests remain under `tests/reliability/**`, disjoint from #269/#270/#271. |
| ✅ Pass | Remote prospective-merge CI log inspection | [CI Lite 40228409557](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40228409557), job `121274716718`, merge `ff2ce32725d355fdac79e8249395da894545961c` of head `ed62cb64` into base `ea39a4fd`: **268 passed in 23.01s**; selected Python checks succeeded. |
| ⚪ Not Verified | Local pytest, candidate removal/mutation, independent specialist or extra fault injection | Not executed in this continuation; code-path proof and GitHub CI are distinct from local execution. |
| ⚪ Not Verified | #277 integrated safety and recovery proof | #277 remains Draft at `74ac659d084fadd5e93900b132ef5b995ef8d919`, initial base `81fe44b2` one commit behind current main; upstream PRs unmerged. |

**Next:** Preserve the schema replay sentinel and complete-state/profile assertions. Reopen the candidate-preflight question only if the owning Spec explicitly changes replay availability semantics or an executable counterexample shows an authorized path failing. The evaluation-Spec missing THEN belongs to its Spec owner; #277 owns only integrated approval→recovery→revalidation and shared execution boundaries. Recheck post-write head/CI before claiming freshness. No Ready, approval, merge or review-thread mutation.

## R5 · 2026-10-26 KST · Incompatible Detection Population Oracle

> [!NOTE]
> **Handoff / independent review pending; no new confirmed current_required.** R4의 schema replay가 아닌 변경된 incident-detection pair 검증을 반증했습니다.

- **Revision:** R4 pre-write `ed62cb64397e23b20fcf6605792e53cd7d8678e8` → authoritative pre-write `b5945a43772ede3446767bf8679691095358046c`: 이 Inbox만 바뀐 단일 commit. `main/base@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`; test/source/Spec 불변.
- **Research → Plan → Review:** [변경된 negative test](../../tests/reliability/test_basic_incident_detection.py) `test_detection_request_rejects_different_populations`, [request validator](../../src/hmda_reliability/reliability/detection/request.py), [정본 detection Spec](../../openspec/specs/reliability-incident-detection/spec.md)의 incompatible-profile scenario를 독립된 계약·구현·oracle 관점에서 대조했습니다.

| ID | Severity | Decision / Evidence | Next |
| --- | --- | --- | --- |
| C7 | 🔵 Note | **Drop:** `model_copy(update=...)`가 `ProfileSnapshot`의 자체 재검증을 생략한다는 이유만으로 false-green이라는 가설은 부적절. 테스트 대상은 **DetectionRequest의 pair compatibility**이며 validator는 `asset_name` 및 `partition` 불일치를 각각 명시적으로 거부합니다. Parametrized test는 각각의 mismatch와 field-specific `ValueError`를 검사해 정본 THEN과 일치합니다. 별도 두 field 동시 mismatch를 요구하는 계약은 없음. | 기존 두 독립 반례를 유지. 이 후보로 새 test나 source 변경을 요구하지 않음. |
| C5 | 🔵 Note | **Keep prior Spec-owner follow_up:** evaluation의 existing/aliased DB scenario missing THEN은 정본 문구 gap이나 기존 read-only/무변경 테스트를 무효화하지 않음. | Spec owner가 기대 의미를 결정; #277은 approval→recovery→revalidation 실제 통합만 소유. |

### R5 Validation and Continuation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | R4→head 및 Spec→validator→test 정적 대조 | Inbox-only commit; 변경된 `tests/reliability/**` 5파일은 #269/#270/#271와 비중복. |
| ✅ Pass | 최신 **원격** prospective-merge CI log | [CI Lite 40232627257](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40232627257), job `121287403548`: **268 passed in 18.47s**, selected Python checks 성공. |
| ⚪ Not Verified | 이번 회차 로컬 pytest/negative mutation, 독립 specialist | 미실행; 코드·Spec의 정적 일치와 실제 회귀 실행 증거는 구분. |
| ⚪ Not Verified | #277 integrated recovery 및 승인 | 선행 PR 미병합, #277 Draft. |

**Next:** 현재 Drop 판단은 pair-compatibility 계약 또는 validator/test가 변경될 때만 재개. 다른 도메인 PR의 test/source를 수정하지 않고 #277은 통합 boundary만 검증. Reviewed head는 Inbox 갱신 전 SHA입니다.

## R6 · 2026-10-26 KST · Post-Promotion Evidence Boundary Countercheck

> [!NOTE]
> **Research → Plan → Review / handoff.** R5 detection-pair validator와 다른 평가 경계를 조사했습니다. “promotion 후 DataOperationError가 발생하면 prior projection을 그대로 보고할 수 있다”는 신규 후보는 **현재 실제 테스트가 반박**합니다. 독립 specialist gate는 여전히 미완료입니다.

- **Revision:** R5 reviewed pre-write `b5945a43772ede3446767bf8679691095358046c` → authoritative pre-write `700bde2e7c0290d3926814c9b98a7684796c90cf`: 단일 Inbox-only commit. `main/base@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686` 유지; code/test/Spec 변경 없음, 새 PR feedback 없음.
- **Candidate C8 · 🔵 Note · Drop (existing safeguard):** [canonical evaluation Spec](../../openspec/specs/reliability-evaluation-report/spec.md) `Artifact state after post-promotion domain failure`는 prior projection을 사실처럼 보고하는 것을 금지. [existing test](../../tests/reliability/test_evaluation_report.py) `test_post_promotion_data_operation_failure_reports_actual_current_projection` (around lines 838–887)는 **실제** `promote_dbt_artifacts`로 current pair를 변경한 뒤 `DataOperationError`를 발생시키고, report가 promoted projection ID를 포함하며 prior ID는 제외하고 `resume_verification`을 기록함을 검사합니다. 동일 파일 `test_volume_drop_vertical_slice_is_deterministic_and_replay_safe`의 별도 `RuntimeError` 경로는 예외 전파와 mutation persistence를 검사할 뿐, domain failure evidence와 혼동하지 않습니다. 따라서 이 계약에 **아무런 테스트가 없다**는 가설은 Drop.
- **Scope limit / #277 handoff:** 해당 Reliability test는 fake dbt candidate/target validation과 실제 local promotion primitive를 조합합니다. 진짜 dbt subprocess → Data Operations current promotion → Reliability read를 하나의 동시 실행 계약으로 입증하지는 않으므로 #277은 그 **접점**만 확인해야 합니다. R3 C5의 schema evaluation Spec missing THEN은 별도 Spec-owner follow_up으로 유지; 이번 C8과 섞지 않음.
- **Cross-PR ownership:** #272의 5개 changed test는 `tests/reliability/**`; #269 HMDA Data, #270 Operations, #271 Platform과 exclusive path 충돌 없음. 공용 fixture/CI/Spec 수정 없음.

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | R5→R6 revision and canonical Spec→test→implementation boundary static review | `b5945a43..700bde2e` Inbox-only; existing test invokes actual promotion and asserts current projection evidence. |
| ✅ Pass | Remote current-head prospective-merge CI | [CI Lite 40238122266](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40238122266): merge `82ea90b1`, **268 passed in 25.84s**, 선택 Python checks 성공. |
| ⚪ Not Verified | Local reliability pytest, real dbt→promotion→consumer integration, independent specialist | 실행하지 않음; remote CI는 domain-selected test only. |
| ⚪ Not Verified | #277 integrated gate and human approval | #269–#276 all open/unmerged Draft; #277 Draft `74ac659d084fadd5e93900b132ef5b995ef8d919` and initial base `81fe44b2` lags `main@ea39a4fd`. |

**Next:** C8 Drop 유지; 실제 dbt→promotion→locked consumer identity는 선행 병합 후 #277 owner가 exact run/manifest/result projection으로 재현. Missing-THEN wording은 Spec owner가 결정. Reviewed head는 Inbox 갱신 전 SHA; 승인/merge/Ready 상태 변경 없음.

## R7 · 2026-10-26 KST · Rejection-Metadata Oracle and Canonical Contract

> [!NOTE]
> **Research → Plan → Review / handoff.** R6의 promotion-evidence 경계와 다른 **신규 변경 approval test**의 독립 oracle 근거를 정본 Spec에 대조했습니다. 구현 동작을 보존하는 test와 정본이 명시한 acceptance를 구별하며, 새 필수 수정 결함은 확정하지 않았습니다.

- **Revision:** R6 pre-write `700bde2e7c0290d3926814c9b98a7684796c90cf` → R7 authoritative pre-write `47c98d33754dd2e8a44fac92530fc9624779cb56`: 이 Inbox만 변경한 1 commit. `main/base@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`; source/test/Spec 불변, PR comments 0.
- **Contract/locations:** [canonical Approval Spec](../../openspec/specs/reliability-data-contracts/spec.md) `Approval contract` (L65–81); [implementation](../../src/hmda_reliability/reliability/contracts/approval.py) `Approval._validate_review_fields` / `can_execute_risky_action`; [changed test](../../tests/reliability/contracts/test_approval.py) L31–86.

| ID | Severity | Decision / scope relation | Evidence and counterevidence | Next |
| --- | --- | --- | --- | --- |
| C9 | 🔵 Note | **Accept as follow_up / pre-existing implementation policy, not `current_required`** | 새 `test_rejected_approval_requires_reviewer_and_time`는 `rejected_by`와 `rejected_at` 누락 3종에 `ValidationError`를 요구하며, **현재** Pydantic validator의 조건을 정확히 구별합니다. 그러나 정본 Spec의 `승인 상태 기록`은 `approved_by/approved_at`만 명시하고, `미승인 작업 차단`은 `pending/rejected`의 실행 거부만 요구합니다. **거절 메타데이터 필수 여부는 정본에서 명시되지 않음.** 이를 현재 제품 결함이나 테스트 false green으로 확대하지 말고, 해당 불변식을 장기 public contract로 보존할지 Spec owner가 결정해야 합니다. | Contract를 명시할 필요가 있을 때만 Spec owner에 의도 확인. 현 PR은 test-only이므로 Spec 변경 금지. |
| C10 | 🔵 Note | **Drop / rejection bypass 가설** | 같은 PR이 추가한 `rejected` 사례는 `can_execute_risky_action(rejected) is False`를 직접 검사하고, 구현도 `status is APPROVED`만 허용합니다. 정본 `미승인 작업 차단`의 최소 status gate는 이미 검출됩니다. 다만 **exact proposal/action binding**은 owning recovery 실행 경계의 별도 contract이며 이 단위 테스트가 증명한다고 주장하지 않습니다. | 중복 단위 테스트를 요구하지 않음; #277에서 실제 proposal→approval→recovery→revalidation 통합만 확인. |

### R7 Validation and Continuation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | R6→R7 head, PR patch 및 Spec→validator→test 정적 대조 | `700bde2e..47c98d33` Inbox-only; `tests/reliability/**` 5파일은 #269/#270/#271의 test lane과 비중복. |
| ✅ Pass | R7 pre-write head의 원격 prospective-merge CI | [CI Lite 40242543901](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40242543901), merge `d344f75` into `ea39a4fd`, **268 passed in 24.81s**. |
| ⚪ Not Verified | 로컬 pytest/approval mutation, 독립 specialist, #277 integration | 미실행. CI 통과는 proposal-bound human approval이나 cross-domain recovery 증명이 아님. |

**Next:** C9는 정책이 정본에 고정되어야 하는지에 대한 **Spec owner의 후속 판단**으로 남기되, 이 test-only PR의 blocker로 만들지 않음. R6 C8 promotion-evidence 가설 Drop과 R3 C5 evaluation missing-THEN follow_up은 유지. #277은 선행 병합 뒤 exact proposal binding과 recovery 결과를 실제 경계에서 검증. 이 절의 head는 **Inbox 갱신 전** SHA; 승인·merge·Ready 변경 없음.

## R8 · 2026-10-26 KST · Schema-Only Hash Metamorphic Oracle

> [!NOTE]
> **Research → Plan → Review / handoff.** R7 approval metadata 정책 판단을 반복하지 않고, 변경된 schema hash 테스트가 **데이터 행만 변하는 경우**를 구별하는지 정본·구현·테스트의 독립 성질로 점검했습니다. 새로운 production defect는 확인되지 않았습니다.

- **Revision:** R7 reviewed pre-write `47c98d33754dd2e8a44fac92530fc9624779cb56` → authoritative R8 pre-write `2af3bb20924e077e5965be45010d035bfe49c16d`; 한 Inbox-only commit. `main/base@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`, source/test/Spec 불변, PR comments 0.
- **Contract/locations:** [schema-hash Spec](../../openspec/specs/reliability-profile-snapshots/spec.md) `Deterministic schema hash`는 column name·physical type에 바인딩; [implementation](../../src/hmda_reliability/reliability/profiling/profile_snapshot_builder.py) `calculate_schema_hash`는 `DESCRIBE`의 name/type만 hash; [changed test](../../tests/reliability/test_profile_snapshots.py) `test_schema_hash_is_deterministic_and_changes_with_schema`.

| ID | Severity | Decision / scope relation | Evidence and counterevidence | Next |
| --- | --- | --- | --- | --- |
| C11 | 🟡 Minor (test-design gap) | **Accept as follow_up / pre-existing oracle omission, not `current_required`** | 변경 테스트는 같은 schema의 연속 두 계산이 같고 ADD/RENAME/TYPE 변화에서 hash가 달라짐을 검사합니다. 하지만 **schema 그대로 두고 row UPDATE/INSERT만 수행한 뒤 hash가 불변**인지 확인하지 않습니다. 예컨대 `hash(schema, row_count)` mutant는 연속 계산과 세 schema mutation을 모두 통과하면서 정본의 schema-only identity를 어깁니다. 현 구현은 name/type만 hash하므로 **제품 결함 근거는 없고**, 이 test-only PR의 필수 수정으로 격상할 근거도 부족합니다. | Reliability test owner가 후속 검출력 보강이 필요하다고 판단하면 같은 connection에서 row-only UPDATE/INSERT 전후 `calculate_schema_hash` 동일성을 고정하는 작은 metamorphic test 추가; mutant가 해당 test에서 실패하는지 확인. |
| C12 | 🔵 Note | **Drop / type-only drift undetected 가설** | 변경 테스트의 `ALTER COLUMN loan_amount TYPE DECIMAL(12,2)`는 이름을 유지하면서 physical type만 바꿉니다. `hash(column names only)` mutant는 이 case에서 실패하므로 이름 변경만 검사한다는 가설은 반박됩니다. | 중복 타입 회귀 테스트 요구 없음. |

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | R7→R8 revision 및 Spec→hash implementation→test 정적 대조 | 한 Inbox-only commit; 현재 hash는 name/type 기반, type-only negative control 존재, row-only invariant test 없음. |
| ✅ Pass | 최신 **원격** prospective-merge CI | [CI Lite 40247154350](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40247154350): merge `dd2e9bbd3f3c1e1fbfbd4ffbe6812ba6c37eddb6`, `tests/reliability` **268 passed in 24.43s**. Row-only mutant 미포함. |
| ⚪ Not Verified | Row-only mutant execution, local pytest, independent specialist, #277 integration | 미실행. 기존 R7 C9 rejection metadata Spec-owner 판단은 계속 열려 있음. |

**Next:** C11은 실제 row-only mutant가 현재 테스트를 통과하는지와 schema-only acceptance 우선순위를 test owner가 판단. C9의 거절 메타데이터 필수 정책은 Spec owner의 별도 결정이며 #277에는 exact proposal→approval→recovery→revalidation 통합만 전달. 갱신 후 head/CI를 재확인하고 승인·merge·Ready는 변경하지 않습니다.

## R9 · 2026-10-26 KST · Recovery Cleanup Failure And Replay Countercheck

> [!NOTE]
> **Research → Plan → Review / handoff.** R8 schema-only hash gap을 반복하지 않고, 승인된 schema recovery의 **commit 이후 cleanup failure**가 이미 완료된 target을 다시 교체하도록 오인하게 만드는지 부정·재실행 관점에서 검토했습니다. 현 테스트가 해당 후보를 반박하므로 새 결함으로 채택하지 않습니다.

- **Revision:** R8 pre-write 2af3bb20924e077e5965be45010d035bfe49c16d → authoritative pre-write 10c66af65587f0547d9967a228ad763f80bfba71: GitHub compare에서 이 Inbox 한 파일만 변경한 1 commit. main/base ea39a4fd6c8f483509cf00a1d1114feb4ef3b686, source/test/Spec 불변, PR feedback 0.
- **Research:** [정본 schema recovery Spec](../../openspec/specs/reliability-schema-recovery/spec.md) L139–168은 post-commit staging cleanup 실패와 replay 중 cleanup 실패에서 **actual state, mutation_state, resume_verification**을 보존하고 재실행 시 table replacement를 반복하지 않도록 요구합니다. [변경 test](../../tests/reliability/test_schema_recovery_executor.py) L237–299는 before/after target 각각에 unlock, DuckDB close, staging cleanup 세 fault를 주입하는 **2×3=6** case에서 SchemaRecoveryValidationError의 failure_stage, mutation_state, actual complete-table state, reconciliation_action을 확인하고 같은 approval로 replay한 뒤 already_restored 및 profile-only action을 요구합니다. [별도 exact replay test](../../tests/reliability/test_schema_recovery_executor.py) L205–235는 _replace_table을 금지한 채 동일 after-state를 검증합니다.
- **Plan:** fault가 rollback 전/후인지 분리하고, cleanup 예외가 committed state를 되돌렸다는 추측을 actual state 및 replay assertion으로 반증합니다. 실제 cross-domain proposal→approval→dbt revalidation은 #277의 예약 integration입니다.

| ID | Severity | Disposition / ownership | Evidence / counterevidence | Next |
| --- | --- | --- | --- | --- |
| C13 | 🔵 Note | **Drop / cleanup-error implies repeated mutation** | 여섯 fault case는 target expected_after_state와 actual identity의 일치, error stage 및 resume_verification, 재시도 시 already_restored를 모두 요구합니다. 별도 test는 after-state에서 table replacement 진입 자체를 차단합니다. 따라서 이 조건에 아무 회귀 검출력이 없다는 가설은 반박됩니다. 단, fault injection은 monkeypatch된 unlock/close/TemporaryDirectory이고 실제 disk-loss/process-kill 복구를 증명하지 않습니다. | 중복 test 요구 없음. |
| C11 | 🟡 Minor | **Keep prior test-design follow_up / #272 test owner**, not current_required | R8의 schema hash row-only invariant 누락은 별개입니다. Cleanup replay test로 이를 해결하거나 부정하지 않습니다. | 필요 시 schema 그대로 row UPDATE/INSERT 후 hash 불변을 고정하는 metamorphic test와 mutant red 검증. |
| C9 | 🔵 Note | **Keep Spec-owner follow_up** | Rejected approval reviewer/time 필수 조건은 구현/test에 있지만 approval Spec에 명시되지 않은 R7 정책 공백입니다. Cleanup/replay 결과와 독립입니다. | Spec owner가 public policy 여부 결정; 여기서 정본 수정 금지. |

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | R8→head compare, recovery Spec→six fault test→exact replay oracle 정적 대조 | Inbox-only, 2×3 parameterization과 persisted state·error·replay assertion 확인. |
| ✅ Pass | **원격** prospective-merge CI | [CI Lite 40251459699](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40251459699): merge 6f69c48fe18263fa9a6ecca696ea5788c5856fa2, tests/reliability **268 passed in 21.17s**. 실제 process-kill/cross-domain fault는 미포함. |
| ⚪ Not Verified | 로컬 원본 pytest, disk-loss/process-kill, 독립 specialist, #277 integration | 이번 회차 미실행. Remote CI의 selected suite 결과만 확인. |

**Next:** C13 Drop, C11과 C9는 각각 Reliability test/Spec owner 후속 판단으로 유지. #277은 선행 #269–#276 병합 뒤 exact proposal binding→recovery→dbt/profile revalidation만 검증합니다. 이 절은 갱신 전 SHA; 이후 head/CI 재확인 필요. 승인·Ready·merge 변경 없음.

## R10 · 2026-10-26 KST · Normal-Case False-Positive Evaluation Oracle

> [!NOTE]
> **Research → Plan → Review / continuation.** R9의 recovery cleanup 및 R8 schema hash와 별개로, normal synthetic evaluation에서 **예상하지 않은 incident가 발생한 경우**의 음성 oracle을 점검했습니다. 현재 구현은 정본과 일치하지만 변경 테스트의 회귀 검출 공백은 후속 판단으로 보존합니다.

- **Revision:** R9 reviewed pre-write `10c66af65587f0547d9967a228ad763f80bfba71` → authoritative R10 pre-write `80ae1187b1c7556bc4c342268fdd18536f757e6f`: GitHub compare는 이 Inbox만 변경한 1 commit. `main/base@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`; test/source/Spec 불변, PR discussion 0.
- **Research / contract:** [정본 evaluation Spec](../../openspec/specs/reliability-evaluation-report/spec.md) `Normal case handling`은 expected incident가 없을 때 실제 detection도 없어야 PASS라고 명시합니다. [구현](../../src/hmda_reliability/reliability/evaluation/case_result.py) `EvaluationCaseResult.detection_passed`는 `not expected`일 때 `not detected`를 반환하므로 **현재 제품 동작은 정본과 일치**합니다. [변경 테스트](../../tests/reliability/test_evaluation_report.py) L75–220의 normal case들은 `expected=[]/detected=[]` 성공, incident case들은 expected nonempty의 누락 및 action 누락을 검사하지만, `expected=[]/detected=["volume_drop"]` 실패는 직접 고정하지 않습니다.
- **Plan / falsifier:** `if not expected_incident_types: return True`라는 false-positive mutant는 위 변경 테스트의 normal 성공·incident 누락·empty report assertion만으로는 거부되지 않습니다. 단, **전체 repository suite의 mutant 생존을 실행·증명한 것은 아니며**, 이는 해당 변경 테스트의 정적 coverage gap입니다.

| ID | Severity | Disposition / scope relation | Evidence / counterevidence | Next |
| --- | --- | --- | --- | --- |
| C14 | 🟡 Minor | **Accept as follow_up / pre-existing test-oracle omission, not current_required** | 정본 normal-case negative contract에 대한 `expected=[]/detected≠[]` 독립 반례가 변경된 aggregation 테스트에 없습니다. 구현은 이미 올바르므로 production defect 또는 신규 regression으로 오인하지 않습니다. | Reliability test owner가 가치 있다고 판단하면 `EvaluationCaseResult(... expected_incident_types=[], detected_incident_types=["volume_drop"]).detection_passed is False` 및 mixed report의 success count를 추가하고 mutant red를 확인. |
| C15 | 🔵 Note | **Drop / expected nonempty에서 모든 extra incident도 금지해야 한다는 가설** | 정본은 **모든 expected type의 포함**을 요구하며, 예상 외 type의 존재 자체를 무조건 FAIL로 규정하지 않습니다. 구현의 subset 비교를 임의로 exact-set 비교로 바꿀 근거가 없습니다. | 현 계약 밖의 strict equality oracle을 요구하지 않음. |
| C11 / C9 | 🟡 Minor / 🔵 Note | **Keep prior owner-specific follow_up** | Schema-only hash row-only invariant(C11) 및 rejected approval metadata 정책(C9)은 이 normal-case oracle과 독립입니다. | 각각 Reliability test owner / Spec owner 결정. |

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | R9→R10 head, Spec→case model→changed evaluation tests 정적 대조 | Inbox-only 1 commit; normal success와 false-positive negative case의 차이 확인. |
| ✅ Pass | **원격** R10 pre-write prospective-merge CI | [CI Lite 40256307308](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40256307308), job `121358796639`: `TARGETS=tests/reliability` **268 passed in 27.83s**, 선택 Python checks 성공. Normal-case mutant는 미실행. |
| ⚪ Not Verified | 이번 회차 로컬 pytest, normal-case mutant, 독립 specialist, #277 integrated recovery | 미실행. |

**Next:** C14는 정본 normal-case 보호의 작은 test-only 보강 후보이며 현 PR의 merge blocker로 격상하지 않습니다. C15 Drop; 기존 C11/C9는 소유자별 판단 유지. #277에는 approval→recovery→revalidation 실제 경계만 인계. 이 절의 SHA는 **Inbox 갱신 전** head이고 Ready·approval·merge는 변경하지 않습니다.

## R11 · 2026-10-26 KST · Normal-Case Spec Direction and Markdown Contamination

> [!IMPORTANT]
> **Research → Plan → Review / correction and continuation.** R10 C14의 **정본 근거를 좁혀 정정**하고, 다른 surface인 evaluation Markdown output에서 구조적 오염 반례를 확인했습니다. 원본 reporter/pytest는 실행하지 않았습니다.

- **Revision:** R10 reviewed pre-write `80ae1187b1c7556bc4c342268fdd18536f757e6f` → authoritative R11 pre-write `f2ed892f7902777f107ab520f1b8ea66117b9f03`; GitHub compare Inbox-only 1 commit. `main/base@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`, tests/source/Spec 불변, PR discussion 0.
- **C14 contract correction:** [Evaluation Spec](../../openspec/specs/reliability-evaluation-report/spec.md) `Normal case without detection`는 **expected=[] AND detected=[] ⇒ PASS**만 명시합니다. R10의 `expected=[]/detected≠[] ⇒ FAIL`을 **명시적인 정본 MUST 계약**으로 서술한 부분은 과장입니다. [구현](../../src/hmda_reliability/reliability/evaluation/case_result.py) `detection_passed`는 실제로 unexpected detection을 FAIL 처리하며 [변경 테스트](../../tests/reliability/test_evaluation_report.py) (L75–220)는 이를 직접 고정하지 않습니다. 따라서 false-positive mutant는 **현재 구현의 동작을 바꾸지만**, Spec 위반이라고 단정하려면 Spec owner의 역방향 기대값 결정이 필요합니다.
- **Markdown contamination:** [reporter](../../src/hmda_reliability/reliability/evaluation/reporter.py) `_case_line` (around L60–76)는 `case_name`, `evidence_refs` 등을 `| ... |` 셀에 escape 없이 삽입합니다. [case model](../../src/hmda_reliability/reliability/evaluation/case_result.py) `_validate_case_name`은 nonblank만 검사합니다. [변경 report 테스트](../../tests/reliability/test_evaluation_report.py) (L216–247)는 고정 안전한 이름만 사용합니다. 별도 disposable Python 문자열 조립 probe에서 `case_name="normal|PASS"`를 삽입하면 10-column case row가 **11개 셀**로 분할됩니다. Newline을 포함한 값은 임의 행처럼 보이게 할 가능성이 있으나 실제 Markdown renderer 및 public input reachability는 검증하지 않았습니다.

| ID | Severity | Disposition / scope relation | Evidence and next |
| --- | --- | --- | --- |
| C14 correction | 🟡 Minor / **uncertain contract** | **Revise R10 `Accept` → `Unknown` (Spec-owner contract_dependency), not current_required** | 구현의 negative semantics는 유지되지만 정본의 역방향 MUST는 없음. Spec owner가 false-positive policy를 명시하면 #272 test owner가 `expected=[]/detected=[volume_drop]` mutant-red oracle을 추가할지 결정. |
| C16 | 🟡 Minor **conditional output integrity** | **Accept as pre-existing source/test follow_up, not current_required** | Unescaped pipe로 case table column drift가 가능. Reporter owner가 escaping/validation policy를 정한 뒤 pipe/newline case의 정확한 row/column 및 user-readable output을 검증. |
| C15 | 🔵 Note | **Keep Drop** | Expected incident nonempty일 때 extra detection까지 자동 FAIL이라는 exact-set 요구는 여전히 정본 근거 없음. |

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | R10→R11 head, Spec implication 방향·model→reporter→test 정적 대조 | Inbox-only 1 commit; 정본 문구와 구현의 구별 확인. |
| ✅ Pass | **로컬 disposable 문자열 조립 probe** | `case_name="normal|PASS"`에서 10개 예정 셀이 11개로 분할됨. **원본 reporter, Markdown renderer 또는 pytest 미실행**. |
| ✅ Pass | **원격** 현재 head prospective-merge CI | [CI Lite 40261555507](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40261555507): `tests/reliability` **268 passed in 24.25s**, selected Python checks 성공; 2026-10-26 02:57 UTC 완료. |
| ⚪ Not Verified | 원본 reporter pipe/newline 실행, normal false-positive mutant, 로컬 pytest, 독립 specialist, #277 통합 | 미실행. `inbox/**` Markdown lint는 CI classifier에서 제외. |

**Next:** C14의 이전 '정본이 negative를 명시한다'는 주장을 이 정정으로 대체; Spec owner 판단 전 필수 test 수정으로 승격하지 않음. C16은 Reliability reporter owner의 output escaping 정책 결정과 별도 component oracle 후보. #277에는 approval→recovery→revalidation 실제 경계만 인계하고 내부 reporter/normal-case 정책을 떠넘기지 않습니다. Ready·approval·merge는 변경하지 않습니다.

## R12 · 2026-10-26 KST · Evaluation Markdown Row-Forgery Falsifier

> [!IMPORTANT]
> **Research → Plan → Review / strengthened C16.** R11의 `|` column drift에서 한 단계 더 나아가, **newline을 포함한 case_name이 Markdown에 별도 PASS 행을 삽입하는 것처럼 보이는** 오염 경계를 검토했습니다. C16과 동일한 root cause이므로 별도 신규 finding을 만들지 않습니다.

- **Revision:** R11 reviewed pre-write `f2ed892f7902777f107ab520f1b8ea66117b9f03` → authoritative R12 pre-write `7ceb3809a3148787e3e75a856046b03e4b08c7a8`; GitHub compare Inbox-only 1 commit. `main/base@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`, tests/source/Spec 불변, PR feedback 0.
- **Contract / code:** [case model](../../src/hmda_reliability/reliability/evaluation/case_result.py) `_validate_case_name`은 `value.strip()` nonblank만 확인하므로 `normal\n| forged ...`를 금지하는 조건이 없습니다. [reporter](../../src/hmda_reliability/reliability/evaluation/reporter.py) `_case_line` (L65–79)는 case_name/evidence refs 등을 그대로 Markdown table cell에 삽입합니다. [changed report tests](../../tests/reliability/test_evaluation_report.py) L75–248은 safe fixed strings만 검사. [Evaluation Spec](../../openspec/specs/reliability-evaluation-report/spec.md)의 현재 문구에서 임의 문자열 escaping 형식을 **MUST**로 단정하지 않습니다.
- **Disposable falsifier:** `case_name="normal\n| forged | - | - | PASS | PASS | - | - | - | - | - |"`를 동일 f-string 구조로 조립하면 한 case row가 **두 물리적 행**으로 분리됩니다. 이는 source에서 보이는 입력 검증과 문자열 조립의 정적 결합을 강화하는 **별도 stdlib 문자열 probe**이며, **원본 Pydantic/reporter 모듈·Markdown renderer/pytest 미실행**입니다. 실제 소비자에 위조 PASS 행이 어떻게 렌더되는지는 미확인입니다.
- **Disconfirmation:** Reporter가 `PASS`/ `FAIL`를 `detection_passed`로 계산하는 로직 자체를 우회하거나 evaluation summary count를 변경하는 증거는 없습니다. 위험은 **human-readable Markdown representation의 구조 오염**이며 domain result의 truth 변경으로 과장하지 않습니다.

| ID | Severity | Disposition / scope relation | Evidence and next |
| --- | --- | --- | --- |
| C16 refined | 🟡 Minor **conditional output integrity** | **Keep pre-existing reporter/test `follow_up`, not current_required** | Pipe와 newline을 모두 escape/validate할 정책을 Reliability reporter owner가 결정하면, 허용 입력과 rendered row/column count 및 raw data 보존을 확인하는 component negative oracle을 추가. #277의 approval/recovery integration으로 내부 reporter 결함을 이관하지 않음. |
| C14 | 🟡 Minor / uncertain contract | **Keep R11 `unknown` (Spec owner)** | Normal-case false-positive inverse MUST는 정본에 명시되지 않음. Spec owner 결정 전 test blocker 아님. |

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | R11→R12 head, case validator→reporter→test→Spec 정적 대조 | Inbox-only 1 commit; 네 PR 변경 test 경로 비중복. |
| ✅ Pass | Disposable stdlib Markdown row-template probe | Nonblank `case_name`에서 물리적 row 1→2; 원본 module/rendered UI 검증 아님. |
| ✅ Pass | **원격** current-head prospective-merge CI | [CI Lite 40266177395](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40266177395): merge `400b78d2` (base `ea39a4fd` + head `7ceb3809`), `tests/reliability` **268 passed in 27.84s**. 오염 입력 미포함. |
| ⚪ Not Verified | 원본 reporter/Pydantic newline, Markdown renderer, local pytest, 독립 specialist, #277 integration | 이번 회차 미실행. |

**Next:** C16은 reporter owner의 escaping/validation policy 이후 원본 module 및 renderer에 대해 좁게 검증. C14는 정본 owner 판단을 기다립니다. #277은 선행 #269–#276 병합 뒤 approval→recovery→revalidation 경계만 소유. 인간 Ready·approval·merge 변경 없음.

## R13 · 2026-10-26 KST · Shared Git-Hook Handoff Feasibility and CI Negative Control

> [!IMPORTANT]
> **Research → Plan → Review / bounded owner-decision handoff.** R12의 domain-specific source risks를 중복 발견으로 재등록하지 않고, 네 PR이 #277에 넘긴 **shared pre-push Git environment fix**의 실제 writable owner를 반증했습니다. **새 PR-introduced product/test defect는 확정하지 않았으며** scope 변경·코드 수정·사람의 readiness 판단은 하지 않았습니다.

- **Revision:** R12 reviewed pre-write `7ceb3809a3148787e3e75a856046b03e4b08c7a8` → authoritative R13 pre-write `8928234c941e29b5643e159d11ace9de7e2cec61`: compare shows **exactly one Inbox review-file commit**, with unchanged source/test/Spec and main `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`. PR feedback 0. #277 head `74ac659d084fadd5e93900b132ef5b995ef8d919` is still Draft, initial base `81fe44b2126e1c013dd2dd68259f12e34088c47b`.
- **Research perspectives:** (1) observable failure/negative oracle in existing domain tests; (2) real shared hook→fixture process boundary and past incident; (3) exact #277 exclusive file ownership; (4) revision-specific CI step evidence. **Plan:** preserve the shared root cause once (#270 F3 / #271 report), record only each PR's affected handoff and avoid inventing a local fix or widening #277's scope.
- **Shared path/contract:** [pre-push command](../../lefthook.yml) `pytest-affected: uv run --no-sync pytest --testmon --testmon-forceselect`; [CI test Git helper](../../tests/scripts/ci/helpers.py) `git(repo, *args)` invokes `subprocess.run(..., cwd=repo)` without an explicit clean `env`; [CI fixture](../../tests/scripts/ci/conftest.py) `repo` creates and commits a disposable repository, while `tool_env` inherits `os.environ`. Inherited `GIT_DIR/GIT_INDEX_FILE` can therefore redirect Git operations despite `cwd`. Actual earlier contamination and isolated-hook retry are documented in [#270 F3](https://github.com/mols3131d/hmda-data-reliability/blob/agent/test/audit-data-operations-design/inbox/github-270-audit-data-operations-design/02-review-data-operations-tests.md) and [#271 hook report](https://github.com/mols3131d/hmda-data-reliability/blob/agent/test/audit-data-platform-design/inbox/github-271-audit-data-platform-design/07-report-pre-push-environment.md); **this R13 did not rerun them**.
- **#277 scope countercheck:** [#277 owning plan](https://github.com/mols3131d/hmda-data-reliability/blob/agent/test/audit-cross-domain-design/inbox/github-277-audit-cross-domain-design/00-plan-cross-domain-tests.md) says *only* its exclusive tests and Inbox are writable. It reserves `tests/scripts/ci/test_ci_workflow.py` for test changes, but **not** `lefthook.yml`, `tests/scripts/ci/helpers.py`, or `tests/scripts/ci/conftest.py`. The same plan says common settings/CI fixes are handed to #277: a concrete **write-scope/owner contradiction**, not evidence that the fix has happened. A new cross-domain test alone cannot repair the inherited environment in the existing hook/helper. Resolve by human assignment of a separate shared-tooling change or explicit revision of #277's writable scope; no automatic scope expansion.
- **CI counterevidence:** latest [#277 CI 40200923996](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40200923996) succeeded against its initial base `81fe44b2126e1c013dd2dd68259f12e34088c47b`, but **Run selected tests / Validate Python / Sync dependencies were skipped**. Current main is `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`, and #277 is Draft with no integrated test changes. Thus green #277 CI is **not** a shared-hook regression or integrated cross-domain PASS.
- **Reliability-specific falsifier:** [#272 current audit H4](02-review-current/README.md) records parent branch/index contamination during broad hook and delegates permanent shared-hook isolation to #277. The changed [evaluation report test](../../tests/reliability/test_evaluation_report.py) is a domain oracle; it does not exercise inherited Git-local vars or prove the shared hook safe. H2's missing THEN in [evaluation Spec](../../openspec/specs/reliability-evaluation-report/spec.md) also requires a **Spec owner**; #277's current write scope excludes `openspec/**`. Prior C16 Markdown representation risk remains separate.

| ID | Severity | Decision / scope relation | Evidence and next |
| --- | --- | --- | --- |
| C17 | 🟡 Minor handoff integrity; underlying H4 🟠 Major | **Accept `scope_decision` / shared-tooling dependency, not #272 `current_required`** | #277 is named for H4 permanent fix but excludes `lefthook.yml` and Git helper/fixture. Human must authorize actual shared-tooling owner and regression scenario; #272 test-only lane stays unchanged. |
| C18 | 🟡 Minor scope integrity | **Keep existing H2 `scope_decision` (not new Spec defect)** | Evaluation Spec missing THEN is not fixed by #277 integration tests, and #277's `openspec/**` write exclusion means a separate Spec owner or explicit scope amendment is needed. Do not silently write Spec in this PR. |
| C19 | 🔵 Note | **Drop / domain CI or #277 green proves hook safety** | Neither check executes the contaminated local pre-push child under inherited Git vars; #277 runtime test step is skipped. |

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | R12→R13 pre-write head and four PR ownership static recheck | R12→current exactly one review Inbox file per PR; exclusive authored tests remain disjoint (`tests/hmda_data/**`, `tests/data_operations/**`, `tests/data_platform/**` + `tests/dbt/**`, `tests/reliability/**`). No new PR feedback. |
| ✅ Pass | Current remote PR CI step/status inspection | [CI Lite 40271177747](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40271177747) succeeded on pre-write head `8928234c941e29b5643e159d11ace9de7e2cec61` + main `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`; `Run selected tests` and `Validate Python` succeeded. This is **remote CI**, not local pre-push regression. |
| ✅ Pass | #277 historical CI step falsification | [CI 40200923996](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40200923996) success with **Run selected tests skipped**, old base and no integrated changes; not integration PASS. |
| ⚪ Not Verified | This-run local pytest, Git fixture environment injection, real hook run, original module fault, independent specialist, #277 integration | None executed in this run. Earlier isolated probes belong to their original reports; they are not R13 direct validation. |

**Next:** Human owner to reconcile #277's shared-tooling/Spec handoff wording with its exclusive write policy (separate owner/PR or explicit authorized scope change). On the authorized lane, add a **disposable parent+child Git regression** asserting parent HEAD/index/config unchanged under inherited Git-local vars and child commit isolated; verify real hook child environment. Keep each domain's existing source risks and cross-domain integration tests separate. Recheck post-write head and CI before any future confidence claim; no Ready/approval/merge/thread resolution.
