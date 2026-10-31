---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Format Review AI Prompts as Markdown
description: 한국어 프롬프트를 Markdown 리소스로 제공하고 검토 규칙을 읽기 쉽게 구분합니다.
---

## Why

일반 텍스트에 역할·출력 계약·검토 기준이 이어져 있어 사람이 규칙을 찾아 읽기 어렵다.

## What Changes

- v1/v2/v3 프롬프트를 `.md` 리소스로 바꾸고 제목, 목록, 인라인 코드와 v2의 JSON 코드 블록으로 정리한다.
- 기존 한국어 지시와 JSON 계약을 유지하며 지시문의 Markdown과 모델의 JSON 응답 형식을 구별한다.
- 로더, 현재 문서 경로와 메시지 digest 회귀를 새 리소스에 맞춘다.

## Capabilities

### Modified Capabilities

#### `review-ai-prompt-engineering`

- 프롬프트 리소스의 Markdown 형식과 구조를 정의하고 그대로 로드되는 경계를 유지한다.

## Impact

- 입력 투영, 출력 schema, validator와 version 기본값은 유지한다.
- Markdown 표기가 추가되어 현재 digest는 달라지며 과거 invocation은 기록된 revision으로 재생한다.
