---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: Reliability Freshness Delay Semantics Tasks
description: Bronze ingestion freshness measurement, age detection와 compound recovery/replay를 TDD로 구현한다.
tasks_completed: 41
tasks_total: 41
---

> [!NOTE]
> Measurement contract와 age detection을 먼저 전환한 뒤, temporal ingestion gate와 freshness-bound recovery를 연결한다. 마지막으로 disposable evaluator가 clean, delay, recovery와 replay evidence를 end-to-end로 입증하며 existing content recovery regression을 보존한다.

## Prerequisites

- [x] Apply 시작 revision의 current Specs, profile/detection, ingestion/recovery와 volume/null evaluation baseline을 재검증한다.
  - **Done when:** `openspec validate --all --json`과 현재 관련 focused tests가 통과하거나 변경과 무관한 baseline failure가 분류된다.

## Tasks

### 1. Explicit freshness measurement

- [x] 1.1 **RED** — Nullable timestamp와 `measured|unavailable` invariant, JSON serialization과 future timestamp failure를 contract/profile tests로 고정한다.
  - **Covers:** `ProfileSnapshot contract`, `Freshness metric`
  - **Done when:** fallback timestamp, inconsistent status/timestamp 또는 future timestamp를 현재 구현이 허용하는 assertion에서 의도한 RED가 발생한다.

- [x] 1.2 **GREEN** — `FreshnessMeasurementStatus`, nullable `freshness_at` validator와 profile builder의 measured/unavailable/future handling을 구현한다.
  - **Done when:** measured max timestamp와 unavailable `None`이 반환되고 future measurement는 `ProfileSnapshotError`로 종료된다.

- [x] 1.3 Snapshot fixture, serialization expectation과 public contract export를 새 shape로 전환하고 `freshness_used_fallback` 사용을 제거한다.
  - **Done when:** repository에서 fallback metric 참조가 사라지고 profile contract/builder focused tests가 통과한다.

### 2. Age-based detection and lifecycle

- [x] 2.1 **RED** — Exact max-age boundary, threshold 미만, unchanged timestamp staleness, unavailable skip과 evidence payload tests를 작성한다.
  - **Covers:** `Freshness delay detection`
  - **Done when:** baseline-relative detector 또는 legacy evidence field 때문에 의도한 assertion에서 실패한다.

- [x] 2.2 **GREEN** — `freshness_max_age_minutes`와 current age rule을 구현하고 legacy threshold field와 baseline freshness payload를 제거한다.
  - **Done when:** incident boundary는 `age >= max_age`이고 unavailable current에서도 다른 rule 결과가 보존된다.

- [x] 2.3 **RED/GREEN** — `run_incident_lifecycle(..., thresholds=...)` keyword input과 default fallback을 test-first로 추가한다.
  - **Covers:** `Configured detection thresholds`
  - **Done when:** explicit max age가 lifecycle evidence/판정에 반영되고 omitted input은 default behavior를 유지한다.

- [x] 2.4 **RED/GREEN** — Freshness detector/remediation action을 Bronze ingestion wording과 `check_bronze_ingestion_freshness` identifier로 전환한다.
  - **Covers:** `Incident-specific actions`
  - **Done when:** freshness draft가 upstream publication을 주장하지 않고 existing incident action tests가 통과한다.

### 3. Atomic temporal ingestion gate

- [x] 3.1 **RED** — Same content/different `max(ingested_at)` target이 transaction gate에서 zero mutation으로 실패하는 component test를 작성한다.
  - **Covers:** `Serialized freshness-state replacement`, `Temporal-only target drift`
  - **Done when:** content identity만 확인하는 현재 loader가 stale temporal target을 교체하여 의도한 assertion에서 실패한다.

- [x] 3.2 **GREEN** — Optional `expected_max_ingested_at` 조회와 content + temporal comparison을 partition replacement transaction에 추가한다.
  - **Done when:** matching compound state만 교체되고 temporal/content mismatch는 `HMDAStalePartitionError`와 unchanged target을 반환한다.

- [x] 3.3 **RED** — Provenance-preserving candidate의 approved timestamp 보존과 missing/incompatible metadata pre-mutation failure tests를 작성한다.
  - **Covers:** `Metadata-preserving partition candidate`
  - **Done when:** 재계산된 timestamp 또는 incomplete candidate가 observable state assertion에서 실패한다.

- [x] 3.4 **GREEN** — Metadata-preserving input validation을 강화하고 candidate `source_*`/`ingested_at`을 그대로 적용한다.
  - **Done when:** approved timestamp가 target `max(ingested_at)`과 같고 invalid candidate는 target을 변경하지 않는다.

### 4. Freshness-bound approval and recovery

- [x] 4.1 **RED** — `incident_type`, `FreshnessObservation`, `FreshnessRecoveryBinding`의 required/forbidden/stale-before invariants를 contract tests로 고정한다.
  - **Covers:** `Incident-typed recovery proposal`
  - **Done when:** missing freshness binding, non-freshness binding 또는 non-stale before observation이 의도한 contract assertion에서 실패한다.

- [x] 4.2 **GREEN** — Freshness contract models와 `RecoveryProposal` validator를 구현하고 volume/null proposal call sites에 exact incident type을 추가한다.
  - **Done when:** freshness proposal만 binding을 요구하고 existing content proposal serialization/equality가 유지된다.

- [x] 4.3 **RED** — Same-content candidate의 timestamp mismatch/unavailable measurement가 approval 또는 mutation 전에 차단되는 tests를 작성한다.
  - **Covers:** `Approved freshness candidate`
  - **Done when:** content-only candidate gate가 invalid temporal candidate를 허용하여 의도한 RED가 발생한다.

- [x] 4.4 **GREEN** — Freshness candidate를 metadata-preserving temporary artifact로 stage하고 content identity와 expected timestamp를 모두 재검증한다.
  - **Done when:** 승인 전 evaluator와 승인 후 executor가 같은 candidate state를 검증하고 mutation은 동일 staged artifact만 사용한다.

- [x] 4.5 **RED** — Equal-content stale before-state mutation, acceptable replay skip, expired replay와 temporal drift zero-mutation tests를 작성한다.
  - **Covers:** `Freshness-bound target reconciliation`
  - **Done when:** stale target의 `already_recovered` 오판 또는 expired replay overwrite에서 의도한 RED가 발생한다.

- [x] 4.6 **GREEN** — Compound reconciliation matrix, transaction expected timestamp 전달과 freshness result fields를 executor에 구현한다.
  - **Done when:** before/after content가 같아도 timestamp/age가 mutation, resume 또는 new approval action을 정확히 결정한다.

- [x] 4.7 **RED/GREEN** — Content/freshness validation 분리와 post-mutation profile failure evidence를 추가하고 content-only recovery regression을 보존한다.
  - **Covers:** `Freshness validation evidence`
  - **Done when:** `validation_passed` 의미는 유지되고 freshness observations/result가 failure에서도 보존되며 volume/null recovery tests가 통과한다.

### 5. Deterministic freshness evaluation

- [x] 5.1 Complex scenario와 oracle을 `test_freshness_delay_evaluation.design.md`에 연결한다.
  - **Done when:** Path isolation, controlled defect, approval/recovery, replay와 pre/post-mutation failure가 실제 test 이름과 독립 oracle에 매핑된다.

- [x] 5.2 **RED** — Side-effect-free path preflight와 clean/delayed content/schema equality, exact fixed timestamps와 single incident tests를 작성한다.
  - **Covers:** `Controlled Bronze ingestion freshness case`
  - **Done when:** legacy source helper 또는 non-deterministic clock으로는 contract를 만족하지 못해 의도한 RED가 발생한다.

- [x] 5.3 **GREEN** — Disposable clean/target/candidate DB, scoped `ingested_at` update와 exact single-incident gate를 가진 evaluator setup을 구현한다.
  - **Done when:** source/business/schema/content는 유지되고 target freshness만 configured delay를 나타낸다.

- [x] 5.4 **RED** — Exact candidate approval, acceptable recovery, incident resolution, dbt validation과 overwrite 없는 replay tests를 작성한다.
  - **Covers:** `Freshness recovery vertical-slice evaluation`
  - **Done when:** recovery/replay structured observations 또는 compound acceptance가 없는 지점에서 의도한 RED가 발생한다.

- [x] 5.5 **GREEN** — `FreshnessDelayVerticalSliceResult`와 end-to-end candidate export, approval, recovery, post-lifecycle, dbt와 replay composition을 구현한다.
  - **Done when:** clean/delayed/recovery/replay observations가 exact하고 overall success가 content, freshness와 incident resolution을 모두 요구한다.

- [x] 5.6 **RED/GREEN** — Unavailable candidate, temporal target drift, expired replay와 post-acceptance lifecycle/dbt failure evidence를 구현한다.
  - **Covers:** `Freshness evaluation failure evidence`
  - **Done when:** failure stage, mutation 여부, reconciliation action과 이미 확정한 네 freshness observation이 loss 없이 반환된다.

- [x] 5.7 Reliability evaluation package와 top-level package에서 freshness evaluator/result를 export하고 report aggregation compatibility를 검증한다.
  - **Done when:** Public import smoke와 existing generic evaluation report tests가 통과한다.

### 6. Migration, documentation and validation

- [x] 6.1 Legacy `freshness_delay()` source helper, exports, tests와 HMDA synthetic documentation을 제거한다.
  - **Covers:** `Freshness delay case` removal
  - **Done when:** Public source helper 참조가 없고 migration target은 freshness vertical-slice API로 연결된다.

- [x] 6.2 Reliability/HMDA domain documentation과 Foundation readiness를 implemented Bronze semantics, public API와 remaining upstream limitation에 맞춘다.
  - **Done when:** Canonical docs가 fallback/baseline regression을 현재 동작으로 설명하지 않고 out-of-scope를 보존한다.

- [x] 6.3 Measurement, detection, lifecycle, remediation와 ingestion focused tests를 실행한다.
  - **Done when:** 관련 contract/unit/component test modules가 project default marker policy로 통과한다.

- [x] 6.4 Recovery/evaluation focused tests와 volume-drop/null-spike regression tests를 실행한다.
  - **Done when:** Freshness integration, approval backfill, generic evaluation과 null-spike evaluation modules가 통과한다.

- [x] 6.5 Ruff, Markdown lint와 OpenSpec validation을 실행한다.
  - **Done when:** `uv run ruff format --check .`, `uv run ruff check src tests`, `uv run rumdl check .`와 `openspec validate --all --json`이 성공하거나, Change와 무관한 baseline failure가 분류되고 changed paths가 모두 통과한다.

- [x] 6.6 Default pytest suite를 실행하고 결과를 validation evidence로 기록한다.
  - **Done when:** `uv run pytest`가 통과하거나 현재 Change와 무관한 baseline failure가 명확히 분류된다.

### 7. Review feedback remediation

- [x] 7.1 **PLANNING** — Freshness Change를 완료된 volume-drop MVP 범위를 변경하지 않는 post-MVP capability로 명시한다.
  - **Done when:** Proposal, Design, Change README와 Vision이 current MVP scope/milestone/status를 그대로 보존한다.

- [x] 7.2 **RED** — Candidate validation callback이 `ingested_at`을 변경해도 approval callback이 호출되지 않는 regression test를 추가한다.
  - **Covers:** `Approved freshness candidate` — `Candidate changes during validation`
  - **Done when:** Validation 전 state로 proposal을 만드는 현재 evaluator에서 approval 호출로 실패한다.

- [x] 7.3 **GREEN** — Validation 뒤 candidate artifact를 생성하고 artifact content/timestamp를 재측정해 proposal과 execution input을 결합한다.
  - **Done when:** Artifact mismatch는 approval 전에 structured failure로 종료되고 exact artifact state만 proposal에 포함된다.

- [x] 7.4 **REVIEW** — Focused/full test, static checks, OpenSpec validation과 approval-boundary review를 실행한다.
  - **Done when:** Review finding을 재현한 test와 관련 regression이 통과하고 validation evidence와 남은 scope risk가 기록된다.

## Validation Evidence

- Apply prerequisite: 관련 baseline 93 tests 통과, initial `openspec validate --all --json` 통과.
- Focused regression: reliability, incident lifecycle, HMDA partition/synthetic 150 tests 통과.
- Review remediation RED: validation mutation 뒤 approval callback이 호출되는 expected failure를 재현했다.
- Review remediation GREEN: exact regression 1 test와 freshness evaluation/recovery 38 tests 통과.
- Default suite: `uv run pytest` 250 tests 통과.
- Type: `uv run ty check` 통과.
- Changed paths: Ruff check와 format 80 files 통과, rumdl 20 files 통과.
- Review changed paths: Ruff check/format 2 Python files와 rumdl 15 Markdown files 통과.
- OpenSpec: 17/17 Specs/Changes valid.
- Diff hygiene: `git diff --check` 통과.
- Unrelated global baseline:
  - `uv run ruff check src tests`: untouched 2 `E501` (`data_operations/dbt_result.py`, `test_dagster_definitions.py`).
  - `uv run ruff format --check .`: untouched 3 files (`pivot-clarify-code` reference, `data_operations/runner.py`, `test_dagster_definitions.py`).
  - `uv run rumdl check .`: untouched 70 issues in 9/162 files; changed Markdown scope는 통과.

## Self-Review

- [x] 모든 관련 Requirement와 Scenario가 구현 및 테스트에 반영되었는지 확인한다.
- [x] Design의 Decision과 Boundary를 지키면서 중복과 불필요한 generic abstraction을 제거한다.
- [x] Replay, post-mutation failure, candidate artifact I/O와 transaction lock-release 경로를 검토한다.
- [x] 필요한 public export, domain documentation과 readiness 상태를 갱신한다.
- [x] Upstream publication freshness, orchestration과 monitoring이 out-of-scope로 남는지 확인한다.
