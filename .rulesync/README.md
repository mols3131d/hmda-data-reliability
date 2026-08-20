# Rulesync

`.rulesync/rules/`는 repository-local Rule의 canonical source다. Generated vendor files는 runtime surface이며 직접 편집하지 않는다.

## Targets

`rulesync.jsonc`는 Rules만 다음 target으로 생성한다.

- `antigravity-ide`
- `copilot`
- `codexcli`

Skills, subagents, hooks, MCP, permissions는 이번 workspace에서 Rulesync가 소유하지 않는다.

## Codex Boundary

Rulesync 16.5.0의 `codexcli` Rules adapter는 non-root glob Rule을 별도 path-scoped 파일로 적용하지 않고 root `AGENTS.md`로 fold한다. 이 저장소는 path scope 손실을 피하기 위해 다음 구조를 사용한다.

- `.rulesync/rules/codex-root.md`만 `codexcli` target으로 생성해 root `AGENTS.md`를 소유한다.
- path-scoped canonical Rule은 기존 target ownership을 유지한다.
- generated `AGENTS.md`의 `Path Rules` table이 Codex에게 matching canonical Rule을 읽도록 지시한다.

따라서 path-scoped Rule의 `targets`에 `codexcli`를 직접 추가하지 않는다. Upstream Codex/Rulesync가 glob-scoped Rules를 native하게 지원할 때 이 boundary를 다시 검토한다.

## Commands

```bash
rulesync generate --dry-run --targets antigravity-ide,copilot,codexcli --features rules
rulesync generate --targets antigravity-ide,copilot,codexcli --features rules
rulesync generate --check --targets antigravity-ide,copilot,codexcli --features rules
```

현재 migration 기준 Rulesync 버전은 `16.5.0`이다.
