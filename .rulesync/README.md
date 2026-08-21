# Rulesync

`.rulesync/rules/`는 repository-local Rule의 canonical source다. Generated vendor files는 runtime surface이며 직접 편집하지 않는다.

## Targets

`rulesync.jsonc`는 Rules만 다음 target으로 생성한다.

- `antigravity-ide`
- `copilot`
- `codexcli`

Skills, subagents, hooks, MCP, permissions는 이번 workspace에서 Rulesync가 소유하지 않는다.

## Version Policy

Active development 동안 Rulesync는 latest를 우선한다. 특정 버전을 repository contract로 고정하지 않고, Rulesync 변경 후 current latest로 validation을 실행해 compatibility를 확인한다.

프로젝트가 안정화되어 reproducible snapshot이 필요해질 때 검증된 버전 고정을 별도로 결정한다.

## Projection Ownership

`delete: true`로 generation 대상 directory의 orphan projection을 제거한다. Canonical Rule을 삭제하거나 target에서 제외한 뒤 예전 generated Rule이 runtime에 남는 drift를 허용하지 않는다.

Root `AGENTS.md`는 Antigravity IDE와 Codex CLI가 공유하는 runtime surface다. `.rulesync/rules/codex-root.md`가 두 target 모두에 같은 root body를 생성해 target order에 따라 orphan cleanup 결과가 달라지지 않게 한다.

## Codex Boundary

현재 Rulesync의 `codexcli` Rules adapter는 non-root glob Rule을 별도 path-scoped 파일로 적용하지 않고 root `AGENTS.md`로 fold한다. 이 저장소는 path scope 손실을 피하기 위해 다음 구조를 사용한다.

- `.rulesync/rules/codex-root.md`가 Antigravity IDE와 Codex CLI의 shared root `AGENTS.md`를 소유한다.
- path-scoped canonical Rule은 기존 target ownership을 유지한다.
- generated `AGENTS.md`의 `Path Rules` table은 Codex CLI에서 matching canonical Rule을 읽도록 지시한다. Antigravity IDE는 native `.agents/rules/` projection을 사용한다.

따라서 path-scoped Rule의 `targets`에 `codexcli`를 직접 추가하지 않는다. Upstream Codex/Rulesync가 glob-scoped Rules를 native하게 지원할 때 이 boundary를 다시 검토한다.

## Commands

`scripts/rulesync.py`가 repository execution entrypoint다. Script는 `rulesync.jsonc`의 target/features 설정을 재정의하지 않고 `npx --yes rulesync@latest`를 호출한다.

```bash
uv run python scripts/rulesync.py preview
uv run python scripts/rulesync.py generate
uv run python scripts/rulesync.py check
uv run python scripts/rulesync.py doctor
uv run python scripts/rulesync.py validate
```

- `preview`: write 없이 generation 결과를 확인한다.
- `generate`: canonical Rules에서 runtime projection을 갱신한다.
- `check`: generated projection drift를 검사한다.
- `doctor`: strict Rulesync diagnostics를 실행한다.
- `validate`: `doctor` 후 `check`를 순서대로 실행한다.

Agent-driven mutation은 `preview`로 예상 변경을 확인한 뒤 `generate`한다. VS Code의 `Rulesync: *` tasks는 같은 script를 호출하는 optional convenience launcher이며 별도 authority나 공식 entrypoint가 아니다.
