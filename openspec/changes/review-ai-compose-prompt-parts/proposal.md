---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Compose Review AI Prompt Parts
description: 프롬프트를 책임별 조각으로 관리하고 검증 후 단일 기본값으로 통일하는 방침을 정의합니다.
---

## Why

버전별 전체 프롬프트가 공통 규칙을 반복하고 있어 같은 내용을 여러 곳에서 수정해야 한다. 다중 버전 비교의 목적은 설명되어 있지만 채택 이후 기본 경로를 하나로 통일한다는 방침이 없고 기존 Spec은 서로 다른 기본값을 영구 보존하도록 읽힌다.

## What Changes

- 역할·언어·자문 경계와 출력 계약을 공통 Markdown 조각으로 분리하고 버전별 순서를 명시해 조립한다.
- 공유 정책, `null_spike` 작업, 출력 계약, 검토 지침과 예시의 책임·재사용 범위를 구분하고 조립부터 provider 전달까지의 개발 가이드를 제공한다.
- 개발 비교와 실제 채택을 구분하며 채택 변경에서 API/live 기본값을 하나의 공통 선택 정의로 통일하도록 명문화한다.
- 조각 추출 전후의 실제 메시지·공백·digest는 그대로 보존한다.

## Boundaries

- **In Scope:** 조각 구성과 조립, 프롬프트 lifecycle, 관련 Spec·가이드·회귀.
- **Out of Scope:** 지금 특정 version의 채택, 현재 기본값 전환, schema·validator·provider 설정 변경, 과거 실행 기록 재작성.

## Capabilities

### Modified Capabilities

#### `review-ai-prompt-engineering`

- 공유 Markdown 조각과 결정적 조립 및 채택 후 하나의 active 기본값을 사용해야 하는 lifecycle을 소유한다.

#### `reliability-agentic-review`

- 현재 개발 기본값과 미래 단일 기본값 전환을 구분하고 과거 재현은 저장된 version/revision에 고정한다.
