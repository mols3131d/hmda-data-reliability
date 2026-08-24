# Rulesync

Rulesync는 repository-owned **cross-cutting Rule과 Skill**의 canonical authoring source다. 하나의 자연스러운 directory subtree가 소유할 수 있는 context는 가장 가까운 `AGENTS.md`가 직접 소유하며 Rulesync로 옮기지 않는다.

## Authority Boundary

| Context | Canonical source | Rulesync role |
| --- | --- | --- |
| Repository-wide root instruction | `.rulesync/rules/codex-root.md` | root `AGENTS.md` projection |
| Natural directory/subtree context | nearest `AGENTS.md` | none |
| Cross-cutting path/file Rule | `.rulesync/rules/` | author and project |
| Repository-owned Skill | `.rulesync/skills/` | author and project |
| Tool/framework-owned asset | owning tool source | route only |
| Generated vendor/runtime projection | upstream canonical source | consume only |

Rule을 만들기 전에 scope를 먼저 판단한다. `src/foo/**`처럼 한 directory가 자연스럽게 소유하는 규칙은 `src/foo/AGENTS.md`를 사용한다. `**/*.md`, `src/**/*.py`, 여러 독립 tree에 걸친 동일 제약처럼 directory hierarchy만으로 표현하기 어려운 규칙만 Rulesync Rule로 둔다.

다른 tool 또는 framework가 CLI나 자체 lifecycle로 생성·관리하는 asset은 그 tool의 canonical source를 계속 사용한다. OpenSpec처럼 별도 source model을 가진 asset을 Rulesync에 복제하거나 mirror하지 않는다.

## Targets

이 repository의 Rulesync support target은 다음 여섯 개다.

- `claudecode`
- `codexcli`
- `copilot`
- `copilotcli`
- `antigravity-ide`
- `antigravity-cli`

개별 asset의 실제 projection은 canonical asset의 `targets`와 current Rulesync feature compatibility가 결정한다.

## Features

현재 `rulesync.jsonc`는 여섯 target에 `rules`와 `skills` feature를 활성화한다.

| Feature | Canonical source | Generated projection |
| --- | --- | --- |
| cross-cutting `rules` | `.rulesync/rules/` | target-native instruction surfaces 또는 documented CLI routing |
| `skills` | `.rulesync/skills/` | target-native Skill directories |
| directory context | nearest `AGENTS.md` | no Rulesync projection |

Subagents, hooks, MCP, permissions와 commands는 Rulesync 지원 여부만으로 활성화하지 않는다. 기존 repository-owned 자산의 semantics와 target compatibility를 확인해 explicit migration할 때 feature를 추가한다.

## Projection Ownership

Generated projection은 직접 authoring하지 않는다. Rule은 `.rulesync/rules/`, Skill은 `.rulesync/skills/`에서 수정한 뒤 generation한다. Canonical Rule을 제거하거나 target을 변경한 뒤 남은 orphan projection은 해당 source 변경을 확인한 후 명시적으로 정리한다.

Shared output surface에 존재한다는 이유만으로 asset applicability를 다른 target까지 넓히지 않는다. 같은 path를 공유하면서 serialization이나 semantics가 다른 경우에는 direct fan-out 대신 canonical routing을 사용한다.

## CLI Path Rule Boundary

- Claude Code, Copilot, Copilot CLI와 Antigravity IDE는 Rulesync에 남아 있는 cross-cutting Rule의 native scoped projection을 사용한다.
- Codex CLI는 non-root glob Rule을 별도 path-scoped file로 적용하지 않으므로 root `AGENTS.md`의 `Cross-cutting Rule Routing`에서 canonical Rule을 route한다.
- Antigravity CLI는 `.agents/rules/` path를 Antigravity IDE와 공유하지만 current adapter serialization이 다르므로 같은 root routing을 사용한다.
- Directory-scoped `AGENTS.md`는 이 compatibility table에 넣지 않는다.
- Vendor-specific Rule은 해당 target에만 남기며 shared CLI routing에 넣지 않는다.

`.rulesync/rules/codex-root.md`가 shared root `AGENTS.md` body와 필요한 CLI fallback routing을 소유한다.

## Commands

`scripts/rulesync.py`가 repository execution entrypoint다.

```bash
uv run python scripts/rulesync.py preview
uv run python scripts/rulesync.py generate
uv run python scripts/rulesync.py check
uv run python scripts/rulesync.py doctor
uv run python scripts/rulesync.py validate
```

- `preview`: write 없이 generation 결과를 확인한다.
- `generate`: canonical source에서 runtime projection을 갱신한다.
- `check`: generated projection drift를 검사한다.
- `doctor`: strict Rulesync diagnostics를 실행한다.
- `validate`: `doctor` 후 `check`를 순서대로 실행한다.

Agent-driven mutation은 `preview`로 예상 변경을 확인한 뒤 `generate`한다. VS Code의 `Rulesync: *` tasks는 같은 script를 호출하는 optional convenience launcher이며 별도 authority나 공식 entrypoint가 아니다.
