---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: Reliability MVP Volume-Drop Vertical Slice Tasks
description: Partition identity부터 exact approval, isolated dbt, recovery reconciliation과 end-to-end acceptance까지 TDD로 구현한다.
tasks_completed: 49
tasks_total: 49
tags:
  - "domain:reliability"
  - "capability:reliability-recovery-backfill"
  - "capability:data-operations-stage-execution"
  - "capability:data-operations-incident-lifecycle"
  - "capability:hmda-data-ingestion"
  - "capability:reliability-evaluation-report"
  - "mvp"
  - "volume-drop"
---

> [!NOTE]
> Apply gate를 최신 baseline과 active Change sequencing 확인으로 시작한 뒤, partition identity와 artifact isolation 같은 하위 primitive부터 approval/recovery와 deterministic vertical slice까지 연결한다. 각 GREEN은 대응 RED와 focused validation을 통과해야 완료한다.

## Prerequisites

- [x] 0.1 최신 `main`에서 현재 reliability, HMDA ingestion과 dbt runner baseline을 재검증한다.
  - **Done when:** `tests/reliability`, `tests/hmda_data/ingestion`, `tests/data_operations/test_dbt_runner.py`, `tests/data_operations/test_incident_lifecycle.py`가 통과하고 실행 command와 결과가 확인된다.

- [x] 0.2 완료됐지만 active인 관련 Change의 source/spec delta와 현재 Change의 overlap을 확인한다.
  - **Done when:** 네 Change의 구현이 현재 `main`에 존재하고 이 Change의 complete Requirement와 Design이 해당 behavior를 보존하며 archive/sync 없이 Apply해도 source conflict가 없음을 확인한다.

## Tasks

### 1. Stable partition identity and serialized replacement

- [x] 1.1 **RED** — partition identity의 order/volatile metadata invariance와 value/duplicate sensitivity test를 추가한다.
  - **Covers:** `Stable partition content identity`, `Equivalent partition content`, `Duplicate or value drift`
  - **Done when:** public identity API 부재 또는 semantic mismatch로 component test가 의도대로 실패한다.

- [x] 1.2 **GREEN** — versioned `PartitionContentIdentity`와 scoped identity 계산 API를 HMDA ingestion에 구현하고 export한다.
  - **Done when:** row order와 volatile metadata는 무시하면서 logical value와 duplicate multiplicity를 보존하는 focused test가 통과한다.

- [x] 1.3 **RED/GREEN** — expected identity compare-and-replace를 existing partition transaction에 추가한다.
  - **Covers:** `Partition replacement`, `Serialized expected-state replacement`, `Stale expected state`, `Target-state freshness`
  - **Done when:** 일치 시 atomic replacement, 불일치 시 typed failure와 zero mutation을 component test가 검증한다.

### 2. Exact recovery proposal and lifecycle inputs

- [x] 2.1 **RED** — approved recovery proposal의 required identity/action과 mismatch를 contract/gate test로 고정한다.
  - **Covers:** `Approval gate`, `Incomplete approval`, `Mismatched approved proposal`
  - **Done when:** incomplete 또는 mismatched approval이 source access 전에 실패하는 test가 의도대로 RED다.

- [x] 2.2 **GREEN** — immutable recovery proposal contract를 추가하고 `Approval`과 `ApprovedBackfillRequest`가 exact proposal을 공유하도록 전환한다.
  - **Done when:** approval validation과 executor gate test가 통과하고 기존 pending approval boundary가 유지된다.

- [x] 2.3 **RED/GREEN** — lifecycle result에 target state와 dbt artifact projection identity를 recovery proposal input으로 추가한다.
  - **Covers:** `Lifecycle result`, `Volume-drop recovery inputs`, `Clean baseline result`
  - **Done when:** incident case는 identity를 포함하고 clean case는 recovery input이 비어 있는 focused test가 통과한다.

### 3. Isolated dbt run and artifact promotion

- [x] 3.1 **RED** — candidate/failed target run이 current artifact를 보존하고 failed-run evidence를 반환하는 test를 추가한다.
  - **Covers:** `dbt build execution`, `Candidate run isolation`, `dbt failure boundary`, `Candidate dbt failure`, `Recovery dbt failure`
  - **Done when:** current runner의 pre-run deletion 또는 evidence 부재로 component test가 의도대로 실패한다.

- [x] 3.2 **GREEN** — run-scoped dbt target path와 structured run failure evidence를 구현한다.
  - **Done when:** stale artifact를 성공으로 보지 않고 candidate/failed run artifact를 current projection과 분리해 보존한다.

- [x] 3.3 **RED/GREEN** — validated target artifact pair promotion과 projection identity를 구현한다.
  - **Covers:** `Successful target artifact promotion`, `Artifact projection identity`, `Evidence projection reference`
  - **Done when:** validation 성공 시에만 manifest/run_results pair가 current로 교체되고 projection identity가 결과에 포함된다.

### 4. Mutation-aware recovery and reconciliation

- [x] 4.1 **RED** — equal-count content mismatch, stale target과 mutation phase result를 recovery component test로 고정한다.
  - **Covers:** `Post-backfill validation`, `Equal count with different content`, `Mutation-aware recovery result`, `Downstream verification failure`
  - **Done when:** row-count oracle 또는 단일 success flag 때문에 test가 의도대로 실패한다.

- [x] 4.2 **GREEN** — executor를 approval gate, before-state compare-and-replace, content/profile validation과 explicit mutation state 순서로 전환한다.
  - **Done when:** pre-mutation failure와 post-mutation verification failure가 구분되고 content identity가 최종 oracle이다.

- [x] 4.3 **RED/GREEN** — expected-after resume와 diverged target 차단 reconciliation을 구현한다.
  - **Covers:** `Recovery reconciliation`, `Resume verification`, `Diverged target`
  - **Done when:** expected-after state는 overwrite 없이 verification을 재개하고 diverged state는 새 approval을 요구한다.

### 5. Deterministic volume-drop vertical slice

- [x] 5.1 **RED** — stable fixture identity, clean baseline과 controlled `volume_drop` acceptance test를 추가한다.
  - **Covers:** `Recovery vertical-slice evaluation`, `Clean baseline`, `Approved volume-drop recovery`
  - **Done when:** 별도 evaluation composition API 부재로 local integration test가 의도대로 실패한다.

- [x] 5.2 **GREEN** — 기존 synthetic source, lifecycle, candidate workspace, external approval input과 recovery를 조합하는 evaluation API를 구현한다.
  - **Done when:** clean case는 incident가 없고 `volume_drop` case는 detection, impact, approved content recovery와 downstream verification을 통과한다.

- [x] 5.3 **RED/GREEN** — safety failures, replay와 reconciliation evidence를 evaluation case/report에 반영한다.
  - **Covers:** `Replay stability`, `Recovery safety case evaluation`, `Pre-mutation safety failures`, `Post-mutation recovery failure`, `Diverged reconciliation case`
  - **Done when:** 각 case의 mutation 여부, preserved artifact, reconciliation action과 stable evidence projection이 독립 oracle로 검증된다.

### 6. Verification and documentation

- [x] 6.1 변경한 component의 focused test와 domain suite를 실행하고 실패를 분류·수정한다.
  - **Done when:** HMDA ingestion, Data Operations와 Reliability suites가 통과한다.

- [x] 6.2 전체 기본 pytest suite와 Ruff를 실행한다.
  - **Done when:** `uv run pytest`와 `uv run ruff check src tests`가 통과하거나 unrelated baseline failure가 명확히 분리된다.

- [x] 6.3 Canonical domain documentation과 public exports를 새 recovery safety contract에 맞게 갱신한다.
  - **Done when:** `docs/domains`의 owning 문서가 approval binding, content identity, artifact promotion과 reconciliation boundary를 설명한다.

## Self-Review

- [x] 모든 관련 Requirement와 Scenario가 구현 및 테스트에 반영되었는지 확인한다.
- [x] Design의 Decision과 Boundary를 지키면서 중복과 불필요한 복잡성을 제거한다.
- [x] 관련 테스트, 실패 경로와 정적 검사가 통과하는지 확인한다.
- [x] 필요한 문서, 설정과 운영 절차를 갱신한다.
- [x] 알려진 제약과 후속 작업을 명시한다.

## Review Follow-up

- [x] 7.1 승인된 candidate와 실행 source의 staged content identity를 target mutation 전에 비교하고 mismatch zero-mutation regression을 추가한다.
- [x] 7.2 dbt run마다 unique artifact directory를 사용하고 promotion 직전 projection identity를 재확인하는 regression을 추가한다.
- [x] 7.3 artifact pair commit과 backup cleanup을 분리하고 cleanup failure가 committed pair를 손상시키지 않는 regression을 추가한다.
- [x] 7.4 검증한 recovery source를 immutable staged artifact로 고정하고 source replacement TOCTOU regression을 추가한다.
- [x] 7.5 dbt artifact projection digest에 pair boundary를 포함하고 collision regression을 추가한다.
- [x] 7.6 current artifact promotion을 local lock으로 직렬화하고 concurrent promotion regression을 추가한다.
- [x] 7.7 artifact promotion lock을 impact/projection reader와 공유해 mixed current pair read를 차단한다.
- [x] 7.8 promotion lock 획득 뒤 projection identity를 재확인하고 lock-wait artifact mutation regression을 추가한다.
- [x] 7.9 recovery candidate staging failure를 `BackfillValidationError`로 변환하고 regression을 추가한다.
- [x] 7.10 artifact lock setup 오류와 locked body의 artifact read 오류를 분리하고 regression을 추가한다.
- [x] 7.11 recovery temporary staging directory failure를 `BackfillValidationError`로 변환하고 regression을 추가한다.
- [x] 7.12 lifecycle impact analysis와 projection identity를 하나의 shared-lock artifact snapshot에서 결합한다.
- [x] 7.13 artifact lock setup failure가 typed lock error로 변환되는 regression을 추가한다.
- [x] 7.14 post-mutation target dbt validation failure를 vertical-slice safety case evidence로 반환하는 regression을 추가한다.
- [x] 7.15 post-mutation target dbt failure safety case에 prior last-known-good target projection을 기록한다.
- [x] 7.16 target dbt failure evidence의 prior projection identity를 shared artifact lock 안에서 읽는다.
- [x] 7.17 invalid candidate, candidate dbt failure, incomplete approval, stale/diverged target을 execution-level evaluation case로 변환하고 pre-mutation regression을 추가한다.
- [x] 7.18 target validation은 `DataOperationError`만 recovery failure로 변환하고 promotion 이후 exception의 실제 current artifact 경계를 regression으로 고정한다.
- [x] 7.19 current head 기준 focused/full validation 결과와 Plan Review 근거를 갱신한다.
- [x] 7.20 **RED/GREEN** — 첫 recovery 성공 뒤 replay verification failure를 분리해 완료된 recovery, target mutation stage와 `resume_verification` evidence를 보존한다.
- [x] 7.21 **RED/GREEN** — evaluation boundary의 최종 reconciliation action을 명시하고 target dbt failure는 `resume_verification`, stale/diverged target은 `request_new_validation_and_approval` 값까지 검증한다.
- [x] 7.22 **RED/GREEN** — artifact projection byte-read I/O failure를 typed Data Platform error로 구분하고 public Data Operations boundary에서 `run_target_path`, 실패 artifact path를 포함한 `DataOperationError`로 변환한다.
  - **Done when:** Build/promotion read failure가 raw `OSError`를 노출하지 않고 current projection을 변경하지 않는 regression이 통과한다.
- [x] 7.23 **RED/GREEN** — promotion 이후 `DataOperationError`에서 locked current projection을 다시 관찰해 actual artifact state 또는 typed 관찰 실패를 evidence에 기록한다.
- [x] 7.24 current head 기준 focused/domain/full pytest, Ruff, OpenSpec strict validation과 diff check를 실행하고 command/result를 task completion 및 PR evidence에 기록한다.
  - **Evidence:** Initial F1-F4 focused regression 6 passed, review follow-up regression 3 passed, full default pytest 177 passed.
  - **Evidence:** `uv run ruff check src tests`, `openspec validate reliability-mvp-volume-drop-vertical-slice --strict`, `git diff --check`와 editor diagnostics가 통과했다.
