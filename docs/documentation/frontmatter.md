---
title: "Frontmatter"
description: "일반 문서에 frontmatter를 적용하거나 `description`을 탐색·라우팅에 맞게 작성할 때 적용 범위와 선택 기준을 확인하는 정책입니다."
categories:
  - software-engineering
tags:
  - documentation
  - frontmatter
  - markdown
---

# Frontmatter

현재 사용하는 field와 required 여부는 repository root의 [`frontmatter.json`](../../frontmatter.json)을 따른다.

## Scope

일반 문서는 repository의 frontmatter schema를 따른다. 확장자만 보고 일괄 적용하지 않고 file role을 먼저 판단한다.

- `AGENTS.md`, `CHATBOT.md`, `SKILL.md`, agent/subagent file 같은 **Agent Asset과 instruction surface**에는 일반 문서 frontmatter를 강제하지 않는다. 해당 standard, framework, vendor 또는 repository rule이 metadata 형식을 소유한다.
- Systemic/generated artifact는 해당 artifact의 owner와 generator 규칙을 따른다.
- Agent Asset이나 tooling을 설명하는 일반 문서는 Agent Asset 자체가 아니므로 일반 문서 frontmatter 규칙을 따른다.

## Description

`description`은 문서를 열기 전에 후보를 구분하고 선택하는 데 쓰는 **탐색·라우팅 metadata**다. Generated docs index도 이 값을 사용한다.

가장 중요한 것은 **언제 이 문서를 선택해야 하는지** 드러나는가이다. 어떤 작업, 문제 또는 판단에 관련되는지 먼저 밝히고, 후보를 구분하는 데 필요하면 핵심 responsibility나 인접 문서와의 차이를 짧게 덧붙인다.

`description`은 문서를 자동으로 적용하거나 authority를 부여하지 않는다. 실제 applicability와 authority는 상위 instruction과 문서 본문, owning source가 정한다.

### Selection Check

같은 범위에서 `path + description`만 봐도 현재 작업에 맞는 후보를 고를 수 있는지 확인한다.

- 후보가 헷갈리면 실제 요청에 등장할 핵심 용어와 구분되는 responsibility를 보강한다.
- 파일명만으로 충분히 구분되고 설명이 새 정보를 주지 못하면 억지로 길게 만들지 않는다.
- 본문 목차를 압축해 나열하거나 제목을 `~을 설명합니다`로 되풀이하는 데 그치지 않는다.

대개 한 문장이면 충분하다. 정확한 선택에 꼭 필요할 때만 더 늘린다.

## Entrypoint Metadata

디렉터리나 문서 묶음의 진입점인 `README.md`도 일반 frontmatter schema를 따른다. 이 metadata는 README 파일 자체보다 **README가 대표하는 범위**를 설명해야 한다.

- `description`은 그 범위를 언제 찾아보거나 사용해야 하는지 표현한다.
- `title`은 README라는 파일명이 아니라 대표하는 범위를 사람이 읽을 이름으로 표현한다.

README를 언제 만들고 무엇을 담을지는 [README Authoring](readme-authoring.md)이 소유한다.

## Generated Index

README나 일반 문서의 frontmatter는 generated `INDEX.tsv`의 입력이 될 수 있지만, generated index는 metadata의 정본이 아니다. Index 생성 방식과 갱신은 repository tooling이 소유하며 generated output을 직접 편집하지 않는다.
