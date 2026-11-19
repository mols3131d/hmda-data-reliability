---
type: design
title: Codex OAuth Provider Priority
description: Reliability AI 실행부 개편에서 Codex의 ChatGPT 구독 로그인을 먼저 연결하는 이유와 로컬 검증 기준을 기록합니다.
tags:
  - llmops
  - codex
  - oauth
---

# Codex OAuth Provider Priority

**첫 구현과 로컬 검증의 1순위 제공자는 ChatGPT 구독 계정으로 OAuth 로그인한 Codex다.** 사용자의 현재 환경에서 연결을 반복해 테스트하기 가장 쉬운 방식이기 때문이다. Ollama는 같은 LangGraph 조사에서 선택할 수 있는 다른 제공자로 둔다.

## Codex Integration

1. **공식 로그인 경로를 사용한다.** 로컬 `codex app-server`에 연결하고 `account/read`로 계정이 `chatgpt` 유형인지 확인한다. 로그인이 필요하면 Codex가 관리하는 ChatGPT 브라우저 로그인으로 연결한다. 세션과 토큰 갱신은 Codex가 관리한다. [Codex 인증](https://developers.openai.com/codex/auth), [App Server 인증 모드](https://learn.chatgpt.com/docs/app-server#authentication-modes)
1. **Codex에서 구조화된 제안을 받는다.** `turn/start`에 허용된 근거 요약과 `outputSchema`를 전달한다. 완료된 턴의 결과를 조회 요청 또는 근거 있는 권고로 읽는다. 검사한 결과만 LangGraph의 다음 단계에 전달한다. [Codex 턴 실행](https://learn.chatgpt.com/docs/app-server)
1. **LangGraph가 조사와 도구 실행을 관리한다.** 요청한 도구와 자료가 허용 범위인지 검사하고, 읽기 전용 도구 결과를 다음 판단의 근거로 돌려준다. 로컬 연동 검증에서 Codex의 파일·셸·도구 접근도 같은 조사 범위에 제한되는지 확인한다.

제공자 경계에는 근거 요약과 요청 예산이 들어가고, 구조화된 제안·실패 상태·실행 참조가 돌아온다. Codex 어댑터는 조사 ID와 `threadId`·`turnId`를 연결한다. 기록에는 인증 유형과 제공자 식별 정보를 사용한다. 기한이 지나면 `turn/interrupt`로 중단을 요청하고, 그때까지 검증한 근거를 담아 조사를 종료한다. [App Server 턴 중단](https://learn.chatgpt.com/docs/app-server)

## Implementation Order

- **기존 사고 조사 교체 Change에서 Codex를 먼저 연결한다.** 실제 사고 조사 진입점을 새 LangGraph로 전환한다. Codex와 Ollama는 그래프가 받는 같은 형태의 제안을 반환하도록 만든다.
- **적재 조사 Change에서 이 연결을 사용한다.** `prepare`와 `review_run`은 같은 제공자 계약을 사용한다. 기존 적재 조사 Change의 모델 연결 설계는 새 실행부 계약이 정해지면 그에 맞춰 갱신한다. [현재 적재 조사 Change](../../openspec/changes/reliability-ai-investigate-hmda-ingestion/proposal.md), [적재 조사 아키텍처](02-proposal-ingestion-llmops/architecture-plan.md)

## Local Verification

| 확인할 항목 | 완료 근거 |
| --- | --- |
| 구독 로그인 | `account/read`에서 ChatGPT 계정을 확인하고, 그 세션으로 승인된 합성 입력의 Codex 턴이 완료된다. |
| 도구 실행 경계 | 구조화된 조회 제안을 LangGraph가 검증하고, 승인된 조회와 결과가 조사 기록에 연결된다. 범위 밖 접근은 실행 경계에서 거절된다. |
| 인증·실행 실패 | 로그인 필요, 턴 실패, 기한 소진의 원인을 구분한다. 늦게 온 제안으로 새 조회를 시작하지 않는다. |

현재 확인 범위는 공식 문서와 로컬 Codex CLI `0.170.0`의 프로토콜 스키마다. 실제 구독 세션에서의 턴 실행은 위 로컬 검증 항목으로 남긴다.
