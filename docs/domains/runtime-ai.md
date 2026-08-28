---
title: "Runtime AI: Provider-Neutral Invocation"
description: "Review semantics와 분리된 provider-neutral AI message, settings, response contract와 OpenAI-compatible invocation adapter를 소유하는 Runtime AI domain을 설명합니다."
categories:
  - artificial-intelligence
  - software-engineering
tags:
  - ai-runtime
  - openai
  - retry
---

# Runtime AI: Provider-Neutral Invocation

**`runtime_ai`는 AI capability의 의미를 알지 않고 provider 호출 mechanics만 소유한다.** Caller가 렌더링한 message와 명시적 settings를 받아 bounded OpenAI-compatible request를 실행하고 typed response 또는 runtime failure를 반환한다.

## Scope

| In scope | Out of scope |
| --- | --- |
| provider-neutral chat message와 rendered prompt contract | review prompt 내용과 policy |
| `RuntimeAISettings`와 sanitized runtime configuration | Reliability incident/evidence contract |
| OpenAI-compatible request/response adapter | approval, recovery 또는 mutation |
| timeout, bounded retry, output byte limit, usage/trace metadata | 범용 model router, fallback graph, agent orchestration |

## Dependency Boundary

`runtime_ai`는 `reliability`와 `review_ai`를 import하지 않는다. Runtime contract는 package-local Pydantic base를 사용하며 review-specific identity, validation, provenance 의미를 포함하지 않는다.

`review_ai` 같은 capability owner가 `RenderedPrompt`를 만들고 `OpenAICompatibleAdapter`를 호출한다. 새 AI capability가 생기더라도 provider mechanics만 재사용하고 capability semantics는 각 owner가 유지한다.

## Runtime Contract

`RuntimeAISettings`는 environment를 암묵적으로 읽지 않는다. Caller가 `base_url`, `api_key`, `model`과 필요한 limit을 명시적으로 전달한다.

Adapter는 다음 공통 profile을 유지한다.

- `temperature=0`
- non-streaming JSON object response
- no tools
- SDK hidden retry `0`
- adapter-owned bounded retry
- configured output byte limit

현재 실제 SDK integration은 OpenAI Python SDK를 사용하는 OpenAI-compatible chat-completions adapter 하나다. Provider routing이나 새로운 abstraction은 두 번째 concrete need가 생기기 전까지 추가하지 않는다.

## Public Surface

- `RuntimeAISettings`
- `ChatMessage`, `RenderedPrompt`, `ChatCompletionRequest`
- `ProviderResponse`, `ProviderUsage`, `TransportResponse`
- `OpenAICompatibleAdapter`
- `ProviderTransportError`, `ProviderUnavailableError`, `ProviderResponseTooLargeError`

정확한 contract와 adapter behavior는 [`../../src/hmda_reliability/runtime_ai/`](../../src/hmda_reliability/runtime_ai/)와 [`../../tests/runtime_ai/`](../../tests/runtime_ai/)에서 확인한다. Review와 runtime의 연결 behavior는 [`../../tests/review_ai/`](../../tests/review_ai/)가 검증한다.

## Reading Order

1. [`runtime_ai/__init__.py`](../../src/hmda_reliability/runtime_ai/__init__.py)에서 public surface를 확인한다.
1. [`contracts.py`](../../src/hmda_reliability/runtime_ai/contracts.py)와 [`settings.py`](../../src/hmda_reliability/runtime_ai/settings.py)에서 provider-neutral boundary를 확인한다.
1. [`provider.py`](../../src/hmda_reliability/runtime_ai/provider.py)에서 OpenAI-compatible adapter와 retry/error normalization을 확인한다.
1. Review semantics가 필요하면 [Review AI](review-ai.md)로 이동한다.
