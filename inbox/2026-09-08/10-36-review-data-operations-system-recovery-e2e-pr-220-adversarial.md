---
type: review
title: "PR #220 Adversarial Review: Deterministic System Recovery E2E"
description: "Adversarial review of PR #220 for false-green safety evidence, E2E boundary accuracy, and scope integrity."
status: completed
tags:
  - data-operations
  - testing
  - reliability
  - adversarial-review
  - pr-220
---

# PR #220 Adversarial Review: Deterministic System Recovery E2E

> [!IMPORTANT]
> **Verdict: Revise.** 검토 대상은 PR #220의 `204183f482d709dcc88ed4156b691fdebd6fa493`이며 baseline은 `ab90cb3ae9d94420046cc103da86517c3f989eb1`이다. 현재 구현에서 실제 unauthorized mutation을 관찰한 것은 아니지만, 새 E2E의 zero-mutation/replay oracle이 provenance-only rewrite를 검출하지 못해 핵심 safety proof가 false green이 될 수 있다. 또한 PR이 주장하는 Data Plane system E2E 경계와 실제 실행 경계가 다르고, unrelated Rulesync/`uv.lock` 변경이 dependency graph까지 바꾼다. CI Lite 성공은 확인했지만 이 세 finding을 해소하지 않는다.

## Overview

| Target | Revision | Scope | Verdict |
| --- | --- | --- | --- |
| PR #220 | `ab90cb3` → `204183f` | 새 deterministic recovery E2E/test design, 직접 영향받는 recovery/data-plane contract, PR에 함께 포함된 변경 | Revise |

이번 검토는 기존 일반 review artifact를 대체하지 않고 adversarial residual risk를 별도로 본다. 특히 현재 코드가 통과하는지를 재확인하기보다, 잘못된 구현이 들어와도 test가 green으로 남을 수 있는 경로와 PR이 실제보다 넓은 proof를 주장하는 지점을 우선했다.

## Findings

### F1. Zero-mutation and replay oracles can miss provenance-only rewrites

- **Severity** - 🟠 High
- **Evidence Strength** - Demonstrated
- **Location** - `tests/data_operations/test_system_recovery_e2e.py#_assert_pre_approval_zero_mutation`, `test_deterministic_system_recovery_e2e`의 S2/S7, `tests/data_operations/test_system_recovery_e2e.design.md`의 S2/S4/S7
- **Evidence** - 새 test/design은 S2와 S4를 zero mutation, S7을 redundant partition rewrite가 없는 replay로 설명한다. 그러나 pre-approval helper는 `PartitionContentIdentity`와 `income` null rate만 비교하고 S7은 executor가 반환한 `mutation_state == "already_recovered"`, logical identity와 row count만 확인한다. `partition_content_identity()`는 재적재 시각 차이를 stale state로 취급하지 않기 위해 `ingested_at`을 의도적으로 digest에서 제외한다. 반면 CSV ingestion은 `current_timestamp`를 `ingested_at`으로 생성하고 recovery executor는 승인 candidate를 staging한 뒤 `preserve_source_metadata=True`로 target overwrite에 사용한다. 따라서 동일 logical content를 실제로 다시 써서 `ingested_at`만 바뀌는 regression은 현재 zero-mutation/replay assertion을 통과할 수 있다. 특히 S7의 `mutation_state`는 검증 대상 executor 자체가 반환하는 self-report라서 "실제로 write가 없었다"는 독립 oracle이 아니다.
- **Reachability** - `already_recovered` 분기에서 잘못된 overwrite가 추가되거나, approval/lifecycle 경계의 regression이 logical columns를 보존한 채 provenance만 갱신하는 경우다. 동일 content overwrite는 stable identity가 그대로이므로 현재 assertion으로는 검출되지 않는다.
- **Impact** - 이 PR의 핵심 가치인 "사전 승인 zero mutation"과 "replay 시 redundant mutation 없음"을 실제 persisted state가 아니라 logical-content projection으로만 증명하게 된다. 안전 경계가 깨져도 테스트가 green일 수 있어 E2E safety evidence로 사용하기 어렵다.
- **Required Change** - no-mutation 경계 직전과 직후의 persisted provenance state를 독립적으로 비교한다. 최소한 대상 partition의 `ingested_at` 값 집합 또는 `partition_max_ingested_at()`을 S2, S4, S7에서 snapshot하고 unchanged를 확인한다. S7에서는 `mutation_state` assertion을 보조 evidence로 유지하되 target provenance가 replay 전후 동일하다는 assertion을 primary no-write oracle로 추가한다.

### F2. The claimed Data Plane system E2E bypasses the Airflow Data Plane boundary

- **Severity** - 🟡 Medium
- **Evidence Strength** - Observed
- **Location** - PR Summary/References, `tests/data_operations/test_system_recovery_e2e.design.md#Contract`, `test_deterministic_system_recovery_e2e`의 S0/S1
- **Evidence** - PR은 Data Plane의 적재 → quality gate → dbt build와 Control Plane을 연결한 "결정론적 시스템 복구 E2E"라고 설명하고 `openspec/specs/orchestration-pipeline/spec.md`를 governing reference로 제시한다. Architecture와 MVP는 Data Plane/Orchestration proof를 Apache Airflow가 소유한다고 정의한다. 하지만 새 system test는 Airflow DAG/runtime boundary를 실행하지 않고 `load_hmda_loans_partition()`, `evaluate_quality_gate()`, `run_quality_gated_dbt_build()`, `promote_dbt_artifacts()`를 직접 호출한다. `load_raw_data()`와 Airflow runtime request 변환, task dependency, task failure/error adaptation도 이 E2E 경로에 포함되지 않는다.
- **Reachability** - Airflow DAG import/runtime config/task ordering 또는 `QualityGateError`의 task failure 전달이 깨져도 Data Operations public API가 정상이라면 이 test는 계속 green일 수 있다.
- **Impact** - 테스트 자체는 Data Operations ↔ Reliability의 실제 DuckDB/dbt integration evidence로 유효하지만, 현재 명칭과 PR 설명대로는 실제 Data Plane system boundary까지 검증한 것으로 과대 해석될 수 있다. MVP의 Orchestration proof와 이 테스트의 증명 범위가 혼동된다.
- **Required Change** - scope를 늘리지 않는 최소 수정은 PR summary와 design contract를 **Data Operations + Reliability deterministic integration E2E core**로 좁히고 Airflow execution boundary가 제외됨을 명시하는 것이다. 실제 system/Data Plane E2E가 acceptance requirement라면 별도 scenario에서 기존 Airflow data-plane execution surface로 S0/S1을 시작하되 recovery task를 DAG에 추가하지 않는다.

### F3. Unrelated Rulesync sync changes the dependency graph inside the test PR

- **Severity** - 🟡 Medium
- **Evidence Strength** - Observed
- **Location** - commit `0728c1d48cac85aa779c05ab164bc5ca4ea95575`, `rulesync.jsonc`, `rulesync.lock`, `.agents/route/skills.jsonl`, docs indexes, `uv.lock`
- **Evidence** - base에서 첫 test commit `9b50202`까지는 새 E2E `.py`와 `.design.md` 두 파일만 변경된다. 다음 `chore(rulesync)` commit이 test 목적과 무관한 agent skill/index/Rulesync 변경과 `uv.lock`을 추가했고, 전체 PR에서 `uv.lock`은 1,412 additions / 1,079 deletions로 2,491 lines가 바뀐다. 같은 PR에는 dependency declaration 변경이 없는데 lock resolution marker가 platform-specific 형태에서 Python-version-only 형태로 바뀌고 실제 resolved package도 예를 들어 `alembic 1.18.5 → 1.19.2`, `anyio 4.14.2 → 4.15.1`로 이동한다. CI Lite는 이 PR의 lock으로 dependency sync를 수행한 뒤 selected tests를 실행했다.
- **Reachability** - test-only 변경의 검증 결과가 base dependency graph가 아니라 unrelated lock regeneration으로 바뀐 dependency graph에서 생성된다. 새 dependency behavior가 failure를 숨기거나 반대로 unrelated regression을 만들 수 있다.
- **Impact** - PR review scope와 validation provenance가 불필요하게 넓어지고, system E2E 변경과 dependency/tooling 변경의 원인 분리가 어려워진다.
- **Required Change** - 공개 history를 rewrite하지 않고 normal follow-up commit으로 unrelated Rulesync/index/lock 변경을 이 PR의 baseline 상태로 되돌리고, 해당 sync는 별도 PR/change unit으로 분리한다. 그 뒤 focused E2E와 CI를 다시 실행해 test 변경의 evidence를 원래 dependency contract에 고정한다.

## Adversarial Checks

| Attack / Hypothesis | Evidence | Result |
| --- | --- | --- |
| Blocking quality gate 뒤 dbt subprocess가 시작될 수 있음 | 기존 `tests/data_operations/test_dbt_runner.py`가 gate failure에서 subprocess 시작 시 실패하도록 별도 guard를 보유하고, current runner도 gate를 subprocess보다 먼저 실행함 | Rejected as new finding |
| Pending/incomplete approval이 source access 전에 차단되지 않을 수 있음 | 기존 `tests/reliability/test_approval_backfill_validation.py`가 missing source를 사용해 pending approval과 missing action의 pre-source-access ordering을 직접 검증함 | Rejected as new finding |
| Read-only lifecycle가 raw logical content를 바꿀 수 있음 | current `run_incident_lifecycle()`는 target DB를 `read_only=True`로 열고, 새 S2도 logical identity preservation을 확인함 | No current defect observed; F1의 stronger zero-mutation oracle 필요성만 유지 |

## Validation

| Check | Evidence | Result |
| --- | --- | --- |
| PR target/baseline pinning | PR #220 base `ab90cb3`, reviewed head `204183f`, 3 commits / 8 changed files | Pass |
| Changed-file and commit decomposition | base → `9b50202`는 test 2 files only; `0728c1d`가 Rulesync/index/`uv.lock` 변경을 추가 | Pass |
| Governing contract review | `docs/VISION.md`, `docs/ARCHITECTURE.md`, `docs/mvp.md`, orchestration/recovery/evaluation Specs, `tests/AGENTS.md`, test-design/review guidance | Pass |
| Current CI evidence | CI Lite run `34176105865` at reviewed head completed successfully; changed Markdown/Python/routes and selected tests passed | Pass |
| PR-body local validation claims | `5 passed`, `55 passed`, ruff/ty/rumdl 결과는 PR body에 기록되어 있으나 이 reviewer가 같은 command를 직접 실행하지 않음 | Not Verified independently |
| F1 runtime mutation reproduction | code path와 oracle semantics로 false-green condition을 입증했지만 별도 fault-injection test를 실행하지 않음 | Not Verified by execution |

## Remaining Risks

- Human E2E, Agent E2E와 live LLM/provider invocation은 PR이 명시적으로 제외했으므로 이번 finding으로 승격하지 않았다.
- F1은 current executor가 실제로 redundant write를 수행한다는 주장과 다르다. 현재 code는 `already_recovered`에서 overwrite를 선택하지 않는다. Finding은 이 보장이 회귀했을 때 새 E2E가 독립적으로 검출하지 못한다는 test-evidence defect다.
- 기존 일반 review artifact의 approval-before-source-processing finding은 component suite가 이미 해당 ordering을 missing-source oracle으로 보호하고 있어 이번 adversarial review의 새 finding으로 반복하지 않았다.
- 이 artifact를 branch에 추가하면 PR head는 새 commit으로 이동하지만 review target은 위에 고정한 `204183f482d709dcc88ed4156b691fdebd6fa493`이다. 이후 implementation/test가 실질적으로 바뀌면 affected finding을 재검토해야 한다.

## Verdict

| Decision | Rationale | Route |
| --- | --- | --- |
| Revise | High-severity zero-mutation false-green gap 1건과 scope/evidence integrity 문제 2건이 남아 있어 현재 상태를 deterministic system recovery proof로 채택하기에는 근거가 부족함 | PR #220에서 F1을 우선 수정하고 F2 claim을 정합화하며 F3 unrelated sync를 분리한 뒤 재검토 |