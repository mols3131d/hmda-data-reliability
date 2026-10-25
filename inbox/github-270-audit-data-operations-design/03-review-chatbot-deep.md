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
