---
type: review
title: PR #81 Post-Merge Reliability Review
description: PR #81의 main 병합 결과와 null-spike recovery evidence 계약, 후속 검증 필요성을 점검한다.
status: "completed"
tags:
  - "domain:reliability"
  - "capability:reliability-evaluation-report"
  - "null-spike"
  - "pr:81"
---

> [!NOTE]
> PR #81의 Git 병합 자체는 정상 완료됐다. 다만 병합된 `main@36ef5d8b42d2ea6e701110c0a630cbb789e7fcc0`에는 OpenSpec Task 4.5가 의도적으로 다시 열린 상태로 남아 있으며, recovery와 replay quality acceptance 이후 downstream failure에서 baseline/recovery/replay null-rate evidence를 보존하는 계약은 아직 구현·테스트로 닫히지 않았다. 병합을 되돌릴 근거는 확인하지 않았고, 범위를 좁힌 후속 fix PR로 이 잔여 계약을 완료하는 것이 적절하다.

## Overview

| Target | Revision | Scope | Verdict |
| --- | --- | --- | --- |
| PR #81 `feat(reliability): null-spike recovery 추가` | merge `36ef5d8b42d2ea6e701110c0a630cbb789e7fcc0` | 병합 결과, null-rate evidence 계약, 테스트/검증 상태 | Revise |

### Scope Boundary

- `plan-review.md` 존재 여부는 이 리뷰의 finding에서 제외한다.
- inbox artifact promotion 경로는 이번 post-merge 기능 판정의 blocker로 다루지 않는다.
- 기존 범위를 넘어 recovery executor, lifecycle 내부 동작 또는 multi-column recovery 재설계는 제안하지 않는다.

## Findings

### F1. Downstream failure에서 확정된 null-rate evidence가 보존되지 않는다

- **Severity** - Medium
- **Location** - `src/project_pivot/reliability/evaluation/null_spike.py`, `tests/reliability/test_null_spike_evaluation.py`, OpenSpec Task 4.5
- **Evidence**
  - 성공 경로는 `baseline-null-rate`, `recovery-null-rate`, `replay-null-rate`를 `post_recovery_case.evidence_refs`에 명시적으로 추가한다.
  - `failed_recovery_quality`와 `failed_replay_quality`도 해당 단계에서 이용 가능한 null-rate evidence를 명시적으로 전달한다.
  - recovery와 replay quality acceptance가 모두 성공한 뒤 `post_recovery_lifecycle`가 실패하면 `_failure_result(...)` 호출에는 recovery/replay 객체만 전달되고 세 null-rate evidence는 전달되지 않는다.
  - target dbt validation failure 경로도 failure/artifact observation evidence를 새로 구성하지만 baseline/recovery/replay null-rate evidence를 추가하지 않는다.
  - `_failure_result()`는 전달받은 `evidence_refs`, exception context, artifact observation은 보존하지만 recovery/replay profile에서 null-rate evidence를 파생하지 않는다.
  - success test는 세 null-rate evidence를 직접 assert하지만 post-recovery lifecycle/artifact-lock failure test는 mutation, reconciliation, artifact projection과 exception evidence만 확인한다.
  - `openspec/changes/reliability-null-spike-recovery-vertical-slice/tasks.md`의 Task 4.5는 이 조건을 완료 기준으로 명시한 채 `[ ]` 상태다.
- **Impact** - recovery와 replay의 content/null-rate quality acceptance가 이미 성공했다는 독립 근거가 downstream verification failure 결과에서 사라진다. 전체 case는 failure로 남으므로 false-success 문제는 아니지만, 실패 시점의 recovery 품질 판단 근거가 불완전해져 reconciliation과 사후 분석의 증거 품질이 낮아진다.
- **Required Change** - recovery와 replay quality acceptance가 모두 완료된 이후의 downstream failure branch에서만 세 null-rate evidence를 보존한다. pre-mutation, recovery failure, replay quality 미완료 경로까지 일괄 주입하지 않는다. 기존 evidence string 형식을 재사용하고, 최소한 post-recovery lifecycle failure와 target validation failure에 focused regression assertion을 추가한다.

## Validation

| Check | Evidence | Result |
| --- | --- | --- |
| PR merge state | PR #81은 `merged=true`, merge commit `36ef5d8b42d2ea6e701110c0a630cbb789e7fcc0` | Pass |
| Main revision | 보고서 작성 시점의 `main` HEAD가 위 merge commit과 동일 | Pass |
| Git integration | PR은 `main` 대상으로 conflict-free 상태에서 병합됨 | Pass |
| Task tracking | Task 4.5 `[ ]`, frontmatter `tasks_completed: 18`, `tasks_total: 24` | Revise |
| Success null-rate evidence | success path와 integration test가 baseline/recovery/replay null rate를 기록·검증 | Pass |
| Downstream failure evidence | lifecycle/target validation failure 경로에서 세 null-rate evidence 보존 로직과 regression assertion을 확인하지 못함 | Fail |
| Merge-commit CI/status | merge commit에 GitHub combined status와 PR-triggered workflow run이 확인되지 않음 | Not Verified |
| PR 기록 검증 | PR 본문에 merge 전 `211 passed`, affected `34 passed`, `ty`와 format/check 통과가 기록됨 | Pass (recorded) |

## Remaining Risks

- PR 본문의 실행 결과는 merge 전 검증 기록이며 merge commit 자체에서 재실행된 CI 근거는 없다.
- Self-Review checklist 5개가 아직 미완료다. 이것만으로 별도 기능 defect를 만들지는 않지만 Task 4.5 후속 fix와 함께 다시 닫는 편이 적절하다.
- 현재 finding은 null-rate evidence 보존에 한정한다. recovery/lifecycle 전체 설계를 다시 여는 근거는 확인하지 않았다.

## Verdict

| Decision | Rationale | Route |
| --- | --- | --- |
| Revise | 병합은 정상이나 Task 4.5의 downstream null-rate evidence 계약이 `main`에서 아직 미완료다. rollback보다 국소 후속 수정이 적절하다. | 최신 `main`에서 별도 `fix` PR로 Task 4.5 구현·focused tests·Self-Review 완료 |
