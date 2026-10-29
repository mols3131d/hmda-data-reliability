---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Unify Current Review Prompt
description: 일반 실행을 현재 한국어 단계 프롬프트로 통일하고 버전별 JSON 검토를 레거시로 격리합니다.
---

## Why

CLI의 새 기본 경로와 달리 일반 Python API에는 기존 structured 실행이 남아 있다. 사용자가 v1~v3를 레거시로 분리하고 우리가 수정한 현재 프롬프트로 실행하도록 명시했다.

## What Changes

- 일반 API·직접 service·live CLI를 현재 한국어 단계별 텍스트 실행으로 통일한다.
- 버전별 JSON 검토는 명시적 legacy namespace와 version 선택으로만 제공한다.
- 기존 환경의 버전 값이 일반 실행을 바꾸지 못하도록 하고 설정·문서를 일치시킨다.
- 기존 version의 본문·digest와 기록은 레거시 snapshot으로 보존한다.

## Boundaries

- **In Scope:** API·CLI 선택, 프롬프트와 legacy 리소스, 설정·회귀·운영 안내.
- **Out of Scope:** main 병합, 모델·credential 변경, 품질 채택 판정, 과거 invocation 재작성, Langfuse 기능 확장.

## Capabilities

### Modified Capabilities

- `reliability-agentic-review`: 일반 검토와 명시적 레거시 실행 경계.
- `review-ai-prompt-engineering`: 현재 모듈 조립과 retired version snapshot 분리.
