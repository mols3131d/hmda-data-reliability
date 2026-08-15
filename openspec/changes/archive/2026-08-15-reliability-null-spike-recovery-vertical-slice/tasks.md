---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: Reliability Null-Spike Recovery Vertical Slice Tasks
description: Controlled null-spike recovery와 quality acceptance를 기존 safety primitives 위에 TDD로 구현한다.
tasks_completed: 24
tasks_total: 24
tags:
  - "domain:reliability"
  - "capability:reliability-recovery-backfill"
  - "capability:reliability-evaluation-report"
  - "null-spike"
---

> [!NOTE]
> Current Specs를 선행 volume-drop implementation과 동기화한 뒤, null-spike에 새로 필요한 controlled defect, null-rate false-green guard와 incident-specific evaluation composition만 test-first로 추가한다. Recovery contracts와 executor는 변경하지 않고 기존 safety tests를 회귀 근거로 사용한다.

## Prerequisites

- [x] Archived volume-drop Change의 stable identity, exact approval, reconciliation과 evaluation delta를 current Specs에 동기화하고 OpenSpec validation을 통과한다.
  - **Done when:** `openspec validate --all --json`이 current Specs 전체를 성공으로 보고한다.

## Tasks

### 1. Controlled null-spike contract

- [x] 1.1 **RED** — Single profiled target column, row-count preservation과 exact single-incident gate를 고정하는 evaluator integration tests를 작성한다.
  - **Covers:** `Controlled single-column null spike`, `Read-only lifecycle preservation`
  - **Done when:** happy fixture는 target-column `null_spike` 하나를 만들고 zero/multiple/unrelated incident fixture는 proposal과 mutation 전에 실패해야 한다는 assertion에서 의도한 RED가 발생한다.

- [x] 1.2 **GREEN** — Clean baseline과 controlled `null_spike` target lifecycle을 구성하고 observed defect/cardinality를 검증하는 최소 evaluator entry/result를 구현한다.
  - **Done when:** clean case는 incident가 없고 valid defect case는 선택한 column의 `null_spike` incident 하나와 target identity를 반환하며 ambiguous case는 pre-mutation failure evidence를 반환한다.

### 2. Approved content recovery

- [x] 2.1 **RED** — Original clean fixture와 같은 candidate identity/null rate, exact approval, partition recovery를 연결하는 happy-path test를 작성한다.
  - **Covers:** `Approved null-spike content recovery`, `Null-rate profile evidence`, `Approved null-spike recovery`
  - **Done when:** expected identity, restored null rate 또는 post-recovery incident resolution 중 구현되지 않은 oracle에서 실패한다.

- [x] 2.2 **GREEN** — Original clean fixture로 expected recovery state를 만들고 existing recovery contracts/executor를 조합해 full-partition recovery를 실행한다.
  - **Done when:** candidate identity와 null rate가 clean fixture baseline과 같고 recovery는 `partition_changed`, content validation success와 exact target column null-rate restoration을 반환하며 post-recovery incident가 없다.

### 3. Quality acceptance and replay

- [x] 3.1 **RED** — Incident threshold 아래 residual null-rate candidate가 clean fixture identity/null-rate mismatch로 approval과 mutation 전에 거부되는 test를 작성한다.
  - **Covers:** `Residual-null candidate rejection`
  - **Done when:** candidate/expected identity와 candidate/baseline null-rate evidence를 요구하는 assertion에서 의도한 RED가 발생한다.

- [x] 3.2 **GREEN** — Candidate를 clean fixture expected identity/null-rate에 검증하고 성공 후 exact baseline null-rate와 post-recovery detections를 evidence에 반영한다.
  - **Done when:** original clean candidate는 recovery로 진행하고 residual-null candidate는 target mutation 없이 failed candidate evidence를 반환한다.

- [x] 3.3 **RED/GREEN** — 같은 approved recovery replay가 overwrite 없이 verification을 재개하고 stable content/null-rate evidence를 보존하는 test와 최소 구현을 추가한다.
  - **Covers:** `Null-spike replay stability`
  - **Done when:** replay는 `already_recovered`, `resume_verification`과 동일 expected identity를 반환하며 duplicate 또는 null-rate drift가 없다.

- [x] 3.4 **RED/GREEN** — First recovery 뒤 replay profile failure와 diverged replay가 최초 recovery/mutation evidence를 보존하는 test와 mapping을 추가한다.
  - **Covers:** `Null-spike replay stability`, `Null-spike safety failure evidence`
  - **Done when:** profile failure는 `resume_verification`, diverged replay는 `request_new_validation_and_approval`을 반환하고 first `partition_changed` recovery가 result에 남는다.

### 4. Failure evidence and public surface

- [x] 4.1 **RED/GREEN** — Invalid candidate source, incomplete/mismatched approval, stale target과 diverged target을 null-spike evaluator의 pre-mutation safety evidence로 연결한다.
  - **Covers:** `Null-spike safety failure evidence`
  - **Done when:** 각 case는 target mutation 없이 정확한 failure name과 `request_new_validation_and_approval` 또는 approval failure evidence를 반환한다.

- [x] 4.2 **RED/GREEN** — Candidate dbt failure, target dbt failure와 post-promotion domain failure를 pre/post-mutation artifact evidence로 연결한다.
  - **Covers:** `Null-spike safety failure evidence`
  - **Done when:** candidate failure는 target data와 unchanged current canonical projection을 shared-lock observation으로 보존한다. Target dbt failure는 changed target, `resume_verification`과 actual current 또는 last-known-good canonical projection을 기록한다. Post-promotion failure는 actual current projection 또는 locked observation failure를 기록한다.

- [x] 4.3 Reliability evaluation package와 top-level reliability package에서 null-spike evaluator와 result를 export한다.
  - **Done when:** public import smoke test와 existing reliability imports가 통과한다.

- [x] 4.4 **RED/GREEN** — Evaluation database path preflight를 모든 side effect보다 먼저 실행한다.
  - **Covers:** `Existing evaluation database`, `Aliased evaluation database paths`, `Evaluation path preflight`
  - **Done when:** Existing target, workspace clean 또는 candidate database와 세 path 사이 physical alias는 workspace directory/file/database 생성, source load와 callback 전에 거부되고 기존 content와 workspace 부재 상태가 보존된다.

- [x] 4.5 **RED/GREEN** — Exact null-rate evidence와 content/null-rate quality reconciliation을 구현한다.
  - **Covers:** `Independent null-rate acceptance evidence`
  - **Done when:** Success evidence는 baseline/recovery/replay null rate를 포함한다. Content validation failure는 새 validation과 approval을 요구하고, content validation은 성공하지만 null rate만 다르면 `resume_verification`으로 종료한다. Recovery와 replay quality acceptance가 완료된 뒤 downstream verification이 실패해도 이미 확정한 baseline/recovery/replay null-rate evidence를 보존한다.

- [x] 4.6 **RED/GREEN** — Candidate와 target validation `ValueError`를 mutation-aware structured failure로 변환한다.
  - **Covers:** `Null-spike safety failure evidence`
  - **Done when:** Candidate `ValueError`는 pre-mutation, target `ValueError`는 recovered target과 artifact observation을 보존한 post-mutation failure result로 종료된다.

### 5. Documentation and validation

- [x] 5.1 Reliability domain documentation에 beyond-MVP null-spike evaluation API, content identity와 null-rate oracle의 책임 분리를 반영한다.
  - **Done when:** 문서가 read-only lifecycle, external approval과 unchanged recovery executor boundary를 정확히 설명한다.

- [x] 5.2 Focused null-spike evaluation tests와 existing recovery/evaluation regression tests를 실행한다.
  - **Done when:** 변경 module과 `tests/reliability`의 관련 test가 기본 marker policy로 통과한다.

- [x] 5.3 Ruff, Markdown formatter와 OpenSpec validation을 실행한다.
  - **Done when:** changed Python/Markdown files와 active Change가 format, lint와 OpenSpec validation을 통과한다.

- [x] 5.4 Default pytest suite를 실행하고 결과를 validation evidence로 기록한다.
  - **Done when:** `uv run pytest`가 통과하거나 현재 변경과 무관한 baseline failure가 명확히 분류된다.

## Self-Review

- [x] 모든 관련 Requirement와 Scenario가 구현 및 테스트에 반영되었는지 확인한다.
- [x] Design의 Decision과 Boundary를 지키면서 중복과 불필요한 복잡성을 제거한다.
- [x] 관련 테스트, 실패 경로와 정적 검사가 통과하는지 확인한다.
- [x] 필요한 문서, 설정과 운영 절차를 갱신한다.
- [x] 알려진 제약과 후속 작업을 명시한다.
