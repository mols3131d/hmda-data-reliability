---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Unify Current Review Prompt
description: 과거 검토 실행과 호환 지원을 삭제하고 현재 한국어 단계별 텍스트 수집만 제공합니다.
---

## Why

일반 실행을 현재 프롬프트로 통일하면서 버전별 JSON 실행을 legacy namespace로 남겼지만, 사용자는 레거시 자체를 삭제하고 지원하지 말라고 명시했다. 같은 실행 통일 목표에서 이전 보존 결정을 바로잡는다. 과거 프롬프트·JSON 계약·설정·평가 연결이 현재 동작으로 다시 선택될 수 없어야 한다.

## What Changes

- 현재 한국어 근거 검토·초안 비판·종합과 코드 JSON 취합을 유일한 Review AI 실행으로 남긴다.
- 버전별 service·prompt snapshot·renderer·PromptIdentity·JSON 응답 계약·파서·validator·invocation reader와 그 결과 전용 Langfuse projection을 삭제한다.
- CLI의 mode·prompt version·과거 projection 선택과 호환 안내·guard·fallback을 제거한다.
- Human rubric 평가 대상을 현재 StagedReviewOutput과 workflow_id로 전환하고 같은 사례·facts·revision·원문 digest의 비교 경계를 유지한다.
- Immutable input·bounded context·정확한 원문·시간 예산·create-only provenance를 보존한다.

## Boundaries

- **In Scope:** Review AI 실행·prompt 리소스·공개 계약·현재 결과 평가·CLI·환경 예제·문서·회귀 검증.
- **Out of Scope:** main 병합, model·credential 변경, 실제 출력의 품질 채택, 과거 로컬 artifact·Inbox·Git 기록 삭제 또는 재작성, 새 Langfuse 통합.
- **Historical evidence:** 이전 실행의 파일은 사용자 자료로 보존한다. 현재 package가 그 파일을 typed load·replay하는 호환 기능을 제공하지 않는다.

## Capabilities

### Modified Capabilities

- `reliability-agentic-review`: 현재 수집·보존 계약과 현재 output의 human 평가만 제공한다.
- `review-ai-prompt-engineering`: 현재 모듈 조립·한국어 지시·revision별 digest를 유지하고 과거 version 선택을 제거한다.
