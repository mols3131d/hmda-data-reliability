# Foundation Blocker Resolution Plan

## B2 — Silver staging oracle

**목표:** 구현 변경 없이 staging contract를 test로 고정한다.

현재 `stg_hmda_loans.sql`은 row 보존, nullable column 유지, `loan_amount`/`income`의 `try_cast`를 이미 구현한다. 문제는 integration test가 staging을 읽지 않고 mart 결과만 검증한다는 것이다.

**변경**

- `tests/dbt/test_analytics_foundation.py`
- fixture에 malformed numeric 값을 1개 포함.
- dbt build 후 `staging.stg_hmda_loans`를 직접 조회.
- 다음 oracle 추가:

  - raw 5 rows → staging 5 rows
  - `state_code`, `county_code` null 보존
  - valid numeric은 `DOUBLE`
  - malformed `loan_amount`/`income` → `NULL`
- 기존 mart/idempotency assertion은 유지.

**Close**
`uv run pytest tests/dbt/test_analytics_foundation.py`

---

## B4 — OpenSpec / documentation lifecycle

현재 active EDA change가 2개이고 둘 다 실제 task는 완료 상태다. 두 번째 change는 `16/16`; 첫 번째는 checkbox 완료 상태와 front matter가 불일치한다.

canonical `hmda-eda-baseline`에는 이미 최종 six-core/evidence 계약이 반영돼 있다.

**변경**

1. 두 change의 delta가 canonical spec에 반영됐는지 최종 대조.
1. 첫 change의 stale task metadata를 실제 task 상태와 정합화.

   - `0/21 → 21/21`처럼 추정해서 고치지 말고 실제 관리 단위 재계산.
1. 완료된 EDA change 2개를 archive.
1. root `README.md`에 최소 navigation 추가:

   - Architecture
   - Development
   - **Foundation Readiness**
1. readiness에서 B4 제거.

현재 README는 프로젝트 설명 한 줄뿐이다.

---

## B1 — Actual-source provenance

현재 retained evidence는 `repository_revision`에 `-dirty`가 기록되어 있지만 generator는 dirty worktree를 명시적으로 거부한다.

**중요:** B1을 먼저 하면 안 된다.

1. B2/B4 변경을 완료하고 commit.
1. `git status`가 clean인지 확인.
1. evidence tests 실행.
1. `uv run python scripts/run_actual_source.py`
1. 생성된

   - `docs/references/hmda_eda_reference.json`
   - `docs/references/hmda_eda.md`
     검토.
1. revision에 `-dirty`가 없고 source SHA·Markdown/JSON metric이 일치하는지 확인.
1. 생성 evidence commit.

generator의 clean-tree invariant 자체는 이미 component test로 고정돼 있으므로 특별한 결함이 발견되지 않는 한 script 수정은 필요 없다.

## Final Gate

마지막으로 Foundation focused suite를 실행한 뒤 `readiness.md`와 `readiness.yml`을 **실제 검증 결과와 최종 revision 기준으로 다시 생성/갱신**한다.

현재 readiness는 과거 revision `b34a785...`를 audit 대상으로 하지만 현재 `main` HEAD는 `1dc4753...`이다. 따라서 blocker만 삭제하는 식의 편집은 금지하고 재평가해야 한다.

**완료 기준: B1/B2/B4 없음 + current HEAD runtime verification Passing → Foundation GO.**
