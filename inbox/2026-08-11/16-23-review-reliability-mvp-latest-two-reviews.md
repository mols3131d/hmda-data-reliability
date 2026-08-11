---
type: review
title: PR #48 최신 2개 리뷰 Inbox 정리
description: reliability volume-drop MVP PR의 current head에 대한 최신 두 review를 중복 없이 통합해 남은 finding과 후속 조치를 정리한다.
status: completed
tags:
  - reliability
  - recovery
  - volume-drop
  - pull-request
  - review
---

> [!NOTE]
> 최신 두 review는 모두 current head `e5e613e2`를 대상으로 했고, 두 번째 review가 최신 요약이다. 이전 approval, staged source, artifact promotion, profile failure, deterministic sampling과 integration oracle finding은 해결된 것으로 확인했지만, safety-case 실행 evidence 2건과 stale `plan-review.md` 1건 때문에 판정은 **Revise**다.

## Overview

| Target | Revision | Scope | Verdict |
| --- | --- | --- | --- |
| PR #48 `reliability-mvp-volume-drop-vertical-slice` | `e5e613e2` | 최신 두 review의 implementation, tests, OpenSpec와 validation evidence | Revise |

## Latest Review Timeline

| Review | 기준 | 결론 |
| --- | --- | --- |
| 이전 최신 review | `e5e613e2` + latest `main` synthetic merge | F1/F2 safety-case finding과 plan-review freshness finding 유지 |
| 최신 review | `e5e613e2` + 최신 review template/OpenSpec/source/tests | 아래 F1-F3를 최신 actionable summary로 유지 |

## Findings

### F1. Pre-mutation safety failure가 evaluation case로 반환되지 않는다

- **Severity** - Major
- **Location** - `src/project_pivot/reliability/evaluation/volume_drop.py`의 `evaluate_volume_drop_vertical_slice()`, `src/project_pivot/reliability/evaluation/recovery_case.py`
- **Evidence** - `validate_candidate()`와 `approve()`/`execute_approved_backfill()`이 safety-case adapter 밖에서 실행된다. invalid candidate, candidate dbt failure, incomplete approval, stale/diverged target이 발생하면 `EvaluationCaseResult` 없이 예외가 전파된다. 현재 safety-case unit test는 `build_recovery_evaluation_case()`에 상태를 수동 주입한다.
- **Impact** - `reliability-evaluation-report` Spec의 실행형 failure acceptance가 false-green이 될 수 있고, 실패·retry evidence가 report에 남지 않는다.
- **Required Change** - 기존 recovery/data-operations domain error를 작은 execution-level adapter에서 구조화된 `EvaluationCaseResult`로 변환한다. invalid candidate, candidate dbt failure, incomplete approval, stale target, diverged target의 실제 failure-boundary regression을 추가한다.

### F2. Post-promotion exception이 실제 artifact state와 다른 evidence를 기록할 수 있다

- **Severity** - Major
- **Location** - `src/project_pivot/reliability/evaluation/volume_drop.py`의 target validation 처리 경계
- **Evidence** - evaluator는 target validation 전에 prior projection을 읽고 `validate_target()`의 모든 `Exception`을 recovery dbt failure로 처리하면서 prior projection을 evidence로 기록한다. 그러나 callback은 promotion 이후에도 예외를 발생시킬 수 있다. promotion은 성공했지만 후속 read/validation이 실패하면 current artifact는 새 projection인데 evidence는 prior projection으로 남을 수 있다.
- **Impact** - evidence-first MVP에서 failure stage와 preserved/promoted artifact evidence가 실제 filesystem state와 분리된다.
- **Required Change** - catch 범위를 pre-promotion dbt/domain failure contract로 제한하거나, 예외 시 shared lock 아래 current projection을 재관찰해 실제 artifact state를 기록한다. promotion 이후 failure regression을 추가한다.

### F3. `plan-review.md`의 완료·validation 근거가 current head보다 오래됐다

- **Severity** - Medium
- **Location** - `openspec/changes/reliability-mvp-volume-drop-vertical-slice/plan-review.md`
- **Evidence** - Review Loop 5는 unresolved finding 없음과 `162 passed`를 기록하지만 current head `e5e613e2` 이후 core implementation/test가 다시 변경됐다. 최신 review는 current head의 GitHub Actions workflow/status도 확인하지 못했다.
- **Impact** - canonical planning artifact가 최신 readiness를 과대 표시해 Completion Gate 판단과 artifact 일관성을 흐린다.
- **Required Change** - F1/F2 수정 후 current head에서 focused/full validation을 수행하고 새 plan-review loop로 현재 근거를 갱신한다. 이전 `approved` 근거를 최신 head 검증으로 간주하지 않는다.

## Resolved Before These Reviews

- Approval action immutability
- Approved candidate와 staged source binding
- Unique dbt run directory와 promotion identity 재검증
- Artifact backup cleanup failure 보호
- Profile failure의 mutation-aware state
- Deterministic sampling tie ordering
- Failed-run context 보존
- 실제 `run_dbt_build()`/promotion boundary integration oracle

## Validation

| Check | Evidence | Result |
| --- | --- | --- |
| Latest two PR reviews inspected | PR #48 timeline의 마지막 2개 review, 모두 `e5e613e2` 대상 | Pass |
| Latest review synthesis | 중복 finding을 F1-F3으로 통합하고 최신 review를 우선함 | Pass |
| Reviewer runtime validation | 최신 두 review 모두 직접 실행하지 않고 정적 교차검토로 작성됨 | Not Verified |
| Local workspace validation | 별도 실행에서 `169 passed`, Ruff 통과, OpenSpec strict validation 통과 | Pass |

## Remaining Risks

- Local full suite 통과만으로 F1의 실제 failure-boundary coverage와 F2의 post-promotion exception 경계가 충족됐다고 볼 수 없다.
- 이 문서는 review evidence를 정리한 non-canonical Inbox artifact다. Requirement와 최종 계획 상태는 OpenSpec owning artifact에 반영해야 한다.

## Verdict

| Decision | Rationale | Route |
| --- | --- | --- |
| Revise | 최신 두 review가 공통으로 F1/F2 구현 finding과 F3 planning freshness finding을 유지한다. | `src/project_pivot/reliability/evaluation/`, 관련 tests, `openspec/.../plan-review.md` |
