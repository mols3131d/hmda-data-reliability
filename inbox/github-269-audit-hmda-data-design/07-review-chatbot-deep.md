---
type: review
title: HMDA Data Chatbot Deep Review
description: PR #269 테스트 변경의 챗봇 심층 리뷰와 세션 간 지속 검토 상태를 기록합니다.
tags:
  - "capability:test-design"
  - "multi-perspective"
---

# HMDA Data Chatbot Deep Review

> [!IMPORTANT]
> **Blocked (review in progress)** — 새 `current_required` 결함은 아직 확정하지 않았습니다. 이는 머지 불가 판정이 아니라 이번 챗봇 리뷰의 검토 범위와 독립 재검증이 아직 닫히지 않았다는 뜻입니다. 로컬 테스트를 직접 실행하지 않았으므로 기존 CI·독립 리뷰 기록을 본 검토의 재현 결과로 간주하지 않습니다.

- **Target** — [PR #269](https://github.com/mols3131d/hmda-data-reliability/pull/269), owning branch의 Inbox.
- **Revision** — base `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`; reviewed code/head `83a4dbc5d8e115c6437212ddc7cabc5f99a70bdb` (2026-10-26 KST 1차 확인). 이후 Inbox-only commit은 반드시 test blob 변경 여부를 대조합니다.
- **Scope** — 변경 테스트 6파일의 diff, 기존 8파일 전수 목록·하위 검토 보고서, EDA 숫자 oracle 및 실패 경로를 1차 대조했습니다. 생산 코드의 직접 실행과 정본 전 항목 trace는 아직 미완료입니다.

## Findings

현재 직접 확인한 범위에서 **확정된 신규 finding 없음**. 이는 PR 전체의 `clear` 또는 merge readiness 검증 완료를 의미하지 않습니다.

## Perspectives

| Perspective | Reviewer / Method | Focus | Assessment and Evidence |
| --- | --- | --- | --- |
| Oracle 정확성 | 동일 세션 정적 대조 | EDA 4관측값의 quartile 및 null 분포 | `loan_amount` [-100,-20,40,200]의 p25=-40·median=10·p75=80은 손계산과 일치. `tests/hmda_data/eda/test_eda.py` diff |
| 실패·복구 | 동일 세션 반증 점검 | partition INSERT 실패, overwrite pair 복구 | 원래 전체 row/bytes를 직접 비교하고 constraint cause를 분리하는 assertion이 추가됨. `test_ingestion_partition.py`, `eda/test_eda_evidence.py` diff |
| 격리·소유권 | 동일 세션 boundary 대조 | synthetic 원본, 잠금, 분리 경로 | invalid fraction 시 source byte 불변·output 부재 및 lock 실패 시 row 불변 테스트 존재. 제품·공용 파일 변경 없음. PR 변경 경로 목록 |

## Candidate Decisions

| ID | Perspectives | Candidate | Decision | Rationale | Finding |
| --- | --- | --- | --- | --- | --- |
| C1 | Oracle | 분위수 계산이 의도적으로 부정확할 수 있음 | Drop | 입력값의 독립 계산이 추가된 fixed oracle과 일치. 실제 결함 근거 없음 | — |
| C2 | 실패·복구 | 두 번째 evidence replace 실패의 기존 pair 복구가 완전하지 않을 수 있음 | Open | 복구 시나리오가 존재하지만 mock 경로/backup cleanup과 구현은 다음 회차에서 독립 추적 필요 | — |
| C3 | 격리 | partition 롤백 테스트가 단순 fixture 예외를 오인할 수 있음 | Open | `duckdb.ConstraintException` cause와 변경 전후 전체 row 동일성을 확인함. 실제 실행·transaction 구현은 미확인 | — |

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Diff/path 소유권 정적 대조 | 변경 18파일 중 테스트는 `tests/hmda_data/**` 6개, 나머지 PR 소유 Inbox로 확인. 다른 세 PR와 겹치는 변경 경로 없음 |
| ✅ Pass | EDA 고정 분포 계산 | `test_eda.py`의 숫자 입력과 expected quartile 손계산 대조 |
| ⚪ Not Verified | 정확한 소스·정본 Spec 전수 trace | 기존 [audit report](05-report-hmda-data-audit.md)와 [independent review](06-review-hmda-data-independent.md)의 주장을 대체할 직접 확인 필요 |
| ⚪ Not Verified | pytest/CI 재실행·negative control | PR의 197 passed/CI 증빙은 읽었지만 이 세션에서 실행하지 않음 |

## Risks and Limits

- 차트 HTML의 `var spec =` 파싱은 생성 결과를 검사하지만 renderer 세부에 결합할 가능성이 있습니다. 실제 contract·실패 영향 확인 전에는 finding으로 승격하지 않습니다.
- EDA JSON/Markdown cleanup 및 target schema drift 등 기존 보고서의 known limits를 이 PR의 새 회귀로 분류하지 않습니다.

## Continuation

- **State:** `mols-loops deep`; Prepare → RPI Research/Plan/Work/Review 1차(동일 세션의 순차 관점) 완료, 독립 신규 specialist 게이트 및 완전한 contract trace 미완료. 이 기록은 제품/테스트를 수정한 증거가 아니라 리뷰 checkpoint입니다.
- **Next:** `tests/hmda_data/eda/test_eda_evidence.py`의 replace mock과 `src`의 evidence write 구현, partition staging/transaction 구현을 정본 Spec과 줄 단위 대조. 합성 파일 helper의 path sanitization 반례 및 과거 H1–H8 disposal을 현행 근거로 spot-check.
- **Revalidation trigger:** main/base, head의 test/source/Spec blob, CI 상태, 새로운 feedback이 바뀌면 기존 판단을 stale로 표시하고 영향을 받는 영역을 다시 조사합니다. 전수 파일 수나 이전 에이전트가 표시한 `clear`를 독립 검증으로 대체하지 않습니다.
- **Boundary:** 이 문서는 비정본입니다. 공유 CI/Git fixture와 교차 도메인 계약은 [#277](https://github.com/mols3131d/hmda-data-reliability/pull/277)에서 선행 PR을 취합한 뒤 검증합니다. 승인·merge·thread resolution은 수행하지 않습니다.

## R2 · 2026-10-26 Source and CI Revalidation

- **Research:** main/base `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686` 유지. R1 code head `83a4dbc5d8e115c6437212ddc7cabc5f99a70bdb`부터 현재 head `3cd6f778fc36aea71868f859d1eb971ea74433dd`까지 Inbox review 추가 1건뿐이며 test/source/Spec 변경은 없다.
- **Plan/Review:** 기존 C2는 [evidence writer](https://github.com/mols3131d/hmda-data-reliability/blob/ea39a4fd6c8f483509cf00a1d1114feb4ef3b686/scripts/run_actual_source.py#L91-L159)의 second-replace rollback 및 [test](https://github.com/mols3131d/hmda-data-reliability/blob/83a4dbc5d8e115c6437212ddc7cabc5f99a70bdb/tests/hmda_data/eda/test_eda_evidence.py#L155-L210)에서 create/overwrite byte equality를 확인해 **Drop**. C3는 [transaction](https://github.com/mols3131d/hmda-data-reliability/blob/ea39a4fd6c8f483509cf00a1d1114feb4ef3b686/src/hmda_reliability/hmda_data/ingestion/partition.py#L323-L383)과 [real constraint failure test](https://github.com/mols3131d/hmda-data-reliability/blob/83a4dbc5d8e115c6437212ddc7cabc5f99a70bdb/tests/hmda_data/test_ingestion_partition.py#L237-L271)로 **Drop**. 새 current_required 없음.
- **Open / pre-existing H5 variant (scope_decision):** evidence writer의 첫 JSON replace 실패는 기존 backup을 남길 수 있는데 test는 두 번째 replace 실패만 주입한다. 현재 pair 손상으로 일반화하지 않고, 기존 [H5](05-report-hmda-data-audit.md)와 묶어 첫 replace 실패의 backup cleanup oracle을 #277에 인계한다. Production 변경은 이 PR 범위 밖이다.
- **Validation:** GitHub [CI Lite 40218900666](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40218900666) log에서 **197 passed in 7.89s**, selected Python check 성공 확인. 이번 회차 로컬 pytest/negative control은 **Not Verified**; 별도 독립 specialist 검토도 **Not Verified**. 동일 세션의 source·oracle·ownership·CI 관점 대조는 독립 리뷰가 아니다.
- **Boundary/Next:** 수정 소유권은 이 PR Inbox뿐. 다른 PR 테스트와 경로 중복 없음. #277은 선행 PR 병합 후 동일 main revision에서 교차 도메인·공용 Git fixture를 검증해야 한다. Review gate는 독립 specialist 미실행으로 `blocked`(PR 승인/merge 판단 아님). 이 기록의 reviewed head는 Inbox-only commit 직전 SHA이며 다음 회차에 다시 대조한다.

## R3 · 2026-10-26 KST · Fresh-Head Challenge and Handoff

> [!NOTE]
> **Research → Plan → Review:** Compared previous R2 head `3cd6f778fc36aea71868f859d1eb971ea74433dd` to authoritative head `ab3d2fc734a3900b8bec31e1ff330aa2e72c636f` and main/base `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`: only this Inbox review changed, so earlier code/Spec/test findings remain revision-applicable. No new PR conversation feedback. The plan was to challenge one unresolved inference against a separate source/test path, keep test-only PR ownership, and validate latest remote CI without claiming local execution. This is same-session multi-perspective analysis, **not** isolated independent review.


### R3 · HMDA Data · H5 Ownership Correction

- **Candidate C6 — 🔵 Note / Accept as follow_up, not current_required:** [Evidence writer lines 122–157](../../scripts/run_actual_source.py) copies an existing JSON to `.json.bak`, then calls `json_tmp.replace(json_path)` **outside** the inner rollback `try`. If that *first* replace raises, the outer `finally` deletes `.tmp` files but does not delete the `.bak`. [Changed test lines 155–210](../../tests/hmda_data/eda/test_eda_evidence.py) injects the **second** replace failure only. Therefore the specific first-replace backup-orphan path is not protected. The old JSON and Markdown remain in place in this branch; do not misreport a proven corrupt pair or executed failure. This script-internal pre-existing cleanup issue belongs to the HMDA Data/source owner (and any domain test correction to #269's lane), **not automatically #277's cross-domain lane**. A disposable first-replace fault injection with exact pair bytes and `.bak/.tmp` absence would distinguish it.
- **Disposition:** R2 C2/C3 remain Drop; the H5 cleanup variant remains an unexecuted conditional source risk. No new confirmed `current_required`; independent specialist gate still **blocked**. #277 should retain only genuine Source→Bronze→gate→dbt and shared fixture integration after prerequisite merges.

### R3 Validation and Next Transition

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Remote revision and changed-path comparison | `3cd6f778fc36..ab3d2fc734a3` is one Inbox-only commit; no new test/source/Spec diff; domain test file paths do not overlap #269/#270/#271/#272. |
| ✅ Pass | Latest remote CI selected-suite log | [CI Lite 40223479777](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40223479777), job `121259859470`: **197 passed in 6.65s** with selected Python checks success on prospective merge. GitHub runner evidence only. |
| ⚪ Not Verified | This session's local pytest, targeted fault injection, and independent specialist | No local execution or isolated reviewer; earlier run reports are historical evidence, not this run's result. |
| ⚪ Not Verified | [#277](https://github.com/mols3131d/hmda-data-reliability/pull/277) integrated contract test | Still Draft at `74ac659d084fadd5e93900b132ef5b995ef8d919`, initial base `81fe44b2`; prerequisite domain PRs remain unmerged. |

**Next:** Re-check exact head/base/CI before reuse. Follow the candidate-specific owner and counterexample above; run only the narrow relevant fault/alias/integration test in a disposable isolated environment if authorized. Preserve the difference between remote CI success, static inference and independent review. Do not modify shared code/Spec or approve/merge. This reviewed head is the **pre-Inbox-update** SHA; verify the resulting commit changed only this document.


## R4 · 2026-10-26 KST · Synthetic Source-Deletion Countercheck

> [!NOTE]
> **Assessment: blocked for the independent specialist gate; no newly confirmed `current_required`.** This loop closes the prior synthetic-path counterexample with source, Spec and actual test-oracle inspection rather than repeating R3's EDA backup finding.

- **Target** — PR #269, `agent/test/audit-hmda-data-design`, existing review artifact only.
- **Revision** — previous R3 reviewed head `ab3d2fc734a3900b8bec31e1ff330aa2e72c636f` → authoritative pre-write head `10d4912e0d6c8afc91531085357d3c142d54987b`; compare is one Inbox-only commit. Current `main@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`. Source/Spec/test blobs unchanged; PR conversation has no new feedback.
- **Scope** — `write_case_file` path safety and source preservation, changed synthetic negative tests, canonical synthetic Spec, domain ownership, latest prospective-merge CI. No implementation/shared file changes.

### R4 Candidate Decision

| ID | Severity | Scope relation / disposition | Evidence and counterevidence | Action |
| --- | --- | --- | --- | --- |
| C7 | 🔵 Note | `contract_dependency` / **Drop** | [Canonical synthetic Spec](../../openspec/specs/hmda-data-synthetic-defects/spec.md), `Isolated synthetic output`, requires rejection of output traversal and preservation of input files. [Writer](../../src/hmda_reliability/hmda_data/synthetic/_writer.py), `_prepare_case_dir` and `_validate_source_paths`, rejects empty, `.`, `..`, path-containing case names before any `rmtree`, and checks both resolved file membership and intermediate symlink entries before deleting a case directory. [Changed tests](../../tests/hmda_data/test_synthetic.py), `test_write_case_file_rejects_unsafe_case_name` and existing `test_synthetic_case_preserves_sources_inside_case_directory`, assert outside sentinel bytes, no output-root creation, and original source bytes across direct, relative, glob and symlink aliases. The hypothesis that this test-only PR lacks *any* traversal/source-preservation oracle is refuted. No claim that every platform-specific alias or TOCTOU race is tested. | Do not duplicate as a new defect. Keep narrowly scoped source/alias race work separate unless an authorized contract and reproducible counterexample appear. |

**Research → Plan → Review:** Tested the R1 continuation's path-sanitization concern against the current writer's validation-before-delete ordering, canonical MUST, and test assertions. The tests observe real file bytes and a DuckDB-backed case generator rather than only mock calls; static review does not replace a fresh filesystem runtime run. R3 C6 (first JSON replace `.bak` orphan) remains a pre-existing HMDA Data source-owner follow-up, **not** a #277 internal cleanup assignment. R2 C2/C3 remain Drop.

### R4 Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Revision and path ownership static comparison | `ab3d2fc7..10d4912e` is this Inbox file only; #269's six changed tests are confined to `tests/hmda_data/**` and do not overlap #270/#271/#272 test changes. |
| ✅ Pass | Remote prospective-merge CI log inspection | [CI Lite 40228407524](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40228407524), job `121274710778`, merge `3956d24f6245759538fdb30817f0bd7dfda96e05` of head `10d4912e` into base `ea39a4fd`: **197 passed in 8.50s**; selected Python checks succeeded. |
| ⚪ Not Verified | Local pytest, first-replace `.bak` fault injection, symlink race/stress or isolated specialist | None executed in this continuation; historical tests and current remote CI are separate evidence tiers. |
| ⚪ Not Verified | #277 integrated interface validation | Prerequisite PRs unmerged; #277 still Draft at `74ac659d084fadd5e93900b132ef5b995ef8d919`, with initial base `81fe44b2` one commit behind current main. |

**Next:** Preserve C7 Drop unless an executable counterexample refutes the actual guard. For R3 C6, run only a disposable first-`json_tmp.replace` fault and assert old JSON/Markdown exact bytes plus no orphan `.bak/.tmp`; route any source correction to HMDA Data. #277 should test Source→Bronze→gate→dbt and shared fixture boundaries after domain integration, not absorb the internal evidence-writer cleanup. Recheck post-write head, CI and any new feedback; no approval/merge decision.

## R5 · 2026-10-26 KST · Evidence-Pair Cleanup Failure Matrix

> [!NOTE]
> **Handoff / independent review pending.** 기존 H5의 **서로 다른 실패 지점**을 분리해 반증했습니다. 새 PR-introduced defect 확정은 없으며, 제품 코드·테스트·Spec은 수정하지 않았습니다.

- **Revision:** R4 pre-write `10d4912e0d6c8afc91531085357d3c142d54987b` → authoritative pre-write `1b095077d92ada7bb252075e0ff3ec98ed87bc66`는 이 Inbox 파일의 단일 commit뿐. `main/base@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`; code/test/Spec 변경 없음.
- **Research → Plan → Review:** R3의 첫 JSON replace 실패와 별도로, [writer](../../scripts/run_actual_source.py) `write_evidence`의 **Markdown 교체 성공 뒤 JSON backup 삭제 실패**를 추적하고 [EDA 정본 Spec](../../openspec/specs/hmda-data-eda-descriptive-evidence/spec.md)의 JSON↔Markdown key-metric 일치 조건 및 [변경 테스트](../../tests/hmda_data/eda/test_eda_evidence.py)와 대조. 정상 rollback이라는 반대 가설은 두 번째 replace 실패에는 성립하지만, backup `unlink` 실패에는 적용되지 않습니다.

| ID | Severity | Decision / Evidence | Next |
| --- | --- | --- | --- |
| C8 (existing H5 refined) | 🟠 Major **if reached** | **Keep pre-existing source risk / not new current_required.** `md_tmp.replace(markdown_path)` 성공 후 `json_backup.unlink()`가 `OSError`를 내면 같은 `except`가 backup JSON만 원상복원하고 이미 교체한 Markdown은 복원하지 않습니다. 따라서 **old JSON + new Markdown**이라는 Spec 불일치 상태가 가능. R3 C6의 **첫 JSON replace 실패 시 .bak 잔존**과 다른 경로입니다. 현재 변경 테스트는 **두 번째 replace 실패**만 주입해 이 상태를 검출하지 않습니다. 실행 재현은 없음. | HMDA Data source owner가 임시 pair에서 `.json.bak` `unlink` 실패를 주입해 정확한 old/new bytes와 잔여 파일을 관측한 뒤 rollback/cleanup 계약을 결정. 테스트 owner는 해당 회귀 oracle을 domain lane에 연결; #277에 내부 cleanup을 떠넘기지 않음. |

### R5 Validation and Continuation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | R4→head 비교 및 정본/소스/테스트 분기 정적 추적 | 위 exact SHA; PR의 변경 테스트는 `tests/hmda_data/**` 전용이며 #270/#271/#272와 경로 충돌 없음. |
| ✅ Pass | 최신 **원격** prospective-merge CI log | [CI Lite 40232604636](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40232604636), job `121287337590`: **197 passed in 8.39s**, selected Python checks 성공. Cleanup-fault 주입은 이 CI에 없음. |
| ⚪ Not Verified | 로컬 pytest, `unlink` fault injection, 독립 specialist | 이번 회차 미실행; C8은 코드 제어 흐름에 따른 조건부 반례. |
| ⚪ Not Verified | #277 통합·인간 승인 | #277은 선행 PR 미병합 Draft. |

**Next:** 첫-replace orphan과 backup-cleanup mismatch를 별도 fault로 재현해 영향/우선순위를 분리하고, 실제 fix는 source owner가 결정. #277은 선행 병합 후 Source→Bronze→gate→dbt 통합과 공용 fixture만 검증. 이 R5의 reviewed head는 **Inbox 갱신 전** SHA이며 갱신 후 CI는 별도 확인합니다.
