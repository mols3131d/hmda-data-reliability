---
type: handoff
title: Bounded Agentic Review Implementation Handoff
description: null_spike vertical slice를 시작점으로 bounded LLM review contract와 provider-compatible invocation을 구현하기 위한 handoff
tags:
  - reliability
  - agentic-review
  - llm
  - llmops
---

# Goal

`null_spike`를 첫 vertical slice로 사용해 **deterministic Reliability 위에 제한된 LLM review를 추가한다.**

```text
Incident + Evidence + RemediationDraft
            ↓
      AgenticReviewInput
            ↓
       Thin LLM Adapter
            ↓
    OpenAI-compatible API
       ├─ OpenAI API
       └─ Ollama / local model
            ↓
      AgenticReviewOutput
            ↓
   Deterministic Validator
            ↓
      Advisory Review
```

LLM은 evidence와 기존 `RemediationDraft`를 설명·검토한다. Incident truth, approval, `RecoveryProposal`, recovery와 mutation authority는 기존 deterministic boundary가 계속 소유한다.

## Current State

이 handoff는 repository `main` revision `7bc9339bfa920f7a5b2642ffbbf5b8ea1c6172ac` 기준이다.

- [`src/hmda_reliability/reliability/remediation/workflow.py`](../../../src/hmda_reliability/reliability/remediation/workflow.py)는 deterministic `triage → rca → plan` LangGraph workflow이며 model invocation이 없다.
- [`src/hmda_reliability/reliability/remediation/draft.py`](../../../src/hmda_reliability/reliability/remediation/draft.py)에 Pydantic frozen `RemediationDraft`가 있다.
- active OpenSpec Change는 없다.
- OpenTelemetry API/SDK는 dev dependency로 있고 OpenAI Python SDK는 아직 없다.

## Scope and Boundary

| Owner | Responsibility |
| --- | --- |
| Deterministic Reliability | incident truth, Evidence, existing RCA/draft, review validation, recovery authority |
| LLM Review | evidence/draft 설명, consistency check, 누락·모순·불확실성 제시 |
| Forbidden | incident 재판정, approval, `RecoveryProposal` ownership, shell/SQL/file mutation, recovery execution, authority expansion |

첫 구현은 `null_spike` 하나만 완결한다. 다른 incident type parity를 동시에 맞추지 않는다.

## Contracts to Close

정확한 field 이름과 storage 위치는 OpenSpec에서 첫 slice에 필요한 만큼만 확정한다.

### AgenticReviewInput

최소 의미:

- incident identity/type
- 실제 제공되는 evidence identity/reference와 필요한 structured payload
- 기존 `RemediationDraft`
- prompt/version을 재현할 identity

자유 텍스트 전체보다 numeric/structured evidence와 reference를 우선한다.

### AgenticReviewOutput

최소 의미:

- review summary
- `evidence_used`
- draft에 대한 finding/concern
- uncertainty 또는 추가 확인 항목
- advisory recommendation

Pydantic schema를 사용하되 schema validity 자체를 safety proof로 보지 않는다.

### Deterministic Validator

최소 검사:

- `evidence_used`가 실제 evidence의 subset인가
- fabricated evidence가 없는가
- deterministic result와 명백하게 모순되는가
- approval/recovery/mutation authority를 주장하지 않는가
- forbidden action을 포함하지 않는가

### Invocation Evidence

실제 model call은 이후 eval/replay가 가능하도록 최소 provenance를 남긴다.

- `invocation_id`
- model + relevant config
- prompt identity/digest
- project revision
- incident/evidence refs
- structured output
- validation result
- latency
- available token/usage/cost
- optional `trace_id` correlation

OTel trace는 durable Invocation Evidence를 대체하지 않는다.

## Model Invocation Boundary

확정 방향:

- client: **OpenAI Python SDK**
- protocol boundary: **OpenAI-compatible API**
- local development/proof: **Ollama + lightweight model**
- cloud-compatible target: **OpenAI API**

Provider-specific code는 thin internal adapter에 격리한다. `base_url`, `api_key`, `model` 차이는 설정으로 처리하며 provider 변경 때문에 Reliability/domain code를 수정하지 않는다.

첫 endpoint는 `chat.completions`와 `responses` 중 **OpenAI와 선택한 local endpoint에서 공통으로 유지할 수 있는 가장 작은 경로**를 선택한다. 실제 live invocation proof는 Ollama로 닫을 수 있으며 OpenAI credential이 없으면 cloud call 성공을 acceptance로 요구하지 않는다.

## Security Requirements

LLM input과 output은 모두 untrusted로 취급한다.

- Raw log/Evidence는 보존하고 prompt injection 방어를 이유로 원본을 변조하지 않는다.
- LLM context는 필요한 정보만 선택하고 structured data를 우선한다.
- log, metadata, 외부 텍스트 안의 명령문은 instruction이 아니라 data로 취급한다.
- model output은 executable action으로 직접 연결하지 않는다.
- validator가 fabricated evidence, contradiction, authority escalation을 검사한다.

첫 slice에는 direct/indirect prompt injection, fabricated evidence, authority escalation, schema-valid dangerous output을 포함한 adversarial fixture를 둔다.

## Implementation Sequence

1. **OpenSpec Change** — `null_spike` bounded review와 authority boundary를 계약한다. 후보 capability는 `reliability-agentic-review`다.
2. **Input/Output contract** — 최소 Pydantic contract를 만든다.
3. **Validator first** — fake/stub output으로 deterministic validation과 adversarial fixture를 검증한다.
4. **Thin LLM adapter** — OpenAI Python SDK를 한 곳에 격리한다.
5. **Provider-compatible proof** — Ollama에서 `SDK → model → structured output → validator`를 실제 검증하고 OpenAI API가 같은 adapter/config boundary를 사용하도록 유지한다.
6. **Minimal invocation evidence** — provenance를 남기고 필요한 경우 OTel trace와 correlation한다.

Langfuse integration은 이 slice의 완료 조건이 아니다. Core contract가 안정된 뒤 trace/evaluation projection으로 연결한다.

## Acceptance

- `null_spike` Incident + Evidence + `RemediationDraft`에서 structured advisory review를 생성한다.
- LLM 호출 없이도 contract와 validator를 deterministic test로 반복 검증할 수 있다.
- local/cloud provider가 같은 adapter/config boundary를 사용한다.
- provider 변경 시 Reliability/domain code 변경이 필요하지 않다.
- fabricated evidence, forbidden authority와 주요 prompt injection fixture를 validator/eval로 다룬다.
- model output만으로 approval, recovery 또는 mutation이 발생하지 않는다.
- 실제 model invocation을 최소 한 번 검증하고 필요한 provenance를 남긴다.
- LLM failure/unavailability가 recovery authority를 부여하거나 변경하지 않는다.

## Deferred / Non-goals

이번 slice에서는 다음을 구현하지 않는다.

- multi-agent, RAG/persistent memory, autonomous RCA/recovery
- generic LLM gateway, provider routing/fallback platform
- 추가 agent framework 도입
- 모든 incident type parity
- production-grade authorization/distributed serving
- Langfuse wiring과 OTel backend/exporter 최적화

이번 slice에서 실제로 닫아야 하는 미정 항목은 **input/output schema, adapter boundary, endpoint, timeout/retry, Invocation Evidence storage**다. Local reference model 최적화와 observability backend 세부사항은 후속으로 남긴다.
