---
type: proposal
title: Refactor Agentic Review into review_ai and runtime_ai
description: reliability 내부의 agentic review를 review capability와 공통 AI runtime 책임으로 분리하는 리팩토링 제안서.
tags:
  - architecture
  - refactor
  - ai
  - reliability
  - runtime
---

# Refactor Agentic Review into `review_ai` and `runtime_ai`

## Summary

현재 AI review capability는 다음 경로에서 Reliability domain의 하위 구현으로 존재한다.

```text
src/hmda_reliability/reliability/agentic_review/
```

이를 책임에 따라 두 top-level domain으로 분리한다.

```text
src/hmda_reliability/
├── reliability/
├── review_ai/
└── runtime_ai/
```

이 변경은 package rename이 아니라 다음 세 ownership을 분리하는 리팩토링이다.

- `reliability`: deterministic truth와 reliability lifecycle
- `review_ai`: AI가 수행하는 review capability와 그 semantics
- `runtime_ai`: 여러 `*_ai` capability가 공유하는 AI execution substrate

## Why

`agentic_review`는 Reliability artifact를 소비하지만 deterministic reliability truth를 직접 소유하지 않는다. 또한 현재 구현에는 review 자체의 의미와 AI provider/runtime 공통 책임이 한 package에 섞여 있다.

향후 LLM/AI는 review 외에도 여러 bounded delegation capability를 수행할 수 있다. 이 capability들을 하나의 포괄적인 AI domain 아래 모으면 ownership과 탐색성이 나빠진다. 반대로 provider invocation, retry, timeout, usage 같은 공통 실행 로직을 각 capability domain이 중복 소유해서도 안 된다.

따라서 capability는 책임별 `*_ai` domain으로 나누고, capability-neutral 실행 기반만 `runtime_ai`가 공유한다.

## Naming

### `review_ai`

`review`가 capability이고 AI는 modifier다.

```text
review_ai/
```

AI 기술 자체보다 무엇을 수행하는지를 먼저 드러낸다.

### `runtime_ai`

`runtime_ai`는 generic AI domain이나 common-utils package가 아니다. 여러 AI capability가 공유하는 **runtime execution responsibility**를 소유하는 supporting technical domain이다.

향후 구조는 필요에 따라 다음처럼 확장할 수 있다.

```text
review_ai/ ─────────┐
investigation_ai/ ──┼──> runtime_ai/
other_capability_ai/ ┘
```

새 capability domain은 실제 책임이 생길 때만 추가한다.

## Ownership Boundary

### `reliability`

계속 deterministic reliability truth와 lifecycle을 소유한다.

- incident
- evidence
- impact
- remediation
- recovery
- deterministic validation

AI prompt, provider, runtime execution lifecycle은 소유하지 않는다.

### `review_ai`

Review라는 capability의 의미를 소유한다.

- review input/output contracts
- review prompt와 prompt identity
- review orchestration
- review-specific validation
- review result/provenance semantics
- `review_null_spike()` 같은 review use case

AI output은 advisory이며 deterministic truth를 대체하지 않는다.

### `runtime_ai`

어떤 AI capability인지 알 필요가 없는 공통 실행 기반을 소유한다.

초기 책임 후보:

- provider-neutral invocation contracts
- OpenAI-compatible provider integration
- provider/model configuration
- retry와 timeout boundary
- output/runtime limits 중 capability-neutral한 부분
- usage와 provider trace metadata
- provider/runtime error normalization

향후 실제 공통 요구가 생기면 execution context, tool invocation boundary, tracing hook 등으로 확장할 수 있다.

`runtime_ai`는 review, investigation, remediation 같은 capability semantics를 소유하지 않는다.

## Dependency Direction

기본 방향은 다음과 같다.

```text
review_ai -> reliability
review_ai -> runtime_ai
```

반대 방향은 만들지 않는다.

```text
reliability -> review_ai   # 금지
reliability -> runtime_ai  # 금지
runtime_ai -> review_ai    # 금지
```

`runtime_ai`는 자신을 사용하는 capability를 몰라야 한다.

따라서 `import hmda_reliability.reliability`만으로 AI provider implementation이나 OpenAI SDK loading이 요구되지 않아야 한다.

## Refactoring Rule

현재 파일을 이름만 보고 기계적으로 이동하지 않는다. **개념과 change driver를 기준으로 분리한다.**

대략적인 방향은 다음과 같다.

```text
review_ai/
├── contracts.py      # review-specific contracts
├── evidence.py       # review provenance semantics
├── prompt.py
├── service.py
├── store.py          # review-specific persistence인 동안 유지
└── validator.py

runtime_ai/
├── contracts.py      # provider-neutral runtime contracts
├── provider.py
└── settings.py       # capability-neutral runtime settings
```

현재 `AgenticReviewSettings`처럼 review 설정과 provider/runtime 설정이 한 모델에 섞여 있다면 책임에 맞게 나눌 수 있다. 다만 분리를 위해 불필요한 configuration hierarchy를 만들지 않는다.

`InvocationEvidenceStore`처럼 구현 일부가 언젠가 공통화될 가능성이 있어도, 현재 review semantics와 storage layout에 묶여 있다면 우선 `review_ai`에 둔다. 두 번째 consumer가 생기기 전에는 speculative shared abstraction을 만들지 않는다.

## Internal Dependency Cleanup

현재 provider-neutral 값이 provider implementation module에 정의되어 불필요한 SDK dependency를 만들 수 있다.

예:

```text
evidence -> provider implementation -> OpenAI SDK
```

`ProviderUsage`, provider-neutral response metadata 등 capability-neutral 값은 `runtime_ai`의 순수 contract로 이동하는 방향을 우선 검토한다.

반대로 review-specific result, validation, provenance contract는 `review_ai`가 소유한다.

이를 이유로 `ports/`, `adapters/`, `gateways/`, `core/`, `common/` 같은 계층을 선제적으로 추가하지 않는다.

## Public Surface

`reliability` package root의 AI-specific re-export는 제거한다.

`review_ai` package root는 실제 review consumer가 필요한 최소 API만 노출한다. 예:

- `AgenticReviewInput`
- `AgenticReviewOutput`
- `AgenticReviewResult`
- review settings facade가 필요하다면 해당 public contract
- `PromptIdentity`
- `review_null_spike`

`runtime_ai`도 최소 public surface를 유지한다. provider implementation, transport internals, SDK-specific error는 실제 외부 consumer가 요구하지 않는 한 package root에서 광범위하게 re-export하지 않는다.

기존 public surface를 compatibility만을 위해 그대로 복제하지 않는다.

## Migration Scope

리팩토링 시 함께 확인할 범위:

1. `src/hmda_reliability/reliability/agentic_review/`의 책임을 `review_ai`와 `runtime_ai`로 분리
2. `reliability/__init__.py`의 AI-specific re-export 제거
3. 최소 `review_ai`와 `runtime_ai` public surface 정의
4. provider-neutral contracts와 SDK integration dependency 정리
5. tests를 새 ownership에 맞게 이동 및 조정
6. live harness/script import path 갱신
7. domain ownership을 설명하는 canonical docs 갱신
8. 현재 agentic review를 소유하는 OpenSpec/change contract가 있다면 새 ownership과 dependency direction에 맞게 정리

## Tests

기존 agentic review tests는 새 domain ownership에 맞춘다.

예상 구조:

```text
tests/
├── review_ai/
└── runtime_ai/
```

`runtime_ai`에 독립적으로 검증할 공통 runtime behavior가 실제로 존재할 때만 별도 tests를 둔다.

최소 다음 boundary를 검증한다.

- 기존 bounded AI review behavior가 유지된다.
- `review_ai`가 Reliability deterministic artifact를 정상적으로 소비한다.
- `review_ai`가 공통 provider/runtime 책임을 중복 구현하지 않는다.
- `runtime_ai`가 review-specific contract나 policy에 의존하지 않는다.
- Reliability가 `review_ai` 또는 `runtime_ai`에 의존하지 않는다.
- `import hmda_reliability.reliability`가 AI provider implementation loading을 요구하지 않는다.
- 각 package public API가 의도한 최소 surface와 일치한다.

## Compatibility

production source와 scripts에서 기존 import consumer를 먼저 확인한다.

실제 consumer가 없다면 다음과 같은 backward compatibility re-export는 만들지 않는다.

```python
from hmda_reliability.reliability import review_null_spike
```

필요한 caller는 새 owner에서 직접 import하도록 갱신한다.

## Non-goals

이번 리팩토링에서는 다음을 하지 않는다.

- 모든 AI capability를 하나의 umbrella domain에 모으기
- `ai_delegation`, `common_ai`, `shared_ai`, `core_ai` 같은 포괄적 package 추가
- 아직 존재하지 않는 `investigation_ai`, `remediation_ai` 등의 선제적 생성
- generic AI platform 구축
- agent framework 도입
- gateway/control-plane architecture 설계
- AI에 recovery/action authority 부여
- Reliability의 deterministic behavior 변경

## Acceptance Criteria

리팩토링 완료 조건은 다음과 같다.

- 현재 `agentic_review`의 review semantics가 `review_ai` top-level domain의 소유가 된다.
- capability-neutral AI execution 책임이 `runtime_ai`에 분리된다.
- dependency direction이 `review_ai -> reliability`, `review_ai -> runtime_ai`로 정리된다.
- `runtime_ai`가 review-specific semantics를 알지 않는다.
- `reliability` public surface와 import graph에서 AI-specific implementation dependency가 제거된다.
- 기존 bounded AI review behavior와 provenance semantics가 유지된다.
- tests, scripts, canonical docs, active contract가 새 ownership과 일치한다.
- 불필요한 compatibility shim, speculative shared abstraction, architecture layer가 추가되지 않는다.

## Principles

> Reliability owns deterministic truth.

> Capability-specific AI behavior belongs to its `*_ai` domain.

> `runtime_ai` owns only capability-neutral AI execution semantics.

KISS, DRY, YAGNI를 우선하며 이번 변경은 ownership과 dependency boundary를 바로잡는 데 필요한 최소 범위로 제한한다.
