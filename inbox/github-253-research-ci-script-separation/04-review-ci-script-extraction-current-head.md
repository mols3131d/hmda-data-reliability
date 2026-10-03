---
type: review
title: CI Script Extraction Current Head Review
description: PR #253 현재 head의 CI script extraction 구현을 baseline, 테스트와 원격 CI evidence에 대조하고 merge 전 필요한 수정 사항을 기록한다.
tags:
  - ci
  - github-actions
  - testing
---

# CI Script Extraction Current Head Review

> [!IMPORTANT]
> **Changes required**: script extraction 자체에서는 큰 correctness 회귀를 찾지 못했지만, workflow-only 변경에서 기존 Tach admission 검증을 제거한 뒤 이를 완전히 대체하는 contract test가 없어 Medium finding 1건이 남는다. 또한 PR description과 revision metadata가 실제 구현 상태보다 오래되어 review readiness 관점의 blocker로 남는다.

- **Target**: PR [#253](https://github.com/mols3131d/hmda-data-reliability/pull/253)
- **Branch**: `agent/research-ci-script-separation`
- **Reviewed Base**: `5532dca2fd93696d40ba870471fa2359c5662335`
- **Reviewed Head**: `60e73c07a0386a43d165955e46bb74f3a6a9def3`
- **Scope**: PR 전체 diff 중 CI workflow, `scripts/ci/`, classifier routing, CI contract tests, 관련 CI/testing documentation과 current validation evidence.

Repository의 top-level review contract는 가능한 경우 `review-lead` 기반 dual-perspective review를 요구한다. 이번 실행 환경에서는 해당 subagent를 직접 호출할 수 없어, 동일 컨텍스트에서 baseline·diff·test·CI evidence를 직접 검증했다. 따라서 이 보고서를 repository가 정의한 독립 `review-lead` 결과와 동급으로 표현하지 않는다.

## Findings

### 🟡 Medium — F1 · Workflow 변경이 Tach admission step을 깨뜨려도 green이 될 수 있음

- **Location**
  - `scripts/ci/classify_changes.sh`
  - `tests/scripts/test_ci_classifier.py`
  - `.github/workflows/ci-lite.yml`
- **Evidence**
  - Baseline classifier는 `.github/workflows/*` 변경 시 `tach=true`를 선택해 실제 `Check Python dependency boundaries` step을 실행했다.
  - 현재 classifier는 `.github/workflows/*|scripts/ci/*` 변경을 `tests/scripts/test_ci_classifier.py`와 `tests/scripts/test_ci_steps.py`로 라우팅하고, workflow-only 변경에서는 `tach=false`를 유지한다.
  - 현재 classifier contract test는 workflow-only 변경에서 `tach=false`를 명시적으로 기대한다.
  - 현재 workflow-related test는 Tach setup 조건과 `uv run --no-sync tach check` 문자열의 존재를 확인하지만, 해당 step이 함께 실행해야 하는 `tests/scripts/test_tach.py`, `tests/scripts/test_tach_config.py`, `tests/review_ai/test_dependency_boundaries.py` 전체 command 계약을 검증하지 않는다.
  - Reviewed head의 GitHub Actions에서는 `Check Python dependency boundaries` step이 실제로 skipped였다.
- **Reachability**
  - 후속 PR이 `.github/workflows/ci-lite.yml`의 Tach step에서 `tests/scripts/test_tach_config.py` 같은 필수 regression test를 실수로 제거하되 `uv run --no-sync tach check`는 남기는 경우, classifier는 `tach=false`를 선택한다.
  - 이때 실제 Tach admission step은 실행되지 않고 현재 contract test도 삭제된 test target을 검출하지 못할 수 있다.
- **Impact:** CI admission 자체를 수정하는 PR이 dependency-boundary 검증 경로를 부분적으로 깨뜨리고도 green이 될 수 있다. 이는 영향 범위를 확신할 수 없으면 validation을 넓히거나 selector를 실패시켜야 한다는 CI fail-safe 원칙을 약화한다.
- **Required Change**
  - 가장 작은 수정은 `.github/workflows/*` 변경에 대한 기존 `tach=true` 선택을 유지하는 것이다.
  - Tach 실행 비용을 의도적으로 제거하려면, 먼저 `test_ci_steps.py`가 Tach step의 selector와 전체 command/target 계약을 충분히 검증해 실제 admission step 실행을 대체할 수 있도록 해야 한다.

## Validation

- ✅ Pass — Current PR state 확인: open, draft, mergeable, reviewed head `60e73c07a0386a43d165955e46bb74f3a6a9def3`.
- ✅ Pass — Baseline/current classifier 대조: workflow 변경에 대한 `tach=true` 제거와 CI contract target 추가를 직접 비교했다.
- ✅ Pass — Current workflow 대조: CI step wiring, `FULL_UNIT`/`CI_TARGETS`, Tach step command를 확인했다.
- ✅ Pass — Current contract tests 대조: `test_ci_classifier.py`, `test_ci_steps.py`의 routing, marker, workflow assertion 범위를 확인했다.
- ✅ Pass — GitHub Actions: reviewed head의 `CI Lite` run은 성공했고 Markdown/Inbox/Python/selected tests는 통과했다.
- ⚪ Not Verified — 이번 리뷰에서 pytest와 Bash validation을 별도로 재실행하지 않았다. 현재 remote CI success와 repository에 보존된 local validation evidence를 참고했다.
- ⚪ Not Verified — repository가 정의한 `review-lead` dual-perspective subagent orchestration은 현재 실행 환경에서 사용할 수 없어 수행하지 못했다.

## Remaining Risks

- ⚠️ 기존 상태에서 이미 존재하던 Git C-quoted 특수 파일명 누락과 OpenSpec intermediate dangling symlink 제한은 이번 변경이 새로 만든 regression으로 보지 않으며 별도 follow-up으로 유지한다.
- ⚠️ PR title과 description은 여전히 조사 단계만 설명하고 `head: 4f6c996`을 기록한다. 실제 reviewed head는 `60e73c07…`이며 구현·테스트·원격 CI evidence까지 추가되었으므로, 현재 PR metadata는 review-readiness evidence로 stale하다. 코드 finding과 별개로 인간 리뷰 진입 전 갱신해야 한다.

```yaml
revision:
  base: 5532dca2fd93696d40ba870471fa2359c5662335
  head: 60e73c07a0386a43d165955e46bb74f3a6a9def3
```
