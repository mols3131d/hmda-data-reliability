# MVP Development Status

> **Snapshot:** 2026-08-11  
> **Observed main:** `99151101cf2872a15985e973c8835b923a3565c6`  
> **Implementation basis:** PR #48 final head `736732b7940b90486185dc93200161f8ae09a542`

현재 MVP 구현은 `main`에 병합됐다. 구현과 final-head validation은 완료됐고, 남은 즉시 작업은 완료된 OpenSpec Change의 lifecycle 정리다.

## Overall

| Gate | Status | Evidence |
| --- | :---: | --- |
| MVP implementation merged | 🟢 Done | PR #48 → merge commit `02aa81f` |
| OpenSpec tasks | 🟢 Done | `49/49` |
| Plan Review | 🟢 Approved | loop 8 |
| Final-head runtime validation | 🟢 Verified | full default pytest `177 passed` + focused regressions |
| Current-main runtime rerun | ⚪ Not rerun | final head 이후 관찰된 변경은 runtime source/test를 바꾸지 않음 |
| OpenSpec Change lifecycle | 🟡 Pending | completed Change가 active directory에 남아 있음 |

## Domain Dashboard

| Domain | MVP goal | State |
| --- | --- | :---: |
| [HMDA Data](hmda-data.md) | controlled drop과 안전한 partition 복원 근거 | 🟢 Implemented |
| [Data Platform](data-platform.md) | dbt evidence identity와 last-known-good 보존 | 🟢 Implemented |
| [Data Operations](data-operations.md) | validation과 current-state 변경 경계 | 🟢 Implemented |
| [Reliability](reliability.md) | volume-drop detection → approved recovery → evidence | 🟢 Implemented |
| [Orchestration](orchestration.md) | data-plane/control-plane 경계 유지 | 🟢 Preserved |

### Status Semantics

- 🟢 **Implemented:** observed `main`에 해당 MVP 결과가 존재한다.
- 🟢 **Preserved:** 새 기능을 추가하지 않고 명시한 비책임 경계를 유지했다.
- 🟢 **Verified:** PR #48 final implementation head에서 validation evidence가 기록됐다.
- 🟡 **Pending:** 구현 완료와 별개로 repository lifecycle 정리가 남아 있다.
- ⚪ **Not rerun:** current `main`에서 같은 runtime validation을 다시 실행하지 않았다.

## Validation Evidence

PR #48 final commit `736732b7940b90486185dc93200161f8ae09a542`의 OpenSpec Tasks 7.24에 다음 evidence가 기록되어 있다.

- focused regression — 6 passed
- review follow-up regression — 3 passed
- full default pytest — 177 passed
- `uv run ruff check src tests` — passed
- `openspec validate reliability-mvp-volume-drop-vertical-slice --strict` — passed
- `git diff --check`와 editor diagnostics — passed

Final head 이후 observed `main`까지의 추가 변경에서는 `src/`, `tests/`, `dbt/` runtime delta를 확인하지 않았다. 따라서 final-head validation과 current-main 재실행 여부를 구분해 기록한다.

## Next

1. `reliability-mvp-volume-drop-vertical-slice`의 current Spec 일관성을 확인하고 sync/archive lifecycle을 정리한다.
1. Runtime code 또는 test가 바뀌면 영향받는 MVP validation을 다시 실행하고 이 dashboard를 갱신한다.
1. 다음 incident 확장은 현재 MVP 완료 상태와 분리된 새 Research/Change로 다룬다.

## References

- [MVP Goal](../../mvp.md)
- [MVP Development](README.md)
- `openspec/changes/reliability-mvp-volume-drop-vertical-slice/tasks.md`
- `openspec/changes/reliability-mvp-volume-drop-vertical-slice/plan-review.md`
- `inbox/2026-08-11/19-03-research-reliability-post-pr-48-next-work.md`
