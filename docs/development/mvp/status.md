# MVP Development Status

> **Snapshot:** 2026-08-11  
> **Repository revision:** `02aa81fbd9e3ca55cfb3b3eacddfbea70db4fd80` (`main`)  
> **Implementation basis:** merged PR #48  
> **Current-main validation:** ⚪ Not rerun after merge

MVP implementation은 `main`에 병합되어 있다. Validation은 PR #48 description에 보고된 결과를 기록하며, 이 문서 작업에서 직접 실행한 결과나 final PR head에 귀속된 결과로 표현하지 않는다.

## Dashboard

| Domain | MVP responsibility | Implementation | Verification |
| --- | --- | :---: | :---: |
| [HMDA Data](hmda-data.md) | controlled drop, partition identity, safe replacement | 🟢 Implemented | 🟡 Reported in PR #48 |
| [Data Platform](data-platform.md) | isolated dbt evidence와 projection integrity | 🟢 Implemented | 🟡 Reported in PR #48 |
| [Data Operations](data-operations.md) | run-scoped dbt, explicit promotion, identity handoff | 🟢 Implemented | 🟡 Reported in PR #48 |
| [Reliability](reliability.md) | volume-drop detection → recovery → evaluation | 🟢 Implemented | 🟡 Reported in PR #48 |
| [Orchestration](orchestration.md) | data-plane/control-plane 분리 유지 | ⚪ Boundary preserved | 🟡 Covered by reported full suite |

### Status Semantics

- 🟢 **Implemented:** snapshot revision에 목표 구현이 존재한다.
- 🟡 **Reported:** 관련 PR에 validation 결과가 보고됐지만 이 snapshot에서 독립적으로 다시 실행하지 않았다.
- ⚪ **Boundary preserved:** 이번 MVP에서 새 구현보다 기존 비책임 경계 유지가 목표다.

## Validation Evidence

PR #48 description에 다음 validation이 보고되어 있다.

- `uv run pytest tests/reliability/test_evaluation_report.py -q` — 7 passed
- `uv run pytest -q` — 170 passed
- `uv run ruff check src tests` — passed
- `ty check` — passed via pre-commit hook
- `openspec validate reliability-mvp-volume-drop-vertical-slice --strict` — passed
- pre-push regression — 170 passed

PR metadata의 final head는 `736732b7940b90486185dc93200161f8ae09a542`지만 description 내부의 `Current head` 표기는 `2b6d42d`로 남아 있다. 따라서 위 validation을 특정 final revision의 실행 결과로 단정하지 않는다.

## Next Gate

Current `main`에서 MVP end-to-end acceptance와 관련 regression을 다시 실행한 뒤, 결과를 `status.md`와 `status.yml`에 같은 snapshot으로 갱신한다.

## References

- [MVP Goal](../../mvp.md)
- [MVP Development](README.md)
- PR #48: `feat: reliability volume-drop MVP vertical slice 추가`
