---
type: review
title: Data Operations Chatbot Deep Review
description: PR #270 테스트 변경의 챗봇 심층 리뷰와 세션 간 지속 검토 상태를 기록합니다.
tags:
  - "capability:test-design"
  - "multi-perspective"
---

# Data Operations Chatbot Deep Review

> [!IMPORTANT]
> **Blocked (review in progress)** — 새 `current_required` 결함은 아직 확정하지 않았습니다. 이는 머지 불가 판정이 아니라 이번 챗봇 리뷰의 검토 범위와 독립 재검증이 아직 닫히지 않았다는 뜻입니다. 로컬 테스트를 직접 실행하지 않았으므로 기존 CI·독립 리뷰 기록을 본 검토의 재현 결과로 간주하지 않습니다.

- **Target** — [PR #270](https://github.com/mols3131d/hmda-data-reliability/pull/270), owning branch의 Inbox.
- **Revision** — base `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`; reviewed code/head `5dd84ee53e56f089f6771d6a2ff9ae23f4105b29` (2026-10-26 KST 1차 확인). 이후 Inbox-only commit은 반드시 test blob 변경 여부를 대조합니다.
- **Scope** — 변경 test 두 파일의 diff, domain inventory 6파일, artifact drift·lifecycle no-write oracle 및 예약된 #277 범위의 소유권 대조.

## Findings

현재 직접 확인한 범위에서 **확정된 신규 finding 없음**. 이는 PR 전체의 `clear` 또는 merge readiness 검증 완료를 의미하지 않습니다.

## Perspectives

| Perspective | Reviewer / Method | Focus | Assessment and Evidence |
| --- | --- | --- | --- |
| 회귀 검출력 | 동일 세션 정적 대조 | 단독 artifact drift 검증 | `@parametrize('artifact_field', ['manifest_path','run_results_path'])`로 두 단독 변경이 모두 기존 JSON pair bytes 보존을 확인. `tests/data_operations/test_dbt_runner.py` |
| 실패 의미 | 동일 세션 반증 점검 | dbt 프로세스 timeout/start failure | timeout 인수·typed error cause·context를 검사하지만 subprocess는 fake boundary. 실제 dbt 품질 결과와 혼동하지 않음 |
| 무변경성·소유권 | 동일 세션 상태 관측 검토 | lifecycle 비교·원본 row·artifact bytes·파일 집합 | 전후 전체 row 및 파일 보존 oracle을 추가하고 허용되는 lock 파일을 명시. `tests/data_operations/test_incident_lifecycle.py` |

## Candidate Decisions

| ID | Perspectives | Candidate | Decision | Rationale | Finding |
| --- | --- | --- | --- | --- | --- |
| C1 | 회귀 검출력 | run_results-only drift 사례가 누락되었음 | Drop | artifact_field에 `run_results_path`가 명시되어 있고 current pair byte 보존을 함께 확인 | — |
| C2 | 실패·격리 | fake subprocess만으로 실제 dbt 경로가 충분히 검증됨 | Drop | 이 테스트는 runner 경계, 실제 dbt·E2E의 책임은 별도 테스트/후속 PR. 해당 claim을 전체 실행 보장으로 사용하지 않음 | — |
| C3 | 무변경성 | lifecycle이 lock 파일 외 다른 side effect를 허용할 수 있음 | Open | 기존 파일 전후 집합 비교의 정확한 기대와 lock 생성 시점을 구현에서 독립 확인 필요. 범위 밖 조합은 #277 소유 | — |

## Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Diff/path 소유권 정적 대조 | 변경 6파일 중 test 2개만 `tests/data_operations/**` 수정, 예약된 quality gate/system recovery test 변경 없음. 세 PR와 path 중복 없음 |
| ✅ Pass | Candidate drift 두 방향 검토 | `test_dbt_runner.py`의 manifest·run_results 매개변수와 `old_manifest`·`old_results` byte assertions 확인 |
| ⚪ Not Verified | runner와 lifecycle implementation·정본 Spec 전체 대조 | 이번 회차는 diff와 [기존 domain report](02-review-data-operations-tests.md) 위주; 호출경계 source와 Spec 직접 trace 추가 필요 |
| ⚪ Not Verified | 실제 dbt/pytest/CI 재실행 | PR의 57 passed 및 1,084 passed 증빙은 재실행하지 않음 |

## Risks and Limits

- 기존 Git fixture의 hook-local 환경 상속 문제는 공통 문제로 보고되었고, 이번 PR scope 안에서 설정을 임의 수정하면 병렬 작업 충돌을 유발할 수 있습니다.
- #277의 실제 시간/identity E2E oracle은 이 PR의 fake-process 테스트와 별개입니다.

## Continuation

- **State:** `mols-loops deep`; Prepare → RPI Research/Plan/Work/Review 1차(동일 세션의 순차 관점) 완료, 독립 신규 specialist 게이트 및 완전한 contract trace 미완료. 이 기록은 제품/테스트를 수정한 증거가 아니라 리뷰 checkpoint입니다.
- **Next:** artifact promotion implementation의 두 파일 atomicity와 result-only drift identity를 추적하고, lifecycle의 read-only 경계 및 projection lock 허용 범위를 source/Spec에 대조. 57-test suite 중 예약 4파일의 검토·제외 이유를 현행 코드와 교차 검증.
- **Revalidation trigger:** main/base, head의 test/source/Spec blob, CI 상태, 새로운 feedback이 바뀌면 기존 판단을 stale로 표시하고 영향을 받는 영역을 다시 조사합니다. 전수 파일 수나 이전 에이전트가 표시한 `clear`를 독립 검증으로 대체하지 않습니다.
- **Boundary:** 이 문서는 비정본입니다. 공유 CI/Git fixture와 교차 도메인 계약은 [#277](https://github.com/mols3131d/hmda-data-reliability/pull/277)에서 선행 PR을 취합한 뒤 검증합니다. 승인·merge·thread resolution은 수행하지 않습니다.


## R2 · 2026-10-26 KST · Contract, Cleanup and CI Revalidation

> [!NOTE]
> **Assessment: blocked (independent specialist gate not performed), no confirmed new `current_required`.** This section updates R1 candidates without treating previous reviewer claims or remote CI as local execution.

- **Research / freshness:** authoritative PR head `2a6aa3117e1725827029b26f105da49c76338e12`, base `ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`. Comparing R1 code `5dd84ee53e56f089f6771d6a2ff9ae23f4105b29` to head shows **one added file only: this Inbox review**. The two tests, main source and Spec were not changed in that interval. PR conversation has no new feedback.
- **Plan:** Reconcile R1 C3 against the actual lifecycle implementation and the stage/lifecycle Specs; challenge promotion's failed-copy cleanup separately from the already-tested second-replace rollback. Only this PR-owned Inbox may change.
- **Review / sequential perspectives:** Source-contract, negative/fault-injection, CI, and cross-PR ownership were checked sequentially in this session. They are **not** independent specialist reviews.

### R2 Candidate Decisions

| ID | Severity | Scope relation / disposition | Evidence and counterevidence | Next |
| --- | --- | --- | --- | --- |
| C3 | 🔵 Note | `contract_dependency` / **Drop** | [Lifecycle implementation](../../src/hmda_reliability/data_operations/incident_lifecycle.py) opens DuckDB with `read_only=True`, calculates profile/impact/draft and uses a shared artifact lock whose only expected file-side effect is `.artifact-promotion.lock`. [Changed test](../../tests/data_operations/test_incident_lifecycle.py) compares ordered full rows, both artifact byte streams and complete file membership, allowing only that lock. The original conjecture that the test silently permits other newly created files is refuted. This is static inspection, not a proof against arbitrary external writes. | Do not duplicate R1 C3 as a finding. |
| C4 | 🟡 Minor | `independent_requirement` / **Accept as follow_up; not current_required** | [Promotion source lines 386–424](../../src/hmda_reliability/data_operations/runner.py) runs `shutil.copyfile(source, staged_path)` **before** appending that item to `staged_promotions`; on an OSError during the current copy, cleanup iterates only previously appended items. A partially created `*.next` for the failing item can therefore survive. [Domain test lines 850–883](../../tests/data_operations/test_dbt_runner.py) injects failure on second `Path.replace` and asserts restored current pair, **not** failure during the first/second copy or orphan `.next` absence. This is a reachable conditional control-flow gap, **not a locally reproduced failure**; prior current pair is not shown corrupted. It predates this test-only PR and is outside the authorized source-edit boundary. | Data Operations source owner: consider a separate production cleanup correction; domain test owner: inject partial `copyfile` failure and assert old pair bytes plus no orphan `.next`. Do **not** assign internal runner cleanup to #277 by default. |
| C5 | 🔵 Note | `contract_dependency` / **Drop** | [Stage Spec](../../openspec/specs/data-operations-stage-execution/spec.md) requires process failure and missing artifact to be domain failures, but does not make every temporary staging-file cleanup error a new stage success criterion. No evidence that C4 alters the completed dbt run result or existing current pair. | Keep the distinction between cleanup hygiene and committed pair integrity. |

### R2 Validation and Handoff

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | GitHub head comparison and path ownership | `5dd84ee5..2a6aa311`: Inbox review addition only; changed test files remain `tests/data_operations/test_dbt_runner.py` and `test_incident_lifecycle.py`; other PR test lanes do not overlap. |
| ✅ Pass | Source and Spec static control-flow inspection | [Lifecycle](../../src/hmda_reliability/data_operations/incident_lifecycle.py), [promotion](../../src/hmda_reliability/data_operations/runner.py), [stage Spec](../../openspec/specs/data-operations-stage-execution/spec.md), [lifecycle Spec](../../openspec/specs/data-operations-incident-lifecycle/spec.md). C4 is conditional inference, not executed reproduction. |
| ✅ Pass | Current remote CI job log inspection | [CI Lite 40218904066](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40218904066), job `121245976491`: prospective merge checkout, `tests/data_operations` **57 passed in 42.05s** and selected Python checks succeeded. GitHub runner only. |
| ⚪ Not Verified | Local pytest, partial-copy fault injection and mutation controls | No local execution in this run; existing historical mutant proof covers **results-only identity**, not C4. |
| ⚪ Not Verified | New independent DualVantage specialist gate and cross-domain integration | No isolated specialist context was available. [#277](https://github.com/mols3131d/hmda-data-reliability/pull/277) remains a prerequisite-blocked Draft with no integrated #269–#276 main revision. |

**Next transition:** On any base/head/test/Spec/CI change, compare exact revisions again. For C4, use a disposable target and fault injection during the *second* `copyfile` after writing partial bytes; assert `*.next` cleanup and current pair preservation, then distinguish source defect from test-oracle defect. Keep F1 timestamp-only E2E and F3 shared Git environment in #277, but route internal runner cleanup to its own source owner. This R2 reviewed head is the **pre-update** SHA; the subsequent Inbox-only commit must be re-compared.


## R4 · 2026-10-26 KST · Rollback Fault Composition

> [!NOTE]
> **Assessment: blocked for the independent specialist gate; no confirmed new in-scope `current_required`.** R2 is the latest section actually persisted in this file before R4; the prior session's R3 summary must not be treated as an additional persisted artifact. A distinct *conditional* rollback-cleanup risk is now tracked without claiming runtime reproduction.

- **Target** — PR #270, `agent/test/audit-data-operations-design`, this Inbox only.
- **Revision** — persisted R2 reviewed head `2a6aa3117e1725827029b26f105da49c76338e12` → authoritative pre-write head `c645a3ae0cc09013a4f6cb9fdc9bf577c75e6eb0`; compare shows this Inbox file alone changed. `main@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686` unchanged; reviewed source/test/Spec blobs unchanged. PR conversation has no comments.
- **Scope** — composed failure in current artifact-pair promotion, changed runner test oracle, normative stage contract, ownership and remote CI. No production or shared files modified.

### R4 Candidate Decisions

| ID | Severity | Scope relation / disposition | Evidence and counterevidence | Action |
| --- | --- | --- | --- | --- |
| C4 | 🟡 Minor | `independent_requirement` / **Keep follow_up** | [Runner](../../src/hmda_reliability/data_operations/runner.py), `_promote_dbt_artifacts`, appends to `staged_promotions` after `copyfile`. An interrupted copy may leave the current item's `.next`; this is not a demonstrated corrupted current pair. Existing R2 disposition remains applicable. | Source owner: isolated partial-copy fault injection; domain test owner: old pair bytes + no orphan `.next`. |
| C6 | 🟠 Major **if reached**; unverified double-fault | `contract_dependency` / **Unknown, not admitted as current_required** | [Runner rollback block](../../src/hmda_reliability/data_operations/runner.py), around lines 405–429: when a second `staged_path.replace` fails, the `except OSError` handler performs `staged_path.unlink`, committed-destination unlink and backup restoration **without guarding rollback I/O failures**. If cleanup `unlink` itself raises, control exits before restoring backed-up current manifest, potentially leaving the already-committed new manifest paired with the old run-results. [Changed test](../../tests/data_operations/test_dbt_runner.py), `test_artifact_promotion_restores_pair_when_second_replace_fails` (around lines 850–883), injects the first failure only; the normal rollback succeeds. This is a source-level two-fault reachability inference, **not** a reproduced failure or evidence that ordinary promotion corrupts data. The [stage Spec](../../openspec/specs/data-operations-stage-execution/spec.md) protects last-known-good projection, but exact rollback-failure semantics need a source-owner decision. | Use a disposable current pair and inject (1) second replace OSError, (2) rollback `.next` unlink OSError; observe exact old/new pair bytes and primary error cause. If reproduced, source owner should define cleanup/restore ordering and failure evidence; test owner may add a focused regression after contract clarification. Do not silently reassign source remediation to #277. |

**Research → Plan → Review:** Challenged the R2 single-fault rollback proof with a distinct two-fault cleanup path and traced the handler's operation order. Separate source correctness, test coverage, and cross-domain promotion/reader identity. A single-fault GREEN test does not refute C6; an unexecuted double-fault hypothesis does not prove a production incident.

### R4 Validation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | Revision and lane comparison | `2a6aa311..c645a3ae` changes this Inbox file only; modified tests remain `tests/data_operations/test_dbt_runner.py` and `test_incident_lifecycle.py`, disjoint from #269/#271/#272. |
| ✅ Pass | Remote prospective-merge CI log inspection | [CI Lite 40228362969](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40228362969), job `121274577764`, merge `a17c0cfec664c3f902c33ad495a24f424eba9391` of head `c645a3ae` into base `ea39a4fd`: **57 passed in 41.80s**; selected Python checks succeeded. |
| ⚪ Not Verified | Local pytest, partial-copy/double-fault injection and actual pair observation | No execution in this continuation; C4/C6 remain conditional source analysis. |
| ⚪ Not Verified | Independent DualVantage and #277 integrated E2E | No isolated reviewer context; #277 remains Draft, initial base `81fe44b2` one commit behind current main and prerequisite PRs unmerged. |

**Next:** Challenge C6 first with a two-fault disposable file pair; if rollback can be interrupted, separate source-level remediation from #270's test-only oracle scope and retain a clear error/state reconciliation record. Keep R1 C1/C2 and R2 C3/C5 Drop. #277 owns only genuine integration (timestamp/identity E2E, dbt log isolation and shared Git environment), not the runner's internal cleanup by default. Revalidate the post-write head and current CI before using this note.

## R5 · 2026-10-26 KST · Corrected Two-Fault State Reconstruction

> [!IMPORTANT]
> **Handoff / independent review pending.** R4 C6의 rollback 중단 가능성은 유지하되 **잔여 current pair 상태에 관한 잘못된 표현을 정정**합니다. 정적 경로 증명과 실행 재현을 구분합니다.

- **Revision:** R4 pre-write `c645a3ae0cc09013a4f6cb9fdc9bf577c75e6eb0` → authoritative pre-write `29c19c540240f2415c14ff234e6dce552481cb21`: 이 Inbox만 바뀐 단일 commit. `main/base@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`; test/source/Spec 불변.
- **Research → Plan → Review:** [runner](../../src/hmda_reliability/data_operations/runner.py) `_promote_dbt_artifacts`의 두 promotion 순서를 파일별로 추적해 [변경 테스트](../../tests/data_operations/test_dbt_runner.py) `test_artifact_promotion_restores_pair_when_second_replace_fails`의 정상 rollback과 비교. R4가 서술한 **new manifest + old run-results**를 반증했습니다.

| ID | Severity | Decision / Evidence | Next |
| --- | --- | --- | --- |
| C6 correction | 🟠 Major **if reached** | **Keep conditional source risk / Unknown runtime, not current_required.** Manifest는 old→`.previous` 뒤 new로 교체됩니다. 이어서 run-results도 old→`.previous`로 이동한 **다음** `run_results.json.next.replace`가 실패합니다. 이때 rollback의 `run_results.json.next.unlink`까지 실패하면 이후 committed manifest 제거·양쪽 backup 복원이 실행되지 않습니다. 정확한 잔여 상태는 **new current manifest + missing current run-results + old .previous pair**, **new + old current pair가 아닙니다**. 단일 replace failure만 주입한 테스트는 정상 rollback을 검증하므로 이 복합 실패를 포착하지 못합니다. | Data Operations source owner: disposable pair에서 second replace OSError와 rollback `.next` unlink OSError를 조합해 파일별 exact bytes/existence와 primary error를 확인. 결과에 따라 복구 순서/오류 evidence 결정. |
| C4 | 🟡 Minor | **Keep prior follow_up:** `copyfile`가 현재 `.next`를 부분 생성한 후 실패하면 그 item은 `staged_promotions`에 추가되기 전이라 cleanup 대상에서 누락될 수 있음. Current pair 손상으로 확대 해석하지 않음. | Partial-copy fault와 orphan `.next` 부재를 별도 확인. |

### R5 Validation and Continuation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | SHA 및 파일 소유권 정적 비교 | R4→현재 단일 Inbox commit; 수정 테스트는 `tests/data_operations/**` 두 파일로 #269/#271/#272와 비중복. |
| ✅ Pass | 최신 **원격** prospective-merge CI log | [CI Lite 40232583736](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40232583736), job `121287269242`: **57 passed in 36.78s**, selected Python checks 성공. 단일 fault oracle이지 double fault 증거 아님. |
| ⚪ Not Verified | 로컬 double-fault/partial-copy 실험, 독립 specialist | 이번 회차 미실행. R4의 파일 상태 표현은 이 절로 대체. |
| ⚪ Not Verified | #277 실제 integration 및 승인 | 선행 PR 미병합. #277은 timestamp/identity E2E·dbt log 격리·공용 Git 환경 owner; 내부 runner cleanup은 이관하지 않음. |

**Next:** C6의 정확한 상태 전이를 일시적 파일 pair에서 재현한 후 source-owner 수정 필요성을 판정. 사람이 승인/병합/Ready 상태를 결정하며 이 R5 reviewed head는 Inbox 갱신 전 SHA입니다.

## R6 · 2026-10-26 KST · Double-Fault Error-Contract Counterexample

> [!IMPORTANT]
> **Research → Plan → Review / handoff.** R5 C6의 정확한 파일 잔여 상태에 더해 **domain error normalization 자체가 누락되는 조건**을 검증했습니다. 이는 이전 C6와 같은 root cause이므로 별도 신규 finding으로 중복 등록하지 않습니다.

- **Revision:** R5 reviewed pre-write `29c19c540240f2415c14ff234e6dce552481cb21` → authoritative pre-write `bd9761752379036e1db67d4fead4d376f7e7a2e2`: 단일 Inbox-only commit. `main/base@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686` 및 code/test/Spec 불변; 새 PR feedback 없음.
- **Contract and location:** [Stage Spec](../../openspec/specs/data-operations-stage-execution/spec.md) `dbt failure boundary`는 caller가 처리 가능한 domain failure를 요구. [runner](../../src/hmda_reliability/data_operations/runner.py) `_promote_dbt_artifacts`의 `except OSError` 안에서 `.next.unlink`가 **`raise DataOperationError(...) from exc`보다 먼저** 실행. [Changed test](../../tests/data_operations/test_dbt_runner.py) `test_artifact_promotion_restores_pair_when_second_replace_fails`는 단일 replace fault만 주입.
- **C6 · 🟠 Major if reached · Keep conditional pre-existing source risk / runtime unverified:** 임시 경로에서 source와 같은 promotion/rollback 순서를 복제하여 (1) `run_results.json.next.replace` OSError, (2) rollback `run_results.json.next.unlink` OSError를 주입했습니다. **관찰:** 최종 예외는 primary `DataOperationError`가 아니라 **secondary raw `OSError`**; current는 **new manifest + missing run-results**, backup은 **old pair**, 실패한 `.next`는 남음. R5의 잔여 상태와 일치하며 primary failure context도 가려집니다. 단, **원본 runner 모듈을 import/실행한 테스트가 아닌 독립 제어 흐름 복제**로, 실제 환경 reachability·복구 성공을 검증하지 않았습니다.
- **C4 · 🟡 Minor · Keep follow_up:** `shutil.copyfile` 중 partial `.next` 생성 후 실패 시 아직 `staged_promotions`에 추가되지 않아 orphan이 남을 수 있음. 이번 실험은 copy fault가 아니므로 C4 실행 검증으로 승격하지 않음.
- **Ownership:** #270 test owner는 정확한 double-fault/partial-copy oracle만 제안받고, runner source 수정은 Data Operations source owner가 결정. #277은 current identity를 소비하는 통합 경계만 소유.

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | R5→R6 head/Spec/source/test static comparison | `29c19c54..bd976175` Inbox-only, 다른 세 PR test lane과 비중복. |
| ✅ Pass | Disposable Python promotion/rollback control-flow simulation | raw secondary OSError, current/backup/staged 파일별 bytes·존재 관측; **실제 repository package 실행 아님**. |
| ✅ Pass | Remote current-head prospective-merge CI | [CI Lite 40238111595](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40238111595): merge `e06f30ca`, **57 passed in 41.82s**, 선택 Python checks 성공. 복합 fault 미포함. |
| ⚪ Not Verified | 원본 runner double-fault/partial-copy fault injection, 로컬 pytest, 독립 specialist | 수행하지 않음. |

**Next:** Data Operations owner가 원본 `_promote_dbt_artifacts`를 임시 pair에서 두 fault와 partial copy로 각각 실행해 exact bytes, 남은 `.next/.previous`, primary/secondary error cause를 확인; source의 rollback failure policy를 먼저 결정. 인간 승인·merge는 건드리지 않음. Reviewed head는 갱신 전 SHA입니다.

## R7 · 2026-10-26 KST · Extracted Promotion Fault Matrix

> [!IMPORTANT]
> **Research → Plan → Review / handoff.** R6의 독립 제어 흐름 모사 대신 `main`의 `_promote_dbt_artifacts` **함수 본문과 `_ArtifactPromotion` 경로 계산**을 별도 Python 파일에 옮겨, 실제 임시 파일에서 실패 지점별로 실행했습니다. `DataOperationError` 타입은 동일 생성자 계약의 최소 stub입니다. **원본 repository 모듈 import/pytest가 아니므로** integration 재현으로 표현하지 않습니다.

- **Revision:** R6 pre-write `bd9761752379036e1db67d4fead4d376f7e7a2e2` → R7 authoritative pre-write `b247582fdec29d0bf4c139cf445d2db970b6792e`: 이 Inbox만 변경한 1 commit. `main/base@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`; source/test/Spec 불변, PR comments 0.
- **Contract/locations:** [Data Operations stage Spec](../../openspec/specs/data-operations-stage-execution/spec.md) `dbt failure boundary`; [runner](../../src/hmda_reliability/data_operations/runner.py) `_ArtifactPromotion` (L36–57), `_promote_dbt_artifacts` (L386–437); [changed test](../../tests/data_operations/test_dbt_runner.py) `test_artifact_promotion_restores_pair_when_second_replace_fails` (L850–884).

| ID | Severity | Decision / scope relation | New evidence and limitation | Next |
| --- | --- | --- | --- | --- |
| C4 | 🟡 Minor | **Keep follow_up / pre-existing source** | 두 번째 `shutil.copyfile`이 `run_results.json.next`에 `PARTIAL`을 쓴 뒤 `OSError` 발생하도록 주입: `DataOperationError` 반환, **old current pair 유지**, 첫 `.next` 삭제, **두 번째 partial `.next` 잔존**. `staged_promotions.append`가 copy 성공 *뒤*이기 때문. R6의 미실행 C4를 격리 추출 함수 수준에서 확인. | 원본 모듈 기반 copy interruption 검증 및 orphan cleanup 정책; current pair corruption으로 과장하지 않음. |
| C6 | 🟠 Major (conditional) | **Keep follow_up / pre-existing source** | 두 번째 `.next.replace`의 primary `OSError` + rollback의 동일 `.next.unlink` secondary `OSError`를 함께 주입: 최종 예외 **raw secondary `OSError`**, current는 **new manifest + missing results**, `*.previous`에 old pair, `run_results.json.next` 잔존. R6 시뮬레이션의 상태를 함수 본문 실행으로 강화. | 원본 모듈 fault test에서 exact bytes·error cause·recovery policy 결정. 이중 fault를 단일 replace-failure 테스트의 통과로 대체하지 않음. |

### R7 Validation and Continuation

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | R6→R7 head, 정본 Spec/source/test 및 파일 소유권 대조 | `bd976175..b247582f` Inbox-only; #269/#271/#272 테스트와 경로 비중복. |
| ✅ Pass | 로컬 **격리 추출 함수 본문**의 실제 파일 fault matrix | partial-copy와 double-fault 두 독립 시나리오에서 current/staged/backup 파일의 bytes·존재, 예외 타입을 assertion으로 확인. **실제 package/pytest 실행 아님**. |
| ✅ Pass | R7 pre-write head의 원격 prospective-merge CI | [CI Lite 40242536478](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40242536478), merge `9895f51` into `ea39a4fd`, **57 passed in 34.24s**; 복합 fault 미포함. |
| ⚪ Not Verified | 원본 runner import 기반 fault, local domain pytest, 독립 specialist, #277 통합 | 미실행; extraction stub 및 단일 CI 성공은 최종 contract 검증 아님. |

**Next:** Data Operations owner가 원본 `_promote_dbt_artifacts`에 (a) partial copy, (b) replace+rollback unlink double fault를 각각 주입해 `.next/.previous` 상태·primary/secondary cause를 검증. rollback cleanup failure를 추가 failure로 덮지 않을 정책은 source owner가 결정. #277은 cross-domain current projection 소비 계약만 담당. 이 절의 head는 **Inbox 갱신 전** SHA입니다.

## R8 · 2026-10-26 KST · Candidate Identity Race and Owner Boundary

> [!NOTE]
> **Research → Plan → Review / handoff.** R7의 copy failure·double-fault를 다시 모사하지 않고, candidate identity 확인과 current pair copy 사이의 동시 변경 가설을 실제 호출 순서와 ownership에 대조했습니다. 동시 writer를 실제 실행한 증거는 없습니다.

- **Revision:** R7 reviewed pre-write `b247582fdec29d0bf4c139cf445d2db970b6792e` → authoritative R8 pre-write `f3734eb6f4209d8fc4ad61e77afe6af006079d8a`; 비교는 이 Inbox만 수정한 1 commit. `main/base@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`, test/source/Spec 불변, PR comments 0.
- **Contract/locations:** [runner](../../src/hmda_reliability/data_operations/runner.py) `run_dbt_build`, `_run_dbt_command`, `promote_dbt_artifacts`, `_ensure_artifact_projection`, `_promote_dbt_artifacts`; [changed test](../../tests/data_operations/test_dbt_runner.py) artifact-only drift / rollback cases; [stage Spec](../../openspec/specs/data-operations-stage-execution/spec.md).

| ID | Severity | Decision / scope relation | Evidence and counterevidence | Next |
| --- | --- | --- | --- | --- |
| C7 | 🔵 Note (conditional integrity risk) | **Keep pre-existing contract limitation / follow_up, not current_required** | `_ensure_artifact_projection`가 candidate 두 파일의 ID를 한 번 확인한 뒤 `_promote_dbt_artifacts`에서 두 파일을 **순차 copy**하고 staged pair ID를 재계산하지 않습니다. Current projection lock은 current directory를 보호하지만 candidate writer를 봉쇄한다는 증거는 없습니다. 검증 후 두 번째 candidate 파일을 바꾸면 채택 pair가 `result.projection_id`와 달라질 수 있다는 interleaving이 성립합니다. 반증 측면에서 `run_dbt_build`는 고유 target의 **동기 subprocess 종료 후** 결과를 반환하므로 정상 호출만으로 concurrent candidate writer가 있다는 주장은 성립하지 않습니다. 외부 mutation·복사 중 변형의 실제 reachability는 미확인입니다. | Source owner가 실제 concurrent writer/TOCTOU threat model을 결정할 때만, disposable candidate의 두 번째 copy 직전 mutation을 주입하고 promoted `artifact_projection_id`와 build result를 비교. 이 PR의 기존 test-only 범위를 임의로 넓히지 않음. |
| C4 / C6 | 🟡 Minor / 🟠 Major (conditional) | **Keep R7 source-owner follow_up** | Partial `.next` 잔존 및 이중 rollback failure의 current pair 손상·raw secondary `OSError`는 R7의 추출 함수 probe 결과이며 이번 race 검토로 해결되지 않음. | 원본 runner module import 기반 두 fault probe; source owner가 rollback policy 결정. |

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | R7→R8 revision, 호출 순서 및 scope 정적 대조 | 이 Inbox만 변경. Candidate 검증→순차 copy→current commit의 ordering과 동기 dbt 종료 safeguard를 함께 확인. |
| ✅ Pass | 최신 **원격** prospective-merge CI | [CI Lite 40247096812](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40247096812): merge `ff5637609f80ce6859993d21c4926456d6bb5f75`, `tests/data_operations` **57 passed in 34.19s**. TOCTOU/복합 fault는 미포함. |
| ⚪ Not Verified | 원본 module fault, concurrent mutation, 로컬 pytest, 독립 specialist | 이번 회차 미실행. |
| ⚪ Not Verified | #277 candidate→current→Reliability 통합 | #269–#276 미병합; #277 Draft의 기존 base는 최신 main과 다름. |

**Next:** C7을 production race로 단정하지 말고 candidate mutability contract를 owner에게 확인. 먼저 R7 C4/C6의 원본 함수 fault 재현을 분리 실행; #277은 실제 candidate/current 소비 identity만 선행 병합 후 검증. 갱신 후 head/CI는 별도 확인하며 승인·Ready·merge는 변경하지 않습니다.

## R9 · 2026-10-26 KST · Quality Gate Revalidation Versus Real Lock

> [!NOTE]
> **Research → Plan → Review / handoff.** R8 candidate TOCTOU와 R7 artifact rollback을 반복하지 않고, 오염된 Bronze에 대한 gate 재검사와 dbt process 시작 차단 테스트가 실제로 무엇을 검출하는지 반증했습니다. 새 production defect는 확정하지 않았습니다.

- **Revision:** R8 pre-write f3734eb6f4209d8fc4ad61e77afe6af006079d8a → authoritative pre-write 00f24f3d2c83751963658494fae3f9540091fed9: 이 Inbox만 변경한 1 commit. main/base ea39a4fd6c8f483509cf00a1d1114feb4ef3b686, test/source/Spec 불변, PR feedback 0.
- **Research:** [변경 runner tests](../../tests/data_operations/test_dbt_runner.py) L322–405의 두 case는 gate 실패 시 subprocess 미시작과 성공 시 gate→dbt 호출 순서 및 동일 lock context를 확인합니다. [runner](../../src/hmda_reliability/data_operations/runner.py) L118–125, L162–181은 database_mutation_lock 안에서 evaluate_quality_gate 다음 _run_dbt_command를 실행합니다. [정본 stage Spec](../../openspec/specs/data-operations-stage-execution/spec.md) L73–92는 dbt process 동안 공통 DB lock 유지와 lock 실패 시 process 미시작을 요구합니다.
- **Plan:** gate ordering 검출력과 **실제 quality gate 판정·OS lock cross-writer interleaving** 검출력을 분리합니다. 후자는 [#277 계획](https://github.com/mols3131d/hmda-data-reliability/blob/agent/test/audit-cross-domain-design/inbox/github-277-audit-cross-domain-design/00-plan-cross-domain-tests.md)의 reserved tests/data_operations/test_quality_gate.py 및 integration lane에서 검증할 대상이지 #270에 공용 fixture를 추가할 이유가 아닙니다.

| ID | Severity | Disposition / ownership | Evidence / counterevidence | Next |
| --- | --- | --- | --- | --- |
| C8 | 🔵 Note | **Drop / subprocess-before-gate hypothesis** | 실패 case는 lock context 내부에서 gate가 QualityGateError를 던지면 subprocess 호출을 AssertionError로 차단하고, 성공 case는 calls == ["gate", "dbt"]를 고정합니다. gate/process 순서가 바뀌는 mutant는 실패합니다. | 같은 ordering test 중복 추가 없음. |
| C9 | 🔵 Note | **Keep cross-domain integration limitation / #277**, not current_required | 두 case는 **database_mutation_lock과 evaluate_quality_gate를 monkeypatch**하므로 실제 dirty Bronze 판정 또는 OS-level full-load/recovery writer와의 lock lifetime은 입증하지 않습니다. 테스트 이름과 source가 해당 기능을 보장한다고 해서 fake를 real integration으로 승격할 수 없습니다. | #277에서 실제 dirty Bronze → gate 거부 → dbt process 미시작/current artifact pair 불변, 별도 writer가 lock을 보유한 동안 dbt 시작 차단을 관측. |
| C4 / C6 / C7 | 🟡 Minor / 🟠 Major conditional / 🔵 Note | **Keep existing source-owner follow_up** | Partial .next 잔존, replace+rollback unlink 이중 장애의 raw OSError/current pair 불일치, candidate TOCTOU는 R7/R8의 별도 조건부 위험입니다. 이 gate ordering 검토로 반박되지 않습니다. | 원본 runner fault와 candidate writer threat model은 Data Operations owner 판단. |

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | R8→head compare, Spec→runner→positive/negative gate tests 정적 검토 | Inbox-only, gate와 process의 lock scope 및 mock boundary 확인. |
| ✅ Pass | **원격** prospective-merge CI | [CI Lite 40251450541](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40251450541): merge 1ddde34159ad8d8ee6d6e614ffcec118559c58c2, tests/data_operations **57 passed in 26.38s**; 실제 cross-domain writer fault 미포함. |
| ⚪ Not Verified | 실제 dbt/gate subprocess·cross-writer lock, 원본 runner 이중 fault, 로컬 pytest, 독립 specialist | 이번 회차 미실행. |
| ⚪ Not Verified | #277 integration | #269–#276 모두 미병합 Draft; #277 최초 base 81fe44b2, Draft. |

**Next:** C8 Drop, C9는 #277 integration boundary로 유지. #270 source owner가 R7 C4/C6의 원본 module fault를 검증하고 cleanup/error 정책을 결정합니다. 이 절은 갱신 전 SHA; 이후 head/CI 재확인 필요. 승인·Ready·merge 변경 없음.

## R10 · 2026-10-26 KST · Stale Current Artifacts Versus Isolated Run Target

> [!NOTE]
> **Research → Plan → Review / continuation.** R9의 quality-gate fake lock, R7의 double-fault promotion과 분리하여, 이전 current artifact만 있는 상태에서 새 dbt build를 성공으로 오인하는 경로를 반증했습니다. 새 `current_required`는 확인되지 않았습니다.

- **Revision:** R9 reviewed pre-write `00f24f3d2c83751963658494fae3f9540091fed9` → authoritative R10 pre-write `d030b144d5312f6307997d2a02d8c9d4bc985ced`: GitHub compare에서 **2 commits, 이 Inbox 1파일만 변경**. `main/base@ea39a4fd6c8f483509cf00a1d1114feb4ef3b686`; test/source/Spec 불변, PR discussion 0.
- **Research / contract:** [stage Spec](../../openspec/specs/data-operations-stage-execution/spec.md) `Stale artifacts are not current success`와 `dbt failure boundary`는 과거 artifact를 현재 성공으로 승격하지 않도록 요구합니다. [변경 테스트](../../tests/data_operations/test_dbt_runner.py) `test_run_dbt_build_rejects_preexisting_artifacts` (L180–202)는 old manifest/results에 `stale` bytes를 쓴 뒤 fake subprocess `returncode=0`이 **새 run artifact를 생성하지 않게** 하고, `DataOperationError` 및 old current bytes 불변을 검사합니다. [runner](../../src/hmda_reliability/data_operations/runner.py) `_create_run_target`는 `mkdtemp(run-*)`로 별도 경로를 만들고, `_validate_dbt_artifacts`는 **그 run 경로의 두 파일** 존재를 검사합니다.
- **Plan / challenge:** `returncode=0` 또는 old current pair의 존재만으로 `DbtBuildResult(succeeded=True)`를 반환하는 mutant라면 위 negative test의 `pytest.raises`에서 실패해야 합니다. 반면 해당 테스트는 dbt JSON **semantic schema**를 검증하지 않습니다. 정본 stage Spec의 현행 성공 계약은 현재 실행 artifact 존재 확인이며 JSON 전체 유효성 검사를 요구한다고 확대하지 않습니다.

| ID | Severity | Disposition / scope relation | Evidence / counterevidence | Next |
| --- | --- | --- | --- | --- |
| C10 | 🔵 Note | **Drop / stale current pair를 build 성공으로 재사용하는 가설** | 테스트는 subprocess 성공에도 fresh run pair가 없으면 실패를 요구하며 current bytes를 보존합니다. Source의 unique target과 양쪽 artifact 존재 검사가 이를 지지합니다. | 같은 stale artifact case 중복 없음. |
| C4 / C6 / C7 | 🟡 Minor / 🟠 Major conditional / 🔵 Note | **Keep prior source-owner follow_up** | Partial `.next` 잔존, replace+rollback unlink 이중 장애, candidate copy TOCTOU는 이 별도 run-target negative test로 해결되지 않습니다. | 원본 runner fault 및 candidate mutability threat model을 Data Operations source owner가 판정. |
| C9 | 🔵 Note | **Keep #277 integration limitation** | 이전 R9의 gate ordering test는 fake gate/lock을 사용합니다. | 선행 병합 후 dirty Bronze→실제 gate 거부→dbt 미시작 및 current pair 불변을 검증. |

| Result | Check | Evidence |
| --- | --- | --- |
| ✅ Pass | R9→R10 revision 및 Spec→runner→negative test 정적 대조 | Inbox-only 2 commits; 현재 run target과 old current pair 경로 분리 확인. |
| ✅ Pass | **원격** R10 pre-write prospective-merge CI | [CI Lite 40256317927](https://github.com/mols3131d/hmda-data-reliability/actions/runs/40256317927), job `121358889288`: `TARGETS=tests/data_operations` **57 passed in 43.08s**, 선택 Python checks 성공. 복합 fault는 미포함. |
| ⚪ Not Verified | 이번 회차 로컬 dbt/pytest, stale-success mutant 실행, 원본 promotion double-fault, 독립 specialist | 미실행. |
| ⚪ Not Verified | #277 current projection→Reliability consumer 통합 | 선행 PR 미병합, #277 Draft. |

**Next:** C10 Drop. C4/C6는 실제 module fault probe, C7은 candidate writer 계약 결정이 선행되어야 합니다. #277에는 실제 gate/lock 및 promotion-consumer identity 접점만 인계. 이 절의 SHA는 **Inbox 갱신 전** head이며 Ready·approval·merge는 변경하지 않습니다.
