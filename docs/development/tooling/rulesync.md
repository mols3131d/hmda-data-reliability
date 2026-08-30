---
title: "Rulesync"
description: "Rulesync를 Agent Asset 관리의 주 실행 경로로 사용하고 Skills CLI를 Rulesync 밖의 agentskills.io 호환 external Skill 보조 경로로 연결하는 repository-specific tooling guide입니다."
categories:
  - ai-engineering
  - software-engineering
tags:
  - agent-skills
  - rulesync
  - tooling
---

# Rulesync

Agent Asset의 **management policy는 [AI Agent](../ai-agent/README.md)가 소유하고, 이 문서는 그 정책을 실행하는 repository entrypoint를 설명한다.** Project Rule/Skill과 Rulesync-managed external Rule/Skill은 Rulesync를 사용하고, Rulesync로 관리하지 않는 [agentskills.io 호환](https://agentskills.io/specification) external Skill만 Skills CLI를 보조 경로로 사용한다.

Rulesync와 Skills CLI 자체의 일반 사용법은 [Rulesync Configuration](https://rulesync.dyoshikawa.com/guide/configuration), [Rulesync CLI reference](https://rulesync.dyoshikawa.com/reference/cli-commands.html)와 [Skills CLI 공식 repository](https://github.com/vercel-labs/skills)를 따른다.

## Repository Integration

| Surface | Responsibility |
| --- | --- |
| [`rulesync.jsonc`](../../../rulesync.jsonc) | Rulesync target과 external source 선언 |
| [`rulesync.lock`](../../../rulesync.lock) | Rulesync-managed external source의 resolved revision과 integrity lock |
| `.rulesync/**` | project Rule/Skill과 Rulesync-managed source |
| [`scripts/rulesync.py`](../../../scripts/rulesync.py) | Rulesync source restore/update, projection generation/check와 compatibility bridge |
| [`skills-lock.json`](../../../skills-lock.json) | Rulesync 밖의 agentskills.io 호환 external Skill에 대한 Skills CLI project lock state |
| [`scripts/agent_assets.py`](../../../scripts/agent_assets.py) | Rulesync를 먼저 실행하고 Skills CLI와 route generation을 이어서 수행하는 high-level entrypoint |
| `.agents/route/**` | source에서 생성된 derived discovery index |

`rulesync.jsonc`가 source intent를 선언하고 `rulesync.lock`이 resolved external source state를 기록한다. Lock과 generated projection은 normal editing surface로 다루지 않고 repository script를 통해 갱신한다.

## Common Entrypoints

Agent Asset 전체를 현재 lock 상태로 복원하거나 external source를 갱신할 때는 `scripts/agent_assets.py`를 사용한다.

```bash
uv run --no-sync python scripts/agent_assets.py install
uv run --no-sync python scripts/agent_assets.py update
```

`install`은 locked state 복원 경로이고 `update`는 managed external source를 새 revision으로 갱신하는 경로다. 이 entrypoint는 Rulesync를 먼저 실행한 뒤 `skills-lock.json`이 있으면 Skills CLI 보조 단계를 수행하고 마지막에 route index를 갱신한다.

Rulesync projection 자체를 확인하거나 검증해야 할 때는 `scripts/rulesync.py`를 직접 사용한다.

| Action | Purpose |
| --- | --- |
| `preview` | generated projection 변경을 쓰지 않고 확인 |
| `generate` | current source에서 projection 생성 |
| `check` | projection drift 확인 |
| `doctor` | Rulesync strict diagnostics 실행 |
| `validate` | locked source restore, projection drift, doctor와 compatibility bridge를 함께 검증 |

```bash
uv run --no-sync python scripts/rulesync.py preview
uv run --no-sync python scripts/rulesync.py validate
```

Rulesync 밖의 특정 agentskills.io 호환 external Skill을 설치하지 않고 supported agent에서 직접 실행할 때만 Skills CLI 기반 `run` entrypoint를 사용한다.

```bash
uv run python scripts/agent_assets.py run <source> --skill <name> --agent <id>
```

Repository wrapper가 Rulesync와 Skills CLI의 package invocation을 소유하므로 global CLI installation이나 직접 binary path를 전제로 하지 않는다.

## Update Boundary

일반 작업 시작에는 [Bootstrap](bootstrap.md)의 `session`을 사용해 현재 lock 상태를 복원한다. External source를 실제로 갱신하려는 경우에만 `bootstrap.py update` 또는 `agent_assets.py update`를 사용한다.

`skills-lock.json`이 없으면 repository script는 Skills CLI 단계를 건너뛴다. Skills CLI는 Rulesync의 대체 관리 경로가 아니라 **Rulesync로 관리하지 않는 agentskills.io 호환 external Skill만 보완하는 경로**다.
