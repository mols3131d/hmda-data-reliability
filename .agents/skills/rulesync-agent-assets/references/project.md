# Project Pivot Defaults

Project Pivot는 **Rulesync-first authority**를 사용한다. Repository가 직접 소유하는 agent asset은 Rulesync canonical source를 기본으로 하고, 다른 tool 또는 framework가 자체 CLI와 lifecycle로 관리하는 asset은 그 tool의 canonical source를 유지한다.

## Authority

| Case | Canonical source | Rulesync role |
| --- | --- | --- |
| Rulesync-managed repository asset | `.rulesync/**` | author and generate |
| Repository asset not yet migrated | current declared owner | explicit migration candidate |
| Tool/framework-owned asset | owning tool's canonical source | route only |
| Generated vendor/runtime projection | upstream canonical source | consume only |

- Copilot, Antigravity, Codex 같은 target-native asset이 존재한다는 이유만으로 그것을 기본 source로 선택하지 않는다.
- OpenSpec처럼 다른 tool이 생성·관리하는 artifact를 source centralization을 위해 `.rulesync/`에 import, mirror 또는 재정의하지 않는다.
- 기존 non-Rule asset은 명시적인 migration 전까지 현재 owner를 유지한다. Migration은 selector, behavior와 target compatibility를 보존하는 별도 변경으로 수행한다.

## Current Route

현재 `rulesync.jsonc`는 `rules` feature만 projection한다.

| Feature | Default mode | Source |
| --- | --- | --- |
| `rules` | Canonical fan-out | `.rulesync/rules/` |
| repository-owned non-Rule feature | Canonical fan-out after explicit migration | appropriate `.rulesync/` source |
| tool/framework-owned feature | Outside Rulesync ownership | owning tool source |

Native bridge는 사용자가 one-off compatibility conversion을 명시적으로 요청한 경우에만 사용한다. Project의 기본 source strategy로 사용하지 않는다.

## Commands

Rules fan-out은 repository entrypoint를 사용한다.

```bash
uv run python scripts/rulesync.py preview
uv run python scripts/rulesync.py generate
uv run python scripts/rulesync.py validate
```

Active development 동안 이 entrypoint는 `rulesync@latest`를 사용한다.

## Project Boundary

- Rulesync-managed asset은 canonical `.rulesync/**` source에서 수정한다.
- Generated target asset을 source로 재해석하거나 직접 수정하지 않는다.
- 다른 tool 또는 framework가 소유하는 asset은 그 tool의 generation과 lifecycle contract를 따른다.
- Rulesync migration은 기존 owner를 암묵적으로 바꾸지 않는다. Migration 자체가 요청되고 preview와 validation으로 semantics를 확인한 경우에만 authority를 이동한다.
- broad `--features "*"`보다 실제 source와 migration scope가 확정된 feature만 다룬다.
