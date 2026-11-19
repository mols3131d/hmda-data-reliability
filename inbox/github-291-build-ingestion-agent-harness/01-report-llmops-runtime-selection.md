---
type: report
title: LLMOps Redesign Runtime Selection
description: 기존 Reliability AI 실행부를 교체하고 적재 조사까지 연결할 LLMOps 런타임 기준을 정리합니다.
tags:
  - llmops
  - langgraph
  - codex
  - reliability-ai
  - langfuse
---

# LLMOps Redesign Runtime Selection

**이번 개편의 기본 구성은 LangGraph와 LangChain Core다.** 기존 Python 조사 루프와 OpenAI-compatible 전용 제공자 경계를 새 그래프와 모델 제공자 계약으로 교체한다. 첫 로컬 제공자는 ChatGPT 구독 OAuth를 사용하는 Codex로 검증하고, Ollama도 같은 작업 흐름에서 선택할 수 있게 한다.

## Decision

LangGraph가 조사 상태, 허용 도구 실행, 분기와 종료를 명시적으로 관리한다. LangChain Core는 공통 메시지·도구·모델 인터페이스에 사용한다. Deep Agents는 별도 계획 계층이나 하위 에이전트가 필요한 요구가 확인되지 않아 이번 구조의 중심에 두지 않는다.

현재 `investigate_incident`는 Python의 동기 반복문이 tool-call 순서와 예산·응답 보존을 함께 소유한다. `runtime_ai`의 단일 OpenAI-compatible Chat Completions adapter는 Ollama 같은 호환 endpoint를 연결하지만, Codex의 ChatGPT 구독 OAuth App Server 흐름을 표현하지 않는다. 따라서 현재 실행부와 모델 adapter를 새 그래프·제공자 경계로 바꾼다. 결정론적 incident/evidence와 승인된 복구 계약은 새 실행부의 입력·도구·권한 경계로 유지한다. [현재 조사 루프](../../src/hmda_reliability/reliability_ai/investigation/service.py), [현재 제공자](../../src/hmda_reliability/runtime_ai/provider.py), [도메인 경계](../../docs/domains/review-ai.md)

## Provider Priority

1. **Codex via ChatGPT subscription OAuth.** Codex App Server의 ChatGPT 계정 인증을 확인하고, 구조화된 조사 제안과 완료·실패·중단 상태를 그래프의 제공자 계약으로 변환한다. 인증 정보는 Codex가 관리하는 경로에 둔다.
1. **Ollama.** 로컬 Chat Completions 제공자를 동일한 그래프 입력·결과 계약으로 연결한다. 제공자별 요청 방식은 adapter 안에 둔다.

두 adapter는 조사 요청, 정규화된 제안·사용량·실패 상태를 같은 경계로 전달한다. 그래프가 결과를 검증한 뒤 허용 도구를 실행한다. 제공자 응답으로 도구 권한이나 복구 승인이 생기지는 않는다. [Codex 제공자 설계](04-design-runtime-ai-codex-oauth-provider.md)

## LLMOps Boundaries

Langfuse native Prompt와 실제 모델·도구 관측은 프롬프트 버전 및 실행 증거를 연결하는 경로로 유지한다. 실행 ID, 요청 입력, 응답 원문, 선택된 도구, 조사 상태와 실패 이유는 로컬에서 먼저 보존한다. 외부 관측이 실패해도 이미 계산한 결과를 모델 재호출 사유로 사용하지 않는다. 기존 평가 CLI와 사람 평가의 증거는 새 조사 실행의 기술적 완료와 구분한다. [현재 평가·관측 계약](../../docs/domains/review-ai.md#provenance-and-evaluation)

## Apply to Ingestion

기존 incident 조사 실행부를 먼저 새 그래프와 제공자 계약으로 전환한다. 다음으로 같은 실행부를 재사용해 HMDA 적재 전 `prepare` 조사와 지정 Airflow 실행의 사후 `review_run`을 붙인다. 원천 버전 검증, 적재 권한과 data-plane 흐름은 기존 HMDA Data·Data Operations·Airflow 경계를 계속 사용한다. [적재 조사 설계](02-proposal-ingestion-llmops/README.md), [Codex 연동 순서](04-design-runtime-ai-codex-oauth-provider.md#implementation-order)

## Verification

이번 PR에서 새 실행부를 사용할 때까지는 다음을 완료 근거로 기록하지 않는다.

- Codex 구독 OAuth로 합성 입력 한 건을 실행하고 구조화된 제안과 조사 근거를 대조한다.
- Ollama가 같은 입출력 계약으로 동작하는지 확인한다.
- Fake provider로 그래프 분기, 도구 범위 거부, 시간 초과, 원문 보존과 재현을 검사한다.
- Airflow에서 실제 mutation 없이 지정 실행의 단계를 조회하고 원천 준비 조사와 결과 연결을 확인한다.
