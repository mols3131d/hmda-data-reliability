---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: "Reliability Bounded Agentic Review"
description: "null_spike의 deterministic evidence와 RemediationDraft를 검토하는 제한된 Agentic review contract와 observable invocation evidence를 추가한다."
tags:
  - "domain:reliability"
  - "capability:reliability-agentic-review"
  - "null-spike"
  - "ai-delegation"
---

## Summary

> **핵심 결정:** `null_spike`의 deterministic truth는 그대로 유지하고, LLM은 제공된 근거에 묶인 advisory review만 수행한다. `accepted` 결과는 deterministic validation과 invocation provenance 저장을 모두 통과한 경우에만 반환한다.

## Why

현재 Reliability는 `null_spike`의 `Incident`, `Evidence`와 `RemediationDraft`를 deterministic하게 생성하지만, 이를 사람이 검토하기 쉬운 advisory review로 연결하거나 실제 model invocation을 재현 가능한 evidence로 남기는 capability가 없다. 따라서 model output의 근거 사용, 위험한 권한 주장과 invocation 조건을 확인할 수 없다.

MVP는 deterministic truth를 유지한 채 LLM이 제공된 evidence와 기존 draft를 설명·검토하는 하나의 완결된 proof를 요구한다. LLM review의 품질이나 자연어 표현을 incident truth 또는 recovery authority로 승격하지 않으면서, `input_rejected`, provider 실패, validation 실패와 provenance 실패를 서로 구분하고 다시 평가할 수 있어야 한다.

## What Changes

- **Review contract:** `null_spike` `Incident`, 실제 `Evidence`와 기존 `RemediationDraft`를 묶는 snapshot 기반 structured input과 deterministic facts를 보존하는 advisory output을 추가한다.
- **Validation and safety:** typed review result, evidence subset, fabricated evidence, deterministic contradiction, authority escalation과 forbidden action을 검사하는 provider-independent validation contract를 추가한다. Untrusted `Evidence`와 model output은 data로만 취급한다.
- **Provider boundary:** OpenAI-compatible `chat.completions` API를 통해 local model과 cloud model을 같은 bounded review interface로 호출한다. 명시적인 실행 의도만 versioned action policy로 차단한다.
- **Provenance:** bounded prompt/output, sanitized configuration, `project_revision`, prompt digest와 logical invocation 단위의 durable evidence를 추가한다.
- **Evaluation:** 정상·실패·adversarial review를 model 호출 없이 반복 검증하고, default suite와 분리된 opt-in Ollama live proof를 제공한다.

## Boundaries

| Scope | Decision |
| --- | --- |
| **In scope** | Reliability domain의 `null_spike` 단일 vertical slice, evidence-bound advisory review, deterministic validation, typed failure result, OpenAI-compatible invocation과 최소 invocation provenance |
| **Out of scope** | 다른 incident type parity, LLM 기반 incident detection 또는 RCA, approval/recovery/mutation authority, autonomous action, multi-agent/RAG/persistent memory, generic gateway·provider routing platform, Langfuse와 production authorization |

## Capabilities

### New Capabilities

#### reliability-agentic-review

시스템이 deterministic `null_spike` `Incident`, 실제 `Evidence`와 `RemediationDraft`를 검토 가능한 structured advisory 결과로 변환한다. 또한 canonical facts·evidence references·action boundary를 deterministic하게 판정하고, provider invocation을 재현 가능한 provenance와 함께 기록한다.

## Impact

| Surface | Impact |
| --- | --- |
| **Code / Systems** | `src/hmda_reliability/reliability` 아래 review contract, typed result, validator, provider boundary와 invocation evidence 저장 경로를 추가하고 public reliability export를 확장한다. |
| **Data / Contracts** | Pydantic frozen snapshot/input/output/validation/invocation contract와 `null_spike` adversarial fixture를 추가한다. 기존 `Incident`, `Evidence`, `RemediationDraft`, `RecoveryProposal`의 authority 의미는 변경하지 않는다. |
| **Interfaces / APIs** | OpenAI-compatible `chat.completions` 기반 local/cloud-compatible review 호출 경계와 deterministic 호출 없는 validation API를 추가한다. Input preflight 실패는 provider invocation 없이 종료한다. |
| **Operations / Dependencies** | OpenAI Python SDK를 runtime dependency로 추가하고 local invocation은 Ollama를 사용한다. Invocation evidence는 기존 `HMDA_RELIABILITY_ARTIFACTS_DIR` 아래 logical call별로 저장하며 API key, credential, raw prompt/log와 raw provider error는 저장하지 않는다. |
| **Documentation** | Reliability domain guide, testing guidance와 `.env.example`에 opt-in provider configuration 및 live-proof 경계를 문서화한다. |
