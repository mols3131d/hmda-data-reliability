# 11 — Assess Review Readiness

## Goal

Repository의 Review Readiness 기준으로 PR #245가 사람의 최종 review/merge 판단을 받을 충분한 evidence를 갖췄는지 평가한다.

## Preconditions

08–10의 current-head validation과 fresh review가 모두 있어야 한다.

## Assessment

Repository가 정의한 `ready / not_ready / blocked` 의미를 그대로 사용한다.

`ready` 판정에는 최소한 다음이 필요하다.

- description claim과 final diff가 일치함
- validation evidence가 current base/head에 적용됨
- blocking review finding이 없음
- remaining limitation과 `Not Verified` 항목이 명확함
- review scope를 방해하는 unrelated change가 없음

`ready`는 correctness approval, independent approval 또는 merge authorization을 뜻하지 않는다.

## Lifecycle Boundary

Agent는 readiness를 평가할 수 있다. Draft → Ready 상태 변경은 현재 repository policy와 해당 시점의 명시적 사용자 요청을 확인한 뒤에만 수행한다.

사용자 요청이 없다면 `ready` 판정과 근거만 보고하고 상태는 변경하지 않는다.

## Done When

Current state에 대해 근거 있는 readiness 판정이 있고, `ready`라면 다음 lifecycle action에 필요한 인간 결정을 명확히 요청할 수 있으면 완료한다.
