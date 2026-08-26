---
title: "Rule"
description: "Repository structure로 applicability가 결정되는 instruction surface인 Rule의 선택 기준, canonical source와 책임 경계를 정의합니다."
categories:
  - ai-engineering
  - software-engineering
tags:
  - rulesync
---

# Rule

Rule은 **repository structure로 applicability가 결정되는 instruction surface**다. 이 project에서는 path, glob, file type, extension처럼 여러 위치에 반복되는 structural scope를 표현할 때 Rulesync Rule을 사용한다.

## Selection

Rule을 우선 사용하는 경우:

- 같은 종류의 파일에 동일한 지침이 반복해서 필요하다.
- 여러 위치에 같은 하위 directory pattern이 반복된다.
- applicability를 task 의미가 아니라 repository structure로 안정적으로 결정할 수 있다.
- 여러 `AGENTS.md`에 같은 cross-cutting 지침을 복제하는 것보다 하나의 selector가 책임을 더 정확하게 표현한다.

하나의 directory subtree가 자연스럽게 소유할 수 있으면 nearest `AGENTS.md`를 우선한다.

Skill도 정책, 제약, 판단 기준 같은 instruction을 담을 수 있다. Rule과 Skill의 선택 기준은 [AI Agent](README.md)가 소유한다.

## Source

Project-authored Rule의 canonical source는 `.rulesync/rules/**`다. 외부 자산의 관리 경로와 source ownership은 [AI Agent](README.md#asset-management)를 따른다.

Generated projection과 `.agents/route/rules.jsonl`은 derived surface다. Selector와 target별 projection semantics는 Rulesync와 실제 target runtime의 current contract를 따른다.

## Boundary

이 문서는 **Rule의 structural applicability와 source location**만 소유한다.

- surface 선택과 asset management: [AI Agent](README.md)
- task-selected instruction: [Skill](skill.md)
- Rulesync integration detail: [`.rulesync/README.md`](../../../.rulesync/README.md)
