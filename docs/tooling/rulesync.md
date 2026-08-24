# Rulesync

Rulesync는 repository-owned Agent Asset 중 Rulesync가 표현할 수 있는 자산의 **canonical authoring surface**다. 이 문서는 이 repository에서 Rulesync 자산을 수정하고 projection을 생성·검증하는 방법만 소유한다.

## Ownership

| Surface | Role |
| --- | --- |
| `.rulesync/rules/` | canonical Rule source |
| `.rulesync/skills/` | canonical Skill source |
| `rulesync.jsonc` | project-level targets와 enabled features |
| target-native generated files | derived projection |
| `.agents/route/*.jsonl` | chatbot discovery용 derived metadata |

다른 tool이나 framework가 자체 CLI와 lifecycle로 소유하는 자산은 그 source를 유지한다. OpenSpec처럼 별도 source model을 가진 자산을 Rulesync에 복제하거나 재정의하지 않는다.

Generated projection은 독립적인 authority가 아니며 직접 authoring하지 않는다. 변경은 canonical source에서 시작한다.

## Targets And Features

현재 project-level support target은 다음 여섯 개다.

- `claudecode`
- `codexcli`
- `copilot`
- `copilotcli`
- `antigravity-ide`
- `antigravity-cli`

`rulesync.jsonc`는 현재 `rules`와 `skills`만 활성화한다. Subagents, hooks, MCP, permissions, checks, commands 등은 Rulesync가 지원한다는 이유만으로 추가하지 않는다. 실제 repository-owned 자산과 target compatibility가 필요한 경우에만 별도 migration으로 활성화한다.

개별 asset의 applicability는 canonical frontmatter의 `targets`와 current Rulesync compatibility가 결정한다. Shared output surface를 사용한다는 이유로 target 범위를 넓히지 않는다.

## Workflow

Rulesync 변경은 다음 순서를 기본으로 한다.

1. `.rulesync/**`의 owning source를 수정한다.
2. `preview`로 예상 projection을 확인한다.
3. 요청 범위가 맞으면 `generate`한다.
4. Skill projection이 바뀌면 chatbot route index를 다시 생성한다.
5. `validate`로 Rulesync diagnostics와 projection drift를 확인한다.

```bash
uv run python scripts/rulesync.py preview
uv run python scripts/rulesync.py generate
uv run python scripts/generate_agent_routes.py
uv run python scripts/rulesync.py validate
uv run python scripts/generate_agent_routes.py --check
```

`scripts/rulesync.py`는 `rulesync.jsonc`의 target/features를 재정의하지 않고 `npx --yes rulesync@latest`를 호출한다. 필요하면 개별 `check`와 `doctor`도 실행할 수 있다.

```bash
uv run python scripts/rulesync.py check
uv run python scripts/rulesync.py doctor
```

## Removing Or Retargeting Assets

이 repository는 `delete: true`를 사용하지 않는다. Copilot과 Copilot CLI처럼 같은 output surface를 공유하는 target 사이에서 잘못된 orphan cleanup이 발생할 수 있기 때문이다.

Canonical asset을 삭제하거나 target 범위를 줄인 경우에는 generation 결과와 canonical target 변경을 먼저 확인한 뒤 stale generated projection을 **명시적으로 정리**한다. Skill projection을 정리한 뒤에는 `.agents/route/skills.jsonl`도 `scripts/generate_agent_routes.py`로 갱신한다.

## CLI Path Rules

Path-scoped generic Rule은 target capability에 따라 적용 방식이 다르다.

- Claude Code, Copilot, Copilot CLI, Antigravity IDE는 Rulesync의 native scoped projection을 사용한다.
- Codex CLI는 non-root glob Rule을 native path-scoped file로 적용하지 않으므로 root `AGENTS.md`의 `Path Rules` table에서 canonical Rule을 route한다.
- Antigravity CLI는 Antigravity IDE와 `.agents/rules/` path를 공유하면서 serialization이 달라, root `AGENTS.md`의 같은 routing을 사용한다.
- Vendor-specific Rule은 해당 target에만 두고 shared CLI routing에 넣지 않는다.

`.rulesync/rules/codex-root.md`가 이 root routing과 generated `AGENTS.md` body를 소유한다.

## Version Policy

Active development 동안 repository wrapper는 `rulesync@latest`를 사용하고 current version으로 compatibility를 검증한다. Reproducible snapshot이 필요해지는 시점에 검증된 버전 고정을 별도로 결정한다.

## Boundaries

- Generated target file을 source로 재해석하거나 직접 authoring하지 않는다.
- Project-level targets나 enabled features를 편의상 넓히지 않는다.
- 다른 tool/framework가 소유하는 자산의 semantics와 lifecycle을 Rulesync가 소유한다고 가정하지 않는다.
- Preview, diagnostics, projection check를 실행하지 않았다면 성공했다고 기록하지 않는다.
