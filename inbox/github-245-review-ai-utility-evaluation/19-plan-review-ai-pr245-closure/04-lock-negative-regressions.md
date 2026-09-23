# 04 — Lock the Correctness Fixes with Negative Regressions

## Goal

01–03의 수정이 happy-path assertion에만 의존하지 않고 다시 깨지기 어려운 negative regression으로 고정됐는지 확인한다.

## Scope

새 test framework를 만들지 않는다. 01–03에서 이미 충분한 regression test가 추가됐다면 중복 test를 만들지 않고 coverage를 확인하는 것으로 끝낸다.

최소 증명 대상은 다음이다.

1. context overflow → typed preflight rejection, no provider/store call
2. missing required control role → invalid quality basis
3. wrong control case/revision/outcome → fail-closed
4. oversized evidence set → prompt-visible citable IDs == validator allowlist
5. fabricated evidence ID → 계속 rejection

## Validation

- 관련 `tests/review_ai` focused tests를 실행한다.
- utility proof script tests를 실행한다.
- 각 negative test가 실제 defect를 재현할 수 있는 oracle인지 확인한다.
- implementation line coverage만 늘리고 contract를 검증하지 않는 assertion은 추가하지 않는다.

## Done When

F1-F3 각각에 대해 defect가 다시 들어오면 실패할 regression proof가 존재하고 focused suite가 통과하면 Stage 1을 완료한다.
