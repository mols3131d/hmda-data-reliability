# Rulesync

Rulesync는 **repository-owned Agent Asset의 기본 canonical authoring source**다. Rulesync가 생성한 vendor/runtime file은 derived projection이며 직접 편집하거나 독립적인 authority로 재해석하지 않는다.

## Authority Boundary

- Repository가 직접 소유하고 Rulesync가 필요한 semantics를 표현할 수 있는 Agent Asset은 `.rulesync/`를 canonical source로 사용한다.
- 다른 tool 또는 framework가 CLI나 자체 lifecycle로 생성·관리하는 asset은 그 tool의 canonical source가 계속 소유한다. OpenSpec처럼 별도 source model을 가진 asset을 Rulesync에 복제하거나 mirror하지 않는다.
- Rulesync는 external tool-owned asset을 필요한 agent context로 route할 수 있지만 그 semantics, generation과 lifecycle을 재정의하지 않는다.
- 아직 Rulesync로 명시적으로 migration하지 않은 repository-owned asset은 현재 owner를 유지하되 migration candidate로 취급한다.

## Targets

이 repository의 Rulesync support target은 다음 여섯 개다.

- `claudecode`
- `codexcli`
- `copilot`
- `copilotcli`
- `antigravity-ide`
- `antigravity-cli`

이 target set은 reusable Agent Asset 관리 repository의 Rulesync support ceiling과 맞춘다. 개별 asset의 실제 projection은 해당 canonical asset의 `targets`와 current Rulesync feature compatibility가 결정한다.

## Features

현재 `rulesync.jsonc`는 여섯 target에 `rules`와 `skills` feature를 활성화한다.

| Feature | Canonical source | Generated projection |
| --- | --- | --- |
| `rules` | `.rulesync/rules/` | target-native instruction surfaces |
| `skills` | `.rulesync/skills/` | target-native Skill directories |

Subagents, hooks, MCP, permissions와 commands는 Rulesync 지원 여부만으로 활성화하지 않는다. 기존 repository-owned 자산의 semantics와 target compatibility를 확인해 explicit migration할 때 feature를 추가한다.

## Version Policy

Active development 동안 Rulesync는 latest를 우선한다. 특정 버전을 repository contract로 고정하지 않고, Rulesync 변경 후 current latest로 validation을 실행해 compatibility를 확인한다.

프로젝트가 안정화되어 reproducible snapshot이 필요해질 때 검증된 버전 고정을 별도로 결정한다.

## Projection Ownership

`delete: true`로 generation 대상 directory의 orphan projection을 제거한다. Canonical asset을 삭제하거나 target에서 제외한 뒤 예전 generated asset이 runtime에 남는 drift를 허용하지 않는다.

Generated projection은 직접 수정하지 않는다. Rule은 `.rulesync/rules/`, Skill은 `.rulesync/skills/`에서 수정한 뒤 generation한다.

Root `AGENTS.md`는 Antigravity IDE/CLI와 Codex CLI가 공유하는 runtime surface다. `.rulesync/rules/codex-root.md`의 target applicability와 generated output이 같은 root body를 공유하는 경우 target order에 따라 orphan cleanup 결과가 달라지지 않게 유지한다.

## Codex Boundary

현재 Rulesync의 `codexcli` Rules adapter는 non-root glob Rule을 별도 path-scoped 파일로 적용하지 않고 root `AGENTS.md`로 fold한다. 이 저장소는 path scope 손실을 피하기 위해 다음 구조를 사용한다.

- `.rulesync/rules/codex-root.md`가 Codex CLI의 root `AGENTS.md`와 canonical path routing을 소유한다.
- path-scoped canonical Rule은 각 target의 native capability와 asset `targets`를 따른다.
- generated `AGENTS.md`의 `Path Rules` table은 Codex CLI에서 matching canonical Rule을 읽도록 지시한다. Native path-scoped Rule을 지원하는 target은 generated target surface를 사용한다.

따라서 path-scoped Rule의 `targets`는 target capability와 필요한 behavior를 기준으로 관리한다. Upstream adapter behavior가 바뀌면 이 boundary를 다시 검토한다.

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
- `generate`: canonical source에서 runtime projection을 갱신한다.
- `check`: generated projection drift를 검사한다.
- `doctor`: strict Rulesync diagnostics를 실행한다.
- `validate`: `doctor` 후 `check`를 순서대로 실행한다.

Agent-driven mutation은 `preview`로 예상 변경을 확인한 뒤 `generate`한다. VS Code의 `Rulesync: *` tasks는 같은 script를 호출하는 optional convenience launcher이며 별도 authority나 공식 entrypoint가 아니다.
