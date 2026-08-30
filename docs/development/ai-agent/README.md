---
title: "AI Agent"
description: "Repository의 agent instruction surface 선택과 Rule/Skill asset management guidance를 모으는 docs/development/ai-agent directory의 entrypoint입니다."
categories:
  - ai-engineering
  - software-engineering
tags:
  - rulesync
---

# AI Agent

이 directory는 repository에서 **instruction surface 선택과 agent asset 관리 정책**을 소유한다. 세부 Rule/Skill 작성법은 각 문서가 소유한다.

## Surface Selection

| Applicability | Surface |
| --- | --- |
| repository 전체 | root `/AGENTS.md` |
| 하나의 directory subtree | nearest `AGENTS.md` |
| path, glob, file type, extension 같은 구조적 scope | [Rule](rule.md) |
| task intent와 semantic relevance | [Skill](skill.md) |

Rule과 Skill은 내용이 아니라 **적용 방식**으로 구분한다. Skill도 정책, 제약, 판단 기준 같은 instruction을 담을 수 있다.

같은 지침을 여러 surface에 복제하지 않는다. 하나의 subtree가 자연스럽게 소유할 수 있으면 `AGENTS.md`를 사용하고, cross-cutting structural scope는 Rule, task-selected context는 Skill을 사용한다.

## Asset Management

AI agent asset 관리는 **Rulesync-first**다.

| Asset | Management |
| --- | --- |
| project Rule 또는 Skill | Rulesync source |
| Rulesync로 관리하는 external Rule 또는 Skill | Rulesync |
| Rulesync로 관리하지 않는 agentskills.io-compatible external Skill | Skills CLI + `skills-lock.json` |

Project asset과 Rulesync-managed external asset은 Rulesync가 소유한다. Skills CLI는 Rulesync에서 관리하지 않는 agentskills.io-compatible external Skill을 보조적으로 관리한다.

Skills CLI로 가져온 external Skill을 Rulesync asset으로 다시 포장해 중복 source를 만들지 않는다. Generated projection과 routing index는 derived surface이며 canonical source가 아니다.

외부 Skill을 특정 supported agent로 실행해야 하면 `uv run python scripts/agent_assets.py run <source> --skill <name> --agent <id>`를 사용한다. 이 경로는 Skills CLI가 제공하는 interactive `use` 실행만 시작하며, repository의 `.github/agents/*.agent.md` 정의를 임의로 자동 실행하거나 권한을 확장하지 않는다.

## Boundary

이 문서는 **surface 선택과 asset management policy**만 소유한다. Rule-specific 기준은 [Rule](rule.md), Skill-specific 기준은 [Skill](skill.md)이 소유한다. Rulesync generation/projection, Skills CLI 동작과 target별 runtime semantics는 해당 tool 또는 runtime의 owning source를 따른다.
