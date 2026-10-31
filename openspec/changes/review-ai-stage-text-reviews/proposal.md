---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Stage Review AI Text Responses
description: 같은 사례의 단계별 한국어 응답을 수집하고 애플리케이션이 결과 JSON을 생성하도록 합니다.
---

## Why

큰 JSON 응답을 모델에게 직접 생성하게 하면 검토 내용과 출력 형식 준수가 한 번의 생성에 결합된다. 사용자는 같은 맥락의 단계별 검토를 원하며 최종 JSON 생성은 코드가 맡도록 명시했다.

## What Changes

- 근거 검토·초안 비판·종합의 고정된 대화 단계에서 한국어 일반 텍스트를 요청한다.
- 코드가 원입력 식별자·수치와 단계별 원문을 결합해 별도 결과 JSON을 만든다.
- 단계별 요청·반환 원문·실패·최종 조립 결과의 출처를 연결하고 중간 실패를 보존한다.
- 기존 live 명령의 기본 경로를 staged로 연결하고 기존 structured 경로는 명시적인 비교·재현용 선택으로 보존한다.

## Boundaries

- **In Scope:** Review AI 고정 단계·출력·기록·모듈 프롬프트, Runtime AI assistant 메시지·명시적 text 호출, live 진입점·문서·회귀.
- **Out of Scope:** 자유로운 agent loop, 자동 semantic 추출·채점·JSON repair, 기존 결과를 새 결과로 변환, approval·recovery 권한, staged Langfuse projection, 과거 invocation 재작성.

## Capabilities

### Modified Capabilities

- `reliability-agentic-review`: 단계별 prose 수집, 코드 JSON 조립, 부분 실패 보존과 기존 structured 경로 구분.
- `review-ai-prompt-engineering`: 단계별 질문·텍스트 출력 모듈과 분리된 사례 데이터.
