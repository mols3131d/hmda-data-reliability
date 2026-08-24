# Project Defaults

이 repository는 **scope-first instruction ownership**을 사용한다. 하나의 자연스러운 directory subtree가 소유할 수 있는 context는 가장 가까운 `AGENTS.md`가 canonical source이며, cross-cutting path/file Rule과 Skill은 Rulesync가 canonical source다.

## Authority

| Case | Canonical source | Rulesync role |
| --- | --- | --- |
| Repository-wide root instruction | `.rulesync/rules/codex-root.md` | root `AGENTS.md` projection |
| Natural directory/subtree context | nearest `AGENTS.md` | do not migrate |
| Cross-cutting path/file Rule | `.rulesync/rules/` | author and generate |
| Repository-owned Skill | `.rulesync/skills/` | author and generate |
| Tool/framework-owned asset | owning tool source | route only |
| Generated vendor/runtime projection | upstream canonical source | consume only |

Rulesync migration은 source centralization 자체가 목적이 아니다. `src/foo/**`처럼 한 directory가 자연스럽게 소유하는 instruction은 `src/foo/AGENTS.md`를 유지하거나 그곳으로 옮긴다. File extension, 공통 하위 pattern, 서로 떨어진 tree에 걸친 동일 제약처럼 directory hierarchy만으로 표현하기 어려운 scope만 Rule로 둔다.

## Targets

Project-level support target은 `claudecode`, `codexcli`, `copilot`, `copilotcli`, `antigravity-ide`, `antigravity-cli`다. 개별 Rulesync asset은 canonical frontmatter의 `targets`로 applicability를 더 좁힐 수 있다.

## Current Route

현재 `rulesync.jsonc`는 여섯 target에 `rules`와 `skills`를 활성화한다.

- Directory/subtree guidance는 `AGENTS.md` hierarchy가 소유한다.
- Cross-cutting generic Rule은 Claude Code, Copilot, Copilot CLI와 Antigravity IDE에 native projection한다.
- Codex CLI와 Antigravity CLI에서 native path selection이 부족한 cross-cutting Rule만 root `AGENTS.md`의 fallback table로 route한다.
- Vendor-specific Rule은 shared fallback routing에 넣지 않는다.
- Generated Skill projection은 canonical source가 아니며 직접 authoring하지 않는다.

## Commands

```bash
uv run python scripts/rulesync.py preview
uv run python scripts/rulesync.py generate
uv run python scripts/rulesync.py validate
```

Active development 동안 이 entrypoint는 `rulesync@latest`를 사용한다.

## Project Boundary

- Rule을 만들거나 migration하기 전에 nearest `AGENTS.md`가 scope를 더 자연스럽게 소유하는지 먼저 확인한다.
- Directory context를 Rulesync fan-out 편의를 위해 glob Rule로 평탄화하지 않는다.
- Rulesync-managed asset은 canonical `.rulesync/**` source에서 수정한다.
- Generated target asset을 source로 재해석하거나 직접 authoring하지 않는다. Canonical source 제거 뒤의 orphan projection cleanup은 별도 mutation으로 수행할 수 있다.
- 다른 tool 또는 framework가 소유하는 asset은 그 tool의 generation과 lifecycle contract를 따른다.
- Shared output path에 target별 serialization이나 semantics 차이가 있으면 target 수를 맞추기 위해 같은 file을 강제로 fan-out하지 않는다.
