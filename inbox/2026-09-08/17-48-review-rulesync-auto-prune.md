---
type: review
title: "Rulesync target Skill projection auto-prune review"
description: "rulesync.py의 target Skill prune 구현을 safety, ownership과 regression contract 기준으로 검토하고 remediation evidence를 추적한다."
status: "completed"
tags:
  - "rulesync"
  - "agent-assets"
  - "prune"
  - "safety"
---

> [!NOTE]
> 직접 main-agent review와 remediation loop를 완료했다. projection root 상위 symlink/junction, 불명확한 canonical source의 fail-open 동작, 별도 `skills-lock.json` external Skill ownership 충돌을 수정하고 검증했다. Direct review verdict는 Pass이며, 독립적인 review-lead 검토는 이번 요청 범위에서 수행하지 않았다.

## Overview

| Target | Revision | Scope | Verdict |
| --- | --- | --- | --- |
| `scripts/rulesync.py`와 `tests/scripts/test_tool_wrappers.py` | commit `60ea6bd`, branch `agents/rulesync-auto-prune-script-addition`, PR #223 | `generate` 전후 stale target Skill detection/prune, source/lock parsing, target boundary, adjacent asset ownership | Pass |

## Findings

### F1. Projection root ancestor symlink/junction가 외부 삭제 경계를 우회한다

- **Severity** - Major
- **Location** - `scripts/rulesync.py:174-190`, `scripts/rulesync.py:193-208`
- **Evidence** - root와 direct child의 symlink만 검사한다. `.agents` 자체가 외부 directory를 가리키면 `.agents/skills`는 symlink가 아니면서 directory로 보이고, 외부의 stale Skill이 `shutil.rmtree()` 대상이 된다.
- **Impact** - 사용자가 예상한 repository 내부 target projection 경계를 벗어나 다른 directory의 Skill data를 삭제할 수 있다.
- **Required Change** - projection root의 모든 ancestor에 대해 symlink/junction를 거부하고, prune 직전에 실제 resolved path가 repository 내부의 허용 root인지 다시 검증한다. ancestor link regression test를 추가한다.
- **Resolution** - `_path_has_link_component()`와 `_safe_skill_projection_root()`로 ancestor와 resolved containment를 검사하고, prune 직전에도 같은 검사를 재실행했다. 외부 target root symlink regression test를 추가했다.

### F2. Symlink 또는 접근 불가 canonical source가 빈 목록으로 변환된다

- **Severity** - Major
- **Location** - `scripts/rulesync.py:102-112`, `scripts/rulesync.py:152-164`
- **Evidence** - `.rulesync/skills`가 symlink이거나 directory가 아니면 `_local_skill_names()`가 빈 set을 반환한다. `_declared_skill_names()`는 이를 unknown 상태가 아닌 정상적인 empty source로 union해 prune을 계속한다.
- **Impact** - source를 읽지 못한 상태에서 실제로 유효한 target Skill projection이 stale로 오판되어 삭제될 수 있다.
- **Required Change** - symlink/junction, source child symlink와 읽기 실패를 `unknown`으로 전파해 전체 prune을 건너뛴다. missing source와 unsafe/unreadable source를 구분하고 회귀 테스트를 추가한다.
- **Resolution** - local source와 `SKILL.md`를 `lstat()`으로 확인하고 unsafe, invalid type, read failure를 `None`으로 전파한다. missing source만 empty로 취급하며 root/child symlink와 non-directory regression test를 추가했다.

### F3. Skills CLI-owned external Skill과 Rulesync prune 범위가 충돌한다

- **Severity** - Major
- **Location** - `scripts/rulesync.py:115-149`, `scripts/rulesync.py:193-208`; ownership contract `docs/development/tooling/rulesync.md:21-42`
- **Evidence** - repository contract는 `skills-lock.json`을 Rulesync 밖의 agentskills.io external Skill state로 정의한다. 현재 prune expected-name set은 `rulesync.jsonc`와 `rulesync.lock`만 읽으므로 Skills CLI가 `.agents/skills` 또는 `.claude/skills`에 설치한 이름을 알지 못한다.
- **Impact** - `rulesync.py generate` 직접 실행 또는 후속 Skills CLI 단계 실패 시 별도 관리 Skill을 삭제할 수 있다.
- **Required Change** - `skills-lock.json`의 valid skill names를 안전하게 union하거나, Rulesync-owned projection만 식별할 수 있는 명시적 ownership marker를 사용한다. 별도 lock이 있는 target Skill 보존 테스트를 추가한다.
- **Resolution** - optional `skills-lock.json`의 valid skill names를 expected set에 union하고, symlink·invalid·unreadable lock이면 전체 prune을 건너뛴다. Skills CLI-owned Skill 보존과 invalid lock regression test를 추가했다.

## Validation

| Check | Evidence | Result |
| --- | --- | --- |
| Focused prune tests | `PYTHONPATH=. uv run --no-sync pytest tests/scripts/test_tool_wrappers.py -q` | Pass: 17 passed |
| Scripts suite | `PYTHONPATH=. uv run --no-sync pytest tests/scripts -q -rs` | Pass: 66 passed, 1 skipped (Windows-only npm/Node test) |
| Adjacent asset/routes tests | `PYTHONPATH=. uv run --no-sync pytest tests/scripts/test_agent_assets.py tests/scripts/test_generate_agent_routes.py -q` | Pass: 16 passed |
| Inbox artifact contract | `uv run --no-sync python scripts/validate_inbox_artifacts.py inbox/2026-09-08/17-48-review-rulesync-auto-prune.md` | Pass |
| Static checks | Ruff, format check, `ty check`, `git diff --check` | Pass |
| Independent review-lead handoff | User explicitly requested no subagent invocation | Not performed |

## Remaining Risks

- GitHub PR #223 remote head는 `60ea6bd`이며 제목/본문과 validation evidence가 갱신됐다. PR은 Draft 상태다.
- Windows junction와 permission-denied source behavior는 Linux local environment에서 직접 실행하지 않았다. `Path.is_junction()`과 `lstat()` 경로는 정적 검증만 수행했다.

## Verdict

| Decision | Rationale | Route |
| --- | --- | --- |
| Pass | destructive prune boundary, unknown source fail-closed behavior와 별도 Skill ownership을 보강했고 local validation 및 PR CI check를 통과했다. | PR #223 Draft; human review/approval/merge pending |
