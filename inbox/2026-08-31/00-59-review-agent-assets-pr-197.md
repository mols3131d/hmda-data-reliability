---
type: review
title: "PR 197 Review"
description: "PR 197의 external Skill routing, npm exec lifecycle, agent 실행 경계와 bootstrap 변경을 검토하고 머지 전 필요한 수정 사항을 기록한다."
status: completed
tags:
  - agent-assets
  - tooling
  - github
---

# PR 197 Review

> [!NOTE]
> PR 197의 external Skill routing과 lock 기반 chatbot route는 대체로 일관되고 CI Lite도 통과했다. 다만 bootstrap entrypoint의 `uv run` 전환이 `uv sync --locked`보다 먼저 lock을 갱신할 수 있는 문제와 Windows에서 `cmd.exe`를 통한 사용자 입력 전달 문제가 있어 현재 판정은 **Revise**다. 두 문제를 수정한 뒤 머지하는 것이 적절하다.

## Overview

| Target | Revision | Scope | Verdict |
| --- | --- | --- | --- |
| PR #197 `chore/replace-clarify-skills` | `27c173343eb4ea577f31984c01471a5c128180d4` | external Skill routing, Rulesync/Skills CLI lifecycle, agent 실행 command, bootstrap·hook·VS Code command, 관련 test와 CI | Revise |

## Findings

### F1. Bootstrap entrypoint가 locked dependency 검증 전에 lock을 변경할 수 있다

- **Severity** - Major
- **Location** - `DEVELOPMENT.md`, `.vscode/tasks.json`, `scripts/bootstrap.py`
- **Evidence** - PR은 bootstrap 사용 command를 `python scripts/bootstrap.py ...`에서 `uv run python scripts/bootstrap.py ...`로 변경했다. 그러나 `bootstrap.py` 자체의 dependency 단계는 `uv sync --locked`를 사용해 stale lock을 거부하도록 설계되어 있다. `uv run`은 project command 실행 전에 environment와 lock을 동기화할 수 있으므로, stale `uv.lock`이 있으면 내부 `uv sync --locked`에 도달하기 전에 lock이 갱신될 수 있다.
- **Impact** - `Bootstrap: Session` 또는 `Bootstrap: Update`처럼 정상적인 운영 command가 검토되지 않은 `uv.lock` 변경을 만들 수 있고, 이후 내부 `--locked` 검증은 이미 갱신된 상태를 기준으로 통과할 수 있다. Python dependency lock 변경을 별도 dependency change로 검토한다는 repository 운영 경계가 약해진다.
- **Required Change** - Bootstrap entrypoint는 bare `python scripts/bootstrap.py ...`처럼 `bootstrap.py`가 dependency synchronization의 첫 owner가 되도록 복구하거나, 동등하게 outer `uv run`의 lock mutation을 차단해야 한다.

### F2. Windows agent 실행에서 사용자 입력이 `cmd.exe` metacharacter로 해석될 수 있다

- **Severity** - Major
- **Location** - `scripts/_commands.py::_run_windows_command`, `scripts/agent_assets.py::_run_agent`
- **Evidence** - Windows 경로는 argument list를 `subprocess.list2cmdline()`으로 문자열화한 뒤 `cmd.exe /d /s /c`에 전달한다. 새 `run` subcommand는 사용자가 지정한 `source`, `skill`, `agent`를 그대로 이 경로로 전달한다. `&`, `|` 등 `cmd.exe` metacharacter는 `list2cmdline()`의 일반 argument quoting만으로 shell syntax에서 분리되지 않는다.
- **Impact** - `C:\R&D\skills`처럼 metacharacter가 포함된 정상 local source가 깨질 수 있고, 사용자 입력이 shell syntax로 해석되는 범위가 새 agent 실행 surface에 생긴다.
- **Required Change** - Windows에서 `.cmd` 실행 시 user-controlled argument가 shell syntax로 재해석되지 않도록 실행 방식을 수정하고, metacharacter를 포함한 argument preservation test를 추가한다.

### F3. 삭제된 repository-owned Skill의 maintainer baseline이 남아 있다

- **Severity** - Minor
- **Location** - `docs/agents/skills/prj-clarify-runtime/baseline.md`
- **Evidence** - PR은 repository-owned `prj-clarify-runtime`을 삭제하고 external `mols-clarify-runtime`을 locked dependency로 도입한다. 그러나 maintainer 문서는 여전히 `prj-clarify-runtime`의 유지보수 기준선을 repository-owned Skill 문서 영역에서 소유한다고 설명한다.
- **Impact** - canonical Skill ownership이 upstream으로 이동한 뒤에도 이전 local owner의 baseline이 남아 향후 유지보수에서 source of truth가 이중화되고 drift할 수 있다.
- **Required Change** - 해당 baseline을 삭제하거나, 프로젝트에 남겨야 하는 별도 policy라면 external Skill 자체의 baseline이 아니라 명시적인 project overlay로 ownership을 다시 정의한다.

## Validation

| Check | Evidence | Result |
| --- | --- | --- |
| PR head와 branch state | PR #197 head `27c173343eb4ea577f31984c01471a5c128180d4`, branch `chore/replace-clarify-skills` 확인 | Pass |
| CI Lite | prospective merge에서 `check` job 완료 | Pass |
| Python validation | Ruff, Ruff format, `ty check` 성공 | Pass |
| Chatbot route validation | `python scripts/generate_agent_routes.py --check` 성공 | Pass |
| Lefthook config | `lefthook validate` 성공 | Pass |
| Unit tests | CI Lite에서 `186 passed` | Pass |
| External Skill route consistency | `rulesync.jsonc`의 configured Skills, `rulesync.lock`의 resolved revision과 `.agents/route/skills.jsonl`의 raw source가 같은 locked revision을 사용함 | Pass |
| Actual interactive agent session | target runtime credential과 interactive session을 필요로 하므로 실행하지 않음 | Not Verified |
| Windows runtime reproduction | code path와 quoting semantics를 검토했으나 Windows runner에서 실제 command 실행은 하지 않음 | Not Verified |

## Remaining Risks

- CI Lite는 Linux runner이므로 F2의 Windows-specific behavior를 직접 검증하지 않는다.
- CI의 test pass는 새 interactive `skills use` session 자체의 end-to-end 성공을 증명하지 않는다.
- F1과 F2 수정 후 관련 focused test와 CI Lite를 다시 확인해야 한다.

## Verdict

| Decision | Rationale | Route |
| --- | --- | --- |
| Revise | external Skill routing과 lock 정합성은 양호하지만 bootstrap lock 보호 회귀와 Windows argument handling 문제를 머지 전에 해결해야 한다. | PR #197 |
