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
| repository에서 직접 작성·관리하는 Rule 또는 Skill | Rulesync source |
| external Rulesync Rule 또는 Skill | Rulesync |
| external standard Agent Skill | Skills CLI + `skills-lock.json` |

External standard Skill을 Rulesync asset으로 다시 포장해 중복 source를 만들지 않는다. Generated projection과 routing index는 derived surface이며 canonical source가 아니다.

## Boundary

이 문서는 **surface 선택과 asset management policy**만 소유한다. Rule-specific 기준은 [Rule](rule.md), Skill-specific 기준은 [Skill](skill.md)이 소유한다. Rulesync generation/projection, Skills CLI 동작과 target별 runtime semantics는 해당 tool 또는 runtime의 owning source를 따른다.
