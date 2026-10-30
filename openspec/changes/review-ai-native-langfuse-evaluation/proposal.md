---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Native Langfuse Review Evaluation
description: 프롬프트·실험·관측·사람 평가를 Langfuse에 맡기고 프로젝트의 중복 운영 계층을 제거합니다.
---

## Why

현재 구현은 native API를 사용하지만 Dataset·점수·대기열 초기화, 별도 프로세스, 사후 관측 재구성과 사람 평가 완비 검사를 직접 운영한다. 사용자가 [조사 결과](../../../inbox/github-280-improve-review-ai-output-quality/13-research-review-ai-langfuse-reduce-custom-code.md)를 바탕으로 Langfuse의 기본 기능과 공식 튜토리얼 관행을 최대한 사용하고 직접 구현을 최소화하도록 승인했다.

## What Changes

- 실행 프롬프트의 정본을 Langfuse Prompt Management로 옮긴다. 한국어 Markdown 모듈은 최초 등록용 자료로 유지하며 실행은 native composition·message placeholder·label/version을 사용한다.
- 최초 Prompt·합성 Dataset 등록과 반복 실험을 분리한다. 반복 실행은 이미 존재하는 Dataset을 SDK experiment task로 실행한다.
- 실제 모델 호출 구간을 native generation으로 관측하고 적용한 prompt·model·usage·실제 입력과 반환 원문을 연결한다.
- 사람의 점수·사유·대기열·비교는 native UI에 맡기고 별도 완비 검사·점수 조회·합계·비교 저장 모델을 제공하지 않는다.
- 별도 worker·watchdog·중복 live CLI·독자 환경 설정을 제거한다. SDK 기본 lifecycle을 사용하며 HTTP timeout을 프로세스 강제 종료 보장으로 표현하지 않는다.
- 세 단계와 대화 이력, Runtime의 한도와 예산, 원문 우선 로컬 보존·checkpoint·기계적 JSON 조립은 유지한다.

## Boundaries

- **In Scope:** native Prompt Management·합성 Dataset setup·작은 SDK task·호출 시점 관측·native UI 평가·중복 코드 제거·관련 계약과 안내.
- **Out of Scope:** 실제 HMDA 적재·운영 데이터 수집·모델 JSON 출력 복원·과거 실행이나 환경 설정 호환·자동 LLM judge·점수로 GitHub 승인/병합 또는 recovery 권한 생성.
- 실제 서버·모델 호출과 원격 쓰기는 이 구현 검증에서 수행하지 않는다. 로컬 fake와 SDK 계약 검사는 실제 원격 적재·사람 평가를 대신하지 않는다.

## Capabilities

### Modified Capabilities

#### `reliability-agentic-review`

- native 실험·호출 관측·로컬 보존·외부 실패와 사람 평가의 소유 경계를 조정한다.

#### `review-ai-prompt-engineering`

- 한국어 모듈의 최초 등록 자료와 Langfuse 실행 정본, native 조합·버전 고정·원격 시작 실패를 정의한다.

## Impact

- SDK는 `langfuse==4.15.6`을 기본 의존성으로 유지한다. 대상 서버 호환성을 확인하지 않은 v5 전환은 포함하지 않는다.
- 과거 실행 파일·Inbox·Git 기록은 보존하며 현재 결과로 변환하지 않는다.
