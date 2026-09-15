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

한국어 번역어와 영어 원어는 필요한 경우에만 병기한다. 쉬운 단어, 의미가 자명한 번역 또는 문맥상 혼동이 없는 용어에는 영어 원어를 덧붙이지 않는다.

- 영어 원어가 식별, 검색, 구분 또는 정확한 기술 의미 확인에 실제로 필요할 때만 처음 등장하는 위치에서 한 번 병기한다.
- 한국어만으로 의미가 충분하면 병기하지 않는다. 예: `기준선`으로 충분하면 `기준선(baseline)`으로 쓰지 않는다.
- 한 번 병기한 뒤에는 선택한 표기 하나를 사용한다. 정확한 영어 label이나 identifier를 다시 가리켜야 하는 경우는 예외다.
- 프로젝트가 이름을 부여한 개념, 제품명, 선언된 label과 identifier는 정해진 표기를 보존한다.
- 영어 일반명사를 괄호 안에 병기할 때는 고유명이나 선언된 표기가 아닌 한 일반적인 대소문자를 따른다.

## Prose

설명 본문과 긴 서술형 문장은 기본 언어 규칙을 따른다. 기술 용어가 영어라고 해서 주변 본문까지 영어로 쓰지 않는다.
