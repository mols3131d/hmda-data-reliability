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
| `rules` | `.rulesync/rules/` | target-native instruction surfaces 또는 documented canonical routing |
| `skills` | `.rulesync/skills/` | target-native Skill directories |

Subagents, hooks, MCP, permissions와 commands는 Rulesync 지원 여부만으로 활성화하지 않는다. 기존 repository-owned 자산의 semantics와 target compatibility를 확인해 explicit migration할 때 feature를 추가한다.

## Version Policy

Active development 동안 Rulesync는 latest를 우선한다. 특정 버전을 repository contract로 고정하지 않고, Rulesync 변경 후 current latest로 validation을 실행해 compatibility를 확인한다.

프로젝트가 안정화되어 reproducible snapshot이 필요해질 때 검증된 버전 고정을 별도로 결정한다.

## Projection Ownership

Generated projection은 직접 수정하지 않는다. Rule은 `.rulesync/rules/`, Skill은 `.rulesync/skills/`에서 수정한 뒤 generation한다.

`delete: true`는 사용하지 않는다. Copilot과 Copilot CLI처럼 같은 output surface를 공유하는 target에서 한 target 전용 asset을 다른 target generation이 orphan으로 해석할 수 있기 때문이다. Projection drift는 `generate --check`로 검증하고, 실제 orphan cleanup은 canonical target 변경을 확인한 뒤 명시적으로 수행한다.

Shared surface에 존재한다는 이유만으로 asset applicability를 다른 target까지 넓히지 않는다. 같은 path를 공유하면서 serialization이나 semantics가 다른 경우에는 direct fan-out 대신 아래처럼 canonical routing을 사용한다.

## CLI Path Rule Boundary

Path-scoped generic Rule은 target capability에 따라 두 방식으로 적용한다.

- Claude Code, Copilot, Copilot CLI와 Antigravity IDE는 current adapter가 제공하는 native scoped Rule projection을 사용한다.
- Codex CLI는 non-root glob Rule을 별도 path-scoped file로 적용하지 않으므로 root `AGENTS.md`의 `Path Rules` table에서 canonical Rule을 route한다.
- Antigravity CLI는 `.agents/rules/` path를 Antigravity IDE와 공유하지만 current Rulesync adapters의 non-root serialization이 다르다. 같은 file을 서로 다른 형식으로 덮어쓰지 않도록 root `AGENTS.md`의 동일한 `Path Rules` routing을 사용한다.
- Vendor-specific Rule은 해당 target에만 남기며 shared CLI routing table에 넣지 않는다. 예를 들어 VS Code Mermaid integration Rule은 Copilot-only다.

`.rulesync/rules/codex-root.md`가 Codex CLI와 Antigravity CLI의 canonical path routing, 그리고 Antigravity IDE와 공유하는 root `AGENTS.md` body를 소유한다.

Rulesync는 root Rule이 없는 enabled target에 advisory를 출력할 수 있다. Claude Code와 Copilot 계열은 현재 scoped Rule과 Skill projection만 사용하므로 root Rule 부재 자체를 validation failure로 간주하지 않는다. Root-wide behavior가 실제로 필요해지면 별도 canonical root Rule을 추가한다.

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
