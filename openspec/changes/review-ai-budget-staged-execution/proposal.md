---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Budget Staged Review Execution
description: 단계별 검토의 전송 대기와 실행 예산을 분리하고 실패 원인을 보존합니다.
---

## Why

세 단계 검토에 단일 HTTP timeout과 단계별 retry만 적용하면 연결 실패와 긴 추론 대기를 구분하기 어렵고 전체 실행 시간도 예측하기 어렵다. 사용자가 환경 설정과 timeout의 재설계를 요청했다.

## What Changes

- 연결·응답 읽기 대기 제한과 단계·전체 실행 예산을 구분한다.
- 예산을 넘긴 응답의 성공 채택과 후속 단계·재시도 진입을 차단하면서 반환된 원문은 보존한다.
- 전송 timeout, 연결 실패, 실행 예산 소진을 서로 다른 실패 코드로 기록한다.
- 새 환경 변수의 우선순위·한계와 시작값을 문서화하고 기존 설정·과거 기록의 호환성을 유지한다.

## Boundaries

- **In Scope:** Runtime 전송 설정·bounded retry, staged 시간 예산·기록, live 환경과 회귀·운영 설명.
- **Out of Scope:** 진행 중 동기 호출의 강제 취소, 모델 서버 설정 변경, 품질 채점, 기존 기록 재작성, Langfuse 설정 개편.

## Capabilities

### Modified Capabilities

- `reliability-agentic-review`: 단계별 시간 예산과 provider 전송 대기·실패의 구분.
