---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Localize Review AI Prompts
description: 프롬프트 작성 계약을 분리하고 모든 지원 버전의 지시문과 생성 설명을 한국어로 맞춥니다.
---

## Why

프롬프트는 프로젝트 기본 언어와 달리 영어로 작성되어 있고 모델 설명문의 출력 언어도 정하지 않는다. 기존 review Spec은 실행과 검증을 소유하지만 편집 가능한 프롬프트 리소스, 작성 언어와 변경 추적을 독립적으로 설명하지 않는다.

## What Changes

- `review-ai-prompt-engineering` Spec으로 버전별 텍스트 리소스, 한국어 지시문·설명문과 revision별 변경 추적을 정의한다.
- 지원하는 v1, v2, v3 지시문 및 v2 예시의 설명문을 한국어로 바꾼다.
- Review AI가 자체 생성하는 context gap과 빈 근거 요약의 대체 문구를 한국어로 바꾼다.
- JSON 필드명, 열거값, 입력 식별자와 수치는 보존한다.
- 과거 digest 보존 조건을 기록된 revision의 renderer와 리소스를 사용하는 replay로 명확히 한다.

## Boundaries

- **In Scope:** Review AI 프롬프트 리소스, 작성 계약, 한국어 설명문 지시, 관련 테스트·가이드.
- **Out of Scope:** 자연어 언어 판별기, validation 완화·강화, schema나 기본 version 변경, provider/runtime 설정 변경, 과거 invocation·응답의 재작성, 자동 judge.

## Capabilities

### New Capabilities

#### `review-ai-prompt-engineering`

- 한국어 프롬프트 작성, 텍스트 리소스 제공과 revision별 변경 근거를 소유한다.

### Modified Capabilities

#### `reliability-agentic-review`

- 프롬프트 작성 언어의 소유 Spec을 연결하고 historical replay를 recorded revision 기준으로 명확히 한다.

## Impact

- 한국어 번역으로 현재 메시지 바이트와 digest가 바뀐다. 과거 기록의 prompt identity, revision과 digest는 유지한다.
- 한국어 지시가 실제 모델 출력의 언어·품질 준수를 보장한다는 주장은 하지 않으며, 실제 출력은 별도 실행과 사람 검토로 확인한다.
