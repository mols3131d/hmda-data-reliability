---
type: design
title: Reliability AI Runtime Replacement
description: 기존 사고 조사 실행부를 LangGraph 기반으로 교체하고 같은 실행부에 HMDA 적재 조사를 연결하는 설계입니다.
tags:
  - reliability-ai
  - langgraph
  - llmops
---

# Reliability AI Runtime Replacement

PR #291에서 **기존 사고 조사의 Python 루프, 단일 제공자 호출 경계, 턴 기록 방식을 LangGraph와 LangChain Core 기반으로 교체한다.** 사고 조사 API와 위임·평가 호출을 전환한 뒤, 같은 실행부로 적재 전 `prepare`와 적재 후 `review_run`을 연결한다. 첫 로컬 검증은 ChatGPT 구독 OAuth를 사용하는 Codex로 진행한다.

## Replacement Boundary

| 교체 대상 | 전환 후 책임 |
| --- | --- |
| `investigate_incident` 내부 모델·도구 반복문 | LangGraph가 입력 확인, 모델 호출 여부, 허용 조회, 종료를 관리한다. |
| 조사와 평가에 결합된 Chat Completions 호출 | Codex와 OpenAI 호환 연결을 같은 계약으로 제공한다. 기존 호환 설정은 Ollama와 다른 호환 서버를 명시적으로 선택하는 데 사용한다. |
| 매 턴의 전체 대화와 원문을 중복 저장하는 기록 | 원문과 관찰값을 한 번 저장하고, 참조로 턴 입력과 최종 결과를 복원한다. |

사건과 사실의 검증, 읽기 전용 근거 조회, 승인 요청에 결합된 복구 실행기, HMDA 적재·Airflow의 운영 계약을 재사용한다. 기존 조사 코드는 현재 동작을 대조할 기준으로 삼는다. [기존 구현 현황](../05-report-reliability-ai-implementation-status.md), [현재 조사 계약](../../../openspec/specs/reliability-agentic-review/spec.md)

## Design Documents

1. [Architecture](architecture.md)에서 조사 진입점, 그래프 분기, 위임 복구와 적재의 연결을 확인한다.
1. [Provider and Evidence](provider-and-evidence.md)에서 Codex와 Ollama의 공통 입출력, 실행 기한, 원문 보존과 Langfuse 관측을 확인한다.
1. [Migration and Verification](migration-and-verification.md)에서 호출부 전환, 기존 루프 제거와 완료 조건을 확인한다.

기존 사고 조사 실행부 교체를 첫 OpenSpec Change로 제안한다. 현재 적재 조사 Change는 이 교체에서 정의할 실행부 계약을 사용한다. [적재 조사 설계](../02-proposal-ingestion-llmops/README.md), [적재 조사 OpenSpec](../../../openspec/changes/reliability-ai-investigate-hmda-ingestion/proposal.md)
