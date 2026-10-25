---
type: review
title: Reliability Chatbot Deep Review
description: PR #272 테스트 변경의 챗봇 심층 리뷰와 세션 간 지속 검토 상태를 기록합니다.
tags:
  - "capability:test-design"
  - "multi-perspective"
---

# Reliability Chatbot Deep Review

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
