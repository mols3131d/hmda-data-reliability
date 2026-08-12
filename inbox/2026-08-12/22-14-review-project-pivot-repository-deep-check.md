---
type: review
title: Project Pivot Repository Deep Check — 2026-08-12 22:14
description: main@36ef5d8 기준 OpenSpec, RPI skill, null-spike 구현, CI와 상태 문서를 반복 교차검증한 repository review.
status: "completed"
tags:
  - project-pivot
  - repository-status
  - openspec
  - reliability
  - ci
---

> [!NOTE]
> **Verdict: Revise.** 최신 Reliability 구현 자체는 첫 점검보다 완성도가 높았지만, `plan-review` 제거 이후의 workflow drift와 null-spike Task 4.5의 downstream failure evidence 공백이 남아 있다. 우선 null-spike evidence를 닫고 Change를 완료한 뒤 RPI skill의 제거된 Plan Review 개념을 정리하는 순서가 안전하다.

## Overview

| Target | Revision | Scope | Verdict |
| --- | --- | --- | --- |
| Project Pivot repository | `main@36ef5d8` | OpenSpec schema/active Change, RPI skill, null-spike implementation/tests, CI, MVP status | Revise |

## Review Loops

### Loop 1 — Contract and repository state

- `spec-driven-tdd/schema.yaml`은 현재 `proposal → specs → design → tasks → apply`만 소유하고 `plan-review` artifact를 정의하지 않는다.
- 반면 `.agents/skills/pivot-spec-driven-tdd-rpi/SKILL.md`는 여전히 `Plan Review contract`, `Plan Review 상태`, `Plan Review 영향`을 schema-owned 개념으로 반복 참조한다.
- active `reliability-null-spike-recovery-vertical-slice`에도 제거된 `plan-review.md`가 남아 있다.

### Loop 2 — Implementation counter-check

초기에는 `tasks.md`의 `18/24`만 보고 Task 4.5 전체가 미구현일 가능성을 검토했다. 실제 코드를 대조한 결과 이 판단은 과했다.

- success 경로는 baseline/recovery/replay null rate를 기록한다.
- content validation 실패와 null-rate-only mismatch는 서로 다른 reconciliation action으로 분리한다.
- 관련 integration test도 존재한다.

그러나 downstream verification failure에서는 Task 4.5가 요구한 exact null-rate evidence가 보존되지 않는다.

- `post_recovery_lifecycle` 실패가 `_failure_result()`를 호출할 때 baseline/recovery/replay null-rate evidence를 전달하지 않는다.
- target dbt failure도 failure/artifact evidence만 구성하고 이미 확정한 세 null-rate 값을 포함하지 않는다.
- 해당 failure tests 역시 mutation/artifact/failure type은 검증하지만 세 null-rate evidence 보존을 oracle로 두지 않는다.

따라서 Task 4.5는 **부분 구현이며 실제 미완료**로 판정한다.

### Loop 3 — Operational and state verification

- `CI Lite` workflow는 active이며 `src/**`, `tests/**` 변경 PR을 대상으로 한다.
- PR #81 head에는 PR-triggered workflow run과 commit status가 없었다.
- PR timeline에는 merge 약 7분 전 `base_ref_changed`가 있고 그 뒤 head synchronize event 없이 Ready 전환 후 merge됐다.
- 따라서 초기 base가 `main`이 아니어서 CI가 열릴 때 실행되지 않았고, base 변경만으로 새 run이 생성되지 않았을 가능성이 높다. 다만 저장된 event만으로 원인을 확정할 수 없으므로 **강한 가설**로만 기록한다.
- `docs/development/mvp/status.md`는 여전히 2026-08-11 snapshot과 이전 volume-drop active Change blocker를 기록해 current repository lifecycle보다 뒤처져 있다.

## Findings

### F1. RPI skill이 제거된 Plan Review contract를 계속 가정한다

- **Severity** - Major
- **Location** - `.agents/skills/pivot-spec-driven-tdd-rpi/SKILL.md`
- **Evidence** - current schema에는 Plan Review artifact/state가 없지만 skill의 Ownership, Arguments, Entry Conditions, Workflow, Boundaries가 이를 명시적으로 참조한다.
- **Impact** - agent가 존재하지 않는 schema state를 확인하거나 workflow dependency로 오해할 수 있다.
- **Required Change** - 특정 `Plan Review` 명칭과 상태 가정을 제거하고, active schema가 실제로 정의한 planning artifact/dependency만 동적으로 따르도록 정리한다.

### F2. active Change에 제거된 `plan-review.md`가 다시 유입됐다

- **Severity** - Major
- **Location** - `openspec/changes/reliability-null-spike-recovery-vertical-slice/plan-review.md`
- **Evidence** - PR #80에서 schema와 template의 plan-review가 제거됐지만 이후 병합된 PR #81의 active Change에 legacy artifact가 존재한다.
- **Impact** - active Change surface가 current schema와 달라지고 review process state의 ownership이 다시 분산된다.
- **Required Change** - active Change에서 `plan-review.md`를 제거하고 current schema 기준으로 proposal/specs/design/tasks만 유지한다. archived historical artifact는 수정 대상이 아니다.

### F3. Null-spike Task 4.5의 downstream failure evidence가 불완전하다

- **Severity** - Major
- **Location** - `src/project_pivot/reliability/evaluation/null_spike.py`, `tests/reliability/test_null_spike_evaluation.py`, active `tasks.md`
- **Evidence** - success와 quality mismatch 경로는 null-rate evidence를 보존하지만 post-recovery lifecycle/dbt failure 결과에는 baseline/recovery/replay null-rate가 누락된다.
- **Impact** - recovery quality acceptance가 이미 끝난 뒤 downstream 실패가 발생하면 결과만 보고 품질 oracle이 실제로 충족됐는지 복원하기 어렵다.
- **Required Change** - 확정된 세 null-rate evidence를 downstream failure result에도 전달하고 lifecycle/dbt failure tests에 이를 oracle로 추가한 뒤 Task 4.5를 완료한다.

### F4. PR #81에서 CI Lite provenance가 생성되지 않았다

- **Severity** - Minor
- **Location** - PR #81 / `.github/workflows/ci-lite.yml`
- **Evidence** - source/test 변경이 있었지만 PR-triggered workflow run/status가 없고 merge 직전 base 변경 event가 존재한다.
- **Impact** - PR body의 local/pre-push validation과 GitHub CI provenance가 분리된다.
- **Required Change** - 다음 source/test PR은 처음부터 `main`을 base로 열어 CI trigger를 확인한다. 재현되기 전 workflow 자체를 수정하지 않는다.

### F5. MVP status snapshot이 current lifecycle보다 뒤처져 있다

- **Severity** - Minor
- **Location** - `docs/development/mvp/status.md`
- **Evidence** - 2026-08-11 snapshot과 이전 volume-drop active Change cleanup을 현재 blocker로 기록한다.
- **Impact** - 다음 작업 선택 시 이미 끝난 lifecycle 정리를 현재 위험으로 오인할 수 있다.
- **Required Change** - null-spike Change가 실제 완료·archive된 뒤 한 번 갱신해 불필요한 status churn을 피한다.

## Validation

| Check | Evidence | Result |
| --- | --- | --- |
| Schema artifact ownership | current `schema.yaml` 직접 확인 | Pass |
| RPI/schema consistency | current RPI skill과 schema 대조 | Fail |
| Active Change surface | active directory와 `plan-review.md` 확인 | Fail |
| Task 4.5 implementation | null-spike source/test 직접 대조 | Partial |
| CI workflow presence | workflow active 및 path filter 확인 | Pass |
| PR #81 CI provenance | workflow run/status와 PR events 확인 | Not Verified / missing provenance |
| Runtime test execution | 이번 review에서 직접 실행하지 않음 | Not Verified |

## Recommended Route

1. **Reliability Change completion**
   - downstream lifecycle/dbt failure에도 exact null-rate evidence 보존
   - 관련 tests 보강
   - Task 4.5 완료 및 Self-Review 5개 수행
   - active legacy `plan-review.md` 제거
   - current Specs 동기화와 archive gate 확인

2. **RPI skill drift correction — 별도 목적**
   - 제거된 Plan Review 개념 삭제
   - OpenSpec + active `spec-driven-tdd` schema dependency 원칙 유지
   - schema가 실제 제공하는 artifact/dependency만 따르도록 capsule 유지

3. **Status refresh**
   - null-spike Change lifecycle이 끝난 뒤 MVP dashboard 갱신

CI는 다음 실제 source/test PR에서 trigger 여부를 먼저 재현한다. 재현 전에는 workflow 변경을 권장하지 않는다.

## Remaining Risks

- PR #81 body에 기록된 `211 passed`, affected `34 passed`, `ty` pass는 이번 review에서 재실행하지 않았다.
- `inbox` branch는 current `main`보다 뒤처져 있으나 routine artifact direct push는 별도 sync commit과 분리할 수 있다. 이 review에서는 repository history를 불필요하게 넓히지 않기 위해 `main → inbox` sync를 수행하지 않았다.

## Verdict

| Decision | Rationale | Route |
| --- | --- | --- |
| Revise | schema/RPI drift와 Task 4.5의 확인된 evidence 공백이 남아 있다. 나머지 초기 의심은 구현 대조 후 축소했다. | Reliability active Change 우선 완료 → RPI skill 별도 정리 → MVP status 갱신 |
