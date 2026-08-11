# MVP Development Status

> **Snapshot:** 2026-08-11  
> **Repository revision:** `02aa81fbd9e3ca55cfb3b3eacddfbea70db4fd80` (`main`)  
> **Implementation basis:** merged PR #48  
> **Current-main validation:** ⚪ Not rerun after merge

MVP implementation은 `main`에 병합되어 있다. 다만 아래 validation evidence는 PR #48 head에서 수행된 결과이며 merge commit 자체를 다시 실행한 결과로 표현하지 않는다.

## Dashboard

| Domain | MVP responsibility | Implementation | Verification |
| --- | --- | :---: | :---: |
| [HMDA Data](hmda-data.md) | controlled drop, partition identity, safe replacement | 🟢 Implemented | 🟡 Audited on PR #48 head |
| [Data Platform](data-platform.md) | isolated dbt evidence와 projection integrity | 🟢 Implemented | 🟡 Audited on PR #48 head |
| [Data Operations](data-operations.md) | run-scoped dbt, explicit promotion, identity handoff | 🟢 Implemented | 🟡 Audited on PR #48 head |
| [Reliability](reliability.md) | volume-drop detection → recovery → evaluation | 🟢 Implemented | 🟡 Audited on PR #48 head |
| [Orchestration](orchestration.md) | data-plane/control-plane 분리 유지 | ⚪ Boundary preserved | 🟡 Audited by full suite on PR #48 head |

### Status Semantics

- 🟢 **Implemented:** snapshot revision에 목표 구현이 존재한다.
- 🟡 **Audited:** 관련 PR revision에서 validation evidence가 있지만 snapshot revision에서 다시 실행하지 않았다.
- ⚪ **Boundary preserved:** 이번 MVP에서 새 구현보다 기존 비책임 경계 유지가 목표다.

## Validation Evidence

PR #48 head `736732b7940b90486185dc93200161f8ae09a542`에서 기록된 validation:

- `uv run pytest tests/reliability/test_evaluation_report.py -q` — 7 passed
- `uv run pytest -q` — 170 passed
- `uv run ruff check src tests` — passed
- `ty check` — passed via pre-commit hook
- `openspec validate reliability-mvp-volume-drop-vertical-slice --strict` — passed
- pre-push regression — 170 passed

## Next Gate

Current `main`에서 MVP end-to-end acceptance와 관련 regression을 다시 실행한 뒤, 결과를 `status.md`와 `status.yml`에 같은 snapshot으로 갱신한다.

## References

- [MVP Goal](../../mvp.md)
- [MVP Development](README.md)
- PR #48: `feat: reliability volume-drop MVP vertical slice 추가`
