# MVP Development Status

> **Snapshot:** 2026-08-11  
> **Repository revision:** `99151101cf2872a15985e973c8835b923a3565c6` (`main`)  
> **Implementation basis:** merged PR #48, final head `736732b7940b90486185dc93200161f8ae09a542`  
> **Current-main runtime validation:** ⚪ Not rerun

MVP implementation은 `main`에 병합되어 있다. PR #48 final head의 OpenSpec Tasks는 `49/49` 완료이고 Plan Review는 loop 8 `approved`다. Runtime validation은 final head에 기록된 evidence와 current `main` 재실행 여부를 분리한다.

## Dashboard

| Domain | MVP responsibility | Implementation | Verification |
| --- | --- | :---: | :---: |
| [HMDA Data](hmda-data.md) | controlled drop, partition identity, safe replacement | 🟢 Implemented | 🟢 Verified on PR #48 final head |
| [Data Platform](data-platform.md) | isolated dbt evidence와 projection integrity | 🟢 Implemented | 🟢 Verified on PR #48 final head |
| [Data Operations](data-operations.md) | run-scoped dbt, explicit promotion, identity handoff | 🟢 Implemented | 🟢 Verified on PR #48 final head |
| [Reliability](reliability.md) | volume-drop detection → recovery → evaluation | 🟢 Implemented | 🟢 Verified on PR #48 final head |
| [Orchestration](orchestration.md) | data-plane/control-plane 분리 유지 | ⚪ Boundary preserved | 🟢 Covered by final-head full suite |

### Status Semantics

- 🟢 **Implemented:** snapshot `main`에 목표 구현이 존재한다.
- 🟢 **Verified on PR head:** final implementation head에 validation evidence가 기록되어 있다.
- ⚪ **Boundary preserved:** 이번 MVP에서 새 구현보다 기존 비책임 경계 유지가 목표다.
- Current `main`을 다시 실행하지 않았다면 별도 current-main verification으로 승격하지 않는다.

## Validation Evidence

PR #48 final commit `736732b7940b90486185dc93200161f8ae09a542`의 OpenSpec Tasks 7.24에 다음 evidence가 기록되어 있다.

- focused regression — 6 passed
- review follow-up regression — 3 passed
- full default pytest — 177 passed
- `uv run ruff check src tests` — passed
- `openspec validate reliability-mvp-volume-drop-vertical-slice --strict` — passed
- `git diff --check`와 editor diagnostics — passed

## Next Gate

Current `main`에서 MVP end-to-end acceptance와 관련 regression을 다시 실행한 뒤, 결과를 `status.md`와 `status.yml`에 같은 snapshot으로 갱신한다.

## References

- [MVP Goal](../../mvp.md)
- [MVP Development](README.md)
- OpenSpec: `openspec/changes/reliability-mvp-volume-drop-vertical-slice/tasks.md`
- OpenSpec: `openspec/changes/reliability-mvp-volume-drop-vertical-slice/plan-review.md`
