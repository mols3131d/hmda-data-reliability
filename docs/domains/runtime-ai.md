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
| provider-neutral message/request/response contract | review prompt 내용과 policy |
| `RuntimeAISettings`와 sanitized runtime configuration | Reliability incident/evidence contract |
| OpenAI-compatible invocation adapter | approval, recovery 또는 mutation |
| timeout, bounded retry, output limit, usage/trace metadata | 범용 model router, fallback graph, agent orchestration |

Current provider-compatible bounded invocation의 normative behavior는 [`reliability-agentic-review`](../../openspec/specs/reliability-agentic-review/spec.md) Spec이 소유한다. Source는 current adapter와 configuration implementation을, tests는 executable expectation과 matching-revision validation evidence를 제공한다.

## Dependency Boundary

`runtime_ai`는 `reliability`와 `review_ai`를 import하지 않는다. Runtime contract는 package-local Pydantic base를 사용하며 review-specific identity, validation, provenance 의미를 포함하지 않는다.

`review_ai` 같은 capability owner는 자신의 prompt semantics를 소유하고 provider-neutral runtime contract와 adapter만 사용한다. 새 AI capability가 생겨도 provider mechanics만 재사용하고 capability semantics는 각 owner에 남긴다.

## Runtime Contract

`RuntimeAISettings`는 environment를 암묵적으로 읽지 않는다. Caller가 provider identity와 필요한 runtime limit을 명시적으로 전달한다. Adapter는 deterministic한 bounded request profile과 자체 retry/error normalization을 적용하며 provider-compatible request, timeout/retry와 no-hidden-retry behavior의 normative contract는 canonical Spec을 따른다. Exact current implementation detail은 [`runtime_ai`](../../src/hmda_reliability/runtime_ai/) source에서 확인하고 [`tests/runtime_ai`](../../tests/runtime_ai/)는 executable expectation과 validation evidence로 사용한다.

현재 concrete integration은 OpenAI Python SDK를 사용하는 OpenAI-compatible chat-completions adapter 하나다. Provider routing이나 새로운 abstraction은 두 번째 concrete need가 생기기 전까지 추가하지 않는다.

## Package Root API

`hmda_reliability.runtime_ai` package root는 capability caller가 configuration contract로 사용하는 `RuntimeAISettings`만 노출한다. OpenAI-compatible adapter, provider-neutral request/response contract와 transport error는 현재 repository 내부 module surface이며 package root에서 re-export하지 않는다.

이 경계는 provider implementation detail을 public API로 고정하지 않으면서 `review_ai`가 필요한 runtime mechanics를 직접 module dependency로 사용할 수 있게 한다.

## Contracts And Evidence

- Canonical bounded invocation contract: [`reliability-agentic-review`](../../openspec/specs/reliability-agentic-review/spec.md)
- Current implementation: [`runtime_ai`](../../src/hmda_reliability/runtime_ai/)
- Executable specification: [`tests/runtime_ai`](../../tests/runtime_ai/)

## Reading Order

1. Exact provider-compatible invocation requirement를 판단할 때는 canonical [`reliability-agentic-review`](../../openspec/specs/reliability-agentic-review/spec.md) Spec을 확인한다.
1. [`runtime_ai/__init__.py`](../../src/hmda_reliability/runtime_ai/__init__.py)에서 current package root API를 확인한다.
1. [`contracts.py`](../../src/hmda_reliability/runtime_ai/contracts.py)와 [`settings.py`](../../src/hmda_reliability/runtime_ai/settings.py)에서 current provider-neutral boundary 구현을 확인한다.
1. [`provider.py`](../../src/hmda_reliability/runtime_ai/provider.py)에서 current OpenAI-compatible adapter와 retry/error normalization 구현을 확인한다.
1. Review semantics가 필요하면 [Review AI](review-ai.md)로 이동한다.
