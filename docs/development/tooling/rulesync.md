---
title: "Rulesync"
description: "Rulesync를 Agent Asset 관리의 주 경로로 사용하고 Skills CLI를 external standard Skill의 보조 경로로 연결하는 repository-specific tooling guide입니다."
categories:
  - ai-engineering
  - software-engineering
tags:
  - agent-skills
  - rulesync
  - tooling
---

# Rulesync

이 repository의 **Agent Asset 관리는 Rulesync가 주 경로**다. Repository에서 직접 관리하는 Rule/Skill과 Rulesync source로 가져오는 external asset은 Rulesync가 소유하고, target별 projection도 Rulesync에서 생성한다.

**Skills CLI는 보조 경로**다. Rulesync asset으로 다시 포장하지 않는 external standard Agent Skill을 lock·복원하거나 필요할 때 supported agent에서 직접 실행하는 용도로만 사용한다.

Rulesync와 Skills CLI 자체의 일반 사용법은 각각 [Rulesync 공식 문서](https://rulesync.dyoshikawa.com/)와 [Skills CLI 공식 repository](https://github.com/vercel-labs/skills)를 따른다. 이 문서는 이 repository에서 두 도구가 맡는 역할과 실행 경로만 설명한다.

Agent instruction surface와 asset ownership을 선택하는 정책은 [AI Agent](../ai-agent/README.md)가 소유한다.

## Management Model

| Asset | Primary path |
| --- | --- |
| repository에서 직접 작성·관리하는 Rule 또는 Skill | Rulesync |
| external Rulesync Rule 또는 Skill | Rulesync |
| external standard Agent Skill | Skills CLI (auxiliary) |

Skills CLI로 가져오는 external standard Skill을 Rulesync asset으로 다시 포장해 중복 source를 만들지 않는다. 반대로 Rulesync가 이미 소유하는 asset을 Skills CLI에서 별도로 관리하지 않는다.

## Repository Integration

| Surface | Responsibility |
| --- | --- |
| [`rulesync.jsonc`](../../../rulesync.jsonc) | Rulesync target과 external source 선언 |
| `.rulesync/**` | repository-managed Rule/Skill source |
| [`scripts/rulesync.py`](../../../scripts/rulesync.py) | Rulesync source sync, projection generation/check와 compatibility bridge |
| `skills-lock.json` | Skills CLI가 관리하는 external standard Agent Skill의 project lock state |
| [`scripts/agent_assets.py`](../../../scripts/agent_assets.py) | Rulesync를 먼저 실행하고 Skills CLI와 route generation을 이어서 수행하는 repository entrypoint |
| `.agents/route/**` | source에서 생성된 derived discovery index |

Generated projection과 route index는 canonical source가 아니다. 변경이 필요하면 owning Rule/Skill source 또는 configuration을 수정한 뒤 repository script로 다시 생성한다.

## Common Commands

Agent Asset 전체를 복원하거나 갱신할 때는 `scripts/agent_assets.py`를 사용한다.

```bash
uv run --no-sync python scripts/agent_assets.py install
uv run --no-sync python scripts/agent_assets.py update
```

이 entrypoint는 Rulesync를 주 경로로 실행한 뒤, `skills-lock.json`이 있으면 Skills CLI 보조 단계를 수행하고 마지막에 route index를 갱신한다.

특정 external standard Skill을 설치하지 않고 supported agent에서 직접 실행할 때만 Skills CLI 기반 `run` entrypoint를 사용한다.

```bash
uv run python scripts/agent_assets.py run <source> --skill <name> --agent <id>
```

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

Rulesync target option, source syntax와 CLI 세부사항은 repository 문서에 복제하지 않고 [공식 문서](https://rulesync.dyoshikawa.com/)를 확인한다.

## Update Boundary

일반 작업 시작에는 [Bootstrap](bootstrap.md)의 `session`을 사용해 현재 lock 상태를 복원한다. External source를 실제로 갱신하려는 경우에만 `bootstrap.py update` 또는 `agent_assets.py update`를 사용한다.

`skills-lock.json`이 없으면 repository script는 Skills CLI 단계를 건너뛴다. Skills CLI는 Rulesync의 대체 관리 경로가 아니라 Rulesync가 직접 소유하지 않는 external standard Skill을 보완하는 경로다.
