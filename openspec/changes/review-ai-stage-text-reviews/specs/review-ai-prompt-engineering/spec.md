---
type: openspec-spec-driven-tdd-spec
category: spec
title: review-ai-prompt-engineering
description: 기존 JSON 출력 조합과 구분한 한국어 텍스트 단계 프롬프트의 계약을 정의합니다.
---

## ADDED Requirements

### Requirement: Staged text prompt modules

시스템은 단계별 검토 질문과 prose 출력 방식을 한국어 Markdown 모듈로 관리해야 한다(SHALL). 단계별 조합은 적용 가능한 기존 작업·검토 지침·자문 경계를 재사용하고, 현재 단계의 신뢰된 system 질문과 별도 canonical input 및 assistant 자료를 결합해야 한다(SHALL). 단계별 출력 지시는 JSON 객체·키·타입 생성을 모델에 요구해서는 안 된다(MUST NOT).

기존 버전별 JSON 지시문 요구사항은 structured 경로에 적용하고 staged text 조합은 별도 identity로 구분해야 한다(SHALL). 기존 v1/v2/v3 프롬프트와 과거 실행 기록을 staged 내용으로 바꿔서는 안 된다(MUST NOT).

#### Scenario: Each stage requests prose for one review concern

- **WHEN** 근거 검토, 초안 비판 또는 종합 단계의 프롬프트를 조립할 때
- **THEN** 현재 단계의 질문·한국어 일반 텍스트 출력·자문 경계가 system에 포함되고 기존 전체 JSON 출력 설명은 포함되지 않아야 한다(SHALL).

#### Scenario: Replaying old structured invocations

- **WHEN** 기존 identity·revision으로 과거 structured invocation을 재현할 때
- **THEN** staged 조합 선택이 기존 메시지·digest 또는 출력 계약을 바꾸어서는 안 된다(MUST NOT).
