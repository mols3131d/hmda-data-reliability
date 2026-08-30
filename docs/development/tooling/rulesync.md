---
title: "Rulesync and Skills CLI"
description: "이 repository의 Agent Asset source를 Rulesync와 Skills CLI로 복원·갱신하고 projection을 검증하는 실행 경로를 설명합니다."
categories:
  - ai-engineering
  - software-engineering
tags:
  - agent-skills
  - rulesync
  - tooling
---

# Rulesync and Skills CLI

Rulesync와 Skills CLI의 일반 사용법은 각각 [Rulesync 공식 문서](https://rulesync.dyoshikawa.com/)와 [Skills CLI 공식 repository](https://github.com/vercel-labs/skills)를 따른다. 이 문서는 이 repository가 두 tool을 어떻게 연결하는지만 설명한다.

Agent instruction surface와 어떤 asset을 Rulesync 또는 Skills CLI로 관리할지에 대한 정책은 [AI Agent](../ai-agent/README.md)가 소유한다.

## Repository Integration

| Surface | Responsibility |
| --- | --- |
| [`rulesync.jsonc`](../../../rulesync.jsonc) | target과 external Rulesync source 선언 |
| `.rulesync/**` | repository-managed Rule/Skill source |
| `skills-lock.json` | external standard Agent Skill의 project lock state |
| [`scripts/rulesync.py`](../../../scripts/rulesync.py) | Rulesync source sync, projection generation/check와 compatibility bridge |
| [`scripts/agent_assets.py`](../../../scripts/agent_assets.py) | Rulesync + Skills CLI + route generation을 묶는 repository entrypoint |
| `.agents/route/**` | source에서 생성된 derived discovery index |

Generated projection과 route index는 canonical source가 아니다. 변경이 필요하면 owning Rule/Skill source 또는 configuration을 수정한 뒤 repository script로 다시 생성한다.

## Common Commands

Agent Asset 전체를 다룰 때는 `scripts/agent_assets.py`를 우선한다.

```bash
uv run --no-sync python scripts/agent_assets.py install
uv run --no-sync python scripts/agent_assets.py update
```

특정 external Skill을 설치하지 않고 supported agent에서 실행할 때는 다음 entrypoint를 사용한다.

```bash
uv run python scripts/agent_assets.py run <source> --skill <name> --agent <id>
```

Rulesync projection 자체를 확인하거나 검증해야 할 때만 `scripts/rulesync.py`를 직접 사용한다.

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

Rulesync 자체의 target option, source syntax와 CLI 세부사항은 repository 문서에 복제하지 않고 [공식 문서](https://rulesync.dyoshikawa.com/)를 확인한다.

## Update Boundary

일반 작업 시작에는 [Bootstrap](bootstrap.md)의 `session`을 사용해 현재 lock 상태를 복원한다. External source를 실제로 갱신하려는 경우에만 `bootstrap.py update` 또는 `agent_assets.py update`를 사용한다.

`skills-lock.json`이 없으면 repository script는 Skills CLI installation step을 건너뛴다. Rulesync와 Skills CLI 중 어느 쪽이 asset을 소유하는지는 이 문서가 아니라 [AI Agent asset management policy](../ai-agent/README.md#asset-management)를 따른다.
