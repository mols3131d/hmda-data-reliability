---
title: "Documentation"
description: "문서의 공통 원칙, frontmatter와 README 작성 기준을 확인하거나 문서 구조·탐색성을 설계할 때 사용하는 documentation policy entrypoint입니다."
categories:
  - software-engineering
tags:
  - documentation
  - markdown
---

# Documentation

이 디렉터리는 repository 문서를 만들고 배치할 때 적용하는 **공통 문서 정책의 진입점**이다.

문서의 일반적인 품질과 ownership 판단은 [Documentation Principles](principles.md)가 소유한다. Frontmatter와 README처럼 특정 surface의 작성 기준은 각각의 문서가 소유한다. `docs/**`의 trust boundary와 phase lifecycle은 상위 [`AGENTS.md`](../AGENTS.md)가 계속 소유한다.

## Policies

| Document | Use When |
| --- | --- |
| [Documentation Principles](principles.md) | 문서의 목적, ownership, 정본, 탐색성, 현재성과 유지보수성을 판단할 때 |
| [Frontmatter](frontmatter.md) | 일반 문서의 frontmatter 적용 범위와 `description` 작성 기준을 확인할 때 |
| [README Authoring](readme-authoring.md) | 디렉터리나 문서 묶음에 README가 필요한지, 무엇을 담을지 판단할 때 |

Field schema와 required 여부는 repository root의 [`frontmatter.json`](../../frontmatter.json)이 소유한다. Generated `INDEX.tsv`와 같은 파생 목록의 동작은 해당 generator와 tooling guide가 소유하며 이 디렉터리에서 복제하지 않는다.
