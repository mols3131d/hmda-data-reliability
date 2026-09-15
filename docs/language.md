---
title: "Language Policy"
description: "Repository 문서와 structured metadata에서 한국어와 영어를 사용하는 기준을 정의합니다."
categories:
  - software-engineering
tags:
  - markdown
---

# Language Policy

기본 언어는 한국어다. 한국어가 어색하고 영어가 자연스러울 때만 영어를 사용한다. 한국어와 영어가 모두 어색하면 한국어를 사용한다.

## Surface Language Rules

| Surface | Rule | Note |
| --- | --- | --- |
| Document title, H1–H3 heading | English | H4 이하 제목은 기본 언어 규칙을 따른다. |
| Field name, label | English | |
| Metadata key와 짧은 structured value | English | 문단처럼 긴 값은 본문으로 보고 기본 언어 규칙을 따른다. |
| File name, directory name, repository path | English | |
| Code identifier, API name, CLI name | Declared identifier | 식별에 필요한 이름은 선언된 표기를 그대로 쓰고, 주변 설명은 기본 언어 규칙을 따른다. |
| Established technical term | Korean or English | 기본 언어 규칙에 따라 자연스러운 한 표기를 선택한다. |

## Bilingual Terms

한국어 번역어와 영어 원어를 관습적으로 병기하지 않는다. 문맥에 자연스러운 한 표기를 선택하고 같은 의미에는 같은 용어를 사용한다.

- 번역 대응 관계가 식별, 검색, 구분 또는 이해에 실제로 도움이 될 때만 처음 등장하는 위치에서 한 번 병기한다. 예: `기준선(baseline)`.
- 한 번 병기한 뒤에는 선택한 표기 하나를 사용한다. 정확한 영어 label이나 identifier를 다시 가리켜야 하는 경우는 예외다.
- 프로젝트가 이름을 부여한 개념, 제품명, 선언된 label과 identifier는 정해진 표기를 보존한다.
- 영어 일반명사를 괄호 안에 병기할 때는 고유명이나 선언된 표기가 아닌 한 일반적인 대소문자를 따른다. 예: `baseline`, not `Baseline`.

## Prose

설명 본문과 긴 서술형 문장은 기본 언어 규칙을 따른다. 기술 용어가 영어라고 해서 주변 본문까지 영어로 쓰지 않는다.
