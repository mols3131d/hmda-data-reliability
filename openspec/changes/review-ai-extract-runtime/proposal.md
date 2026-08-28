---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: "Extract AI Runtime from Review AI"
description: "Reliability 내부 agentic review 구현을 review semantics와 provider-neutral AI runtime으로 분리하는 behavior-preserving refactor입니다."
tags:
  - "domain:review-ai"
  - "ai-runtime"
---

## Why

현재 `reliability/agentic_review`가 deterministic Reliability contract, review semantics, provider SDK와 runtime configuration을 한 package에서 함께 소유한다. 그 결과 `reliability` public import가 AI provider implementation을 끌어오고, 향후 review 외 AI delegation이 생기면 provider-neutral runtime을 재사용하기 어렵다.

## What Changes

- `review_ai`가 review input/output, prompt projection, deterministic validation, review orchestration과 invocation provenance를 소유한다.
- `runtime_ai`가 provider-neutral message/request/response contract, provider/model settings와 OpenAI-compatible adapter를 소유한다.
- `reliability`의 AI-specific re-export를 제거하고 deterministic truth와 recovery lifecycle에 집중시킨다.
- repository 내부 caller, test와 live harness를 새 ownership에 맞춘다. 기존 observable review status, prompt identity, provenance path/record semantics와 provider wire behavior는 유지한다.
- CI test routing이 새 domain과 reverse dependency를 인식하도록 맞춰 review/runtime integration을 prospective merge에서 검증한다.

## Boundaries

- **In Scope:** package ownership, import direction, 최소 package-root API, 내부 caller/test path, AI domain test routing, 관련 domain/testing 문서 정합성
- **Out of Scope:** review behavior 변경, prompt policy 변경, provider 추가, generic gateway/router, Langfuse, Airflow orchestration, recovery/approval semantics 변경, compatibility shim

## Impact

- `src/hmda_reliability/review_ai`, `src/hmda_reliability/runtime_ai`가 새 top-level owner가 된다.
- `review_ai -> reliability`, `review_ai -> runtime_ai`만 허용하고 `reliability -> review_ai/runtime_ai`, `runtime_ai -> reliability/review_ai` 의존은 만들지 않는다.
- package root는 실제 consumer가 요구하는 최소 API만 노출하고 provider/transport/provenance 내부 surface를 compatibility 목적으로 재수출하지 않는다.
- 기존 `reliability-agentic-review` behavioral contract와 `HMDA_AGENTIC_REVIEW_*` live configuration 이름은 변경하지 않는다.
