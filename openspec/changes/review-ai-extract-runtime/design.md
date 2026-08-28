---
type: openspec-spec-driven-tdd-design
category: design
title: "Review AI Runtime Extraction Boundary"
description: "Review semantics와 provider-neutral runtime 사이의 단방향 dependency와 migration boundary를 고정합니다."
---

## Technical Delta

### Boundary Changes

| Boundary | Owns | Does Not Own |
| --- | --- | --- |
| `reliability` | deterministic Incident/Evidence/Remediation/Recovery truth | prompt, model/provider integration, AI invocation |
| `review_ai` | review contracts, prompt projection/rendered review state, prompt byte preflight, validation, orchestration, review provenance/store | provider SDK transport, approval/recovery authority |
| `runtime_ai` | provider-neutral message/request/response/usage contract, provider/transport/output settings, OpenAI-compatible adapter | Reliability contract, review policy, prompt provenance meaning |

`review_ai`는 `reliability`와 `runtime_ai`를 사용할 수 있지만, `runtime_ai`는 두 package를 import하지 않는다. Runtime model은 Reliability의 Pydantic base를 재사용하지 않고 package-local frozen/forbid base를 사용해 dependency inversion을 지킨다.

Package root는 consumer-oriented API만 노출한다. `review_ai`는 review input/output/result, prompt identity와 review use case를, `runtime_ai`는 explicit settings contract만 re-export한다. Provider transport, low-level runtime contract와 review prompt/validation/provenance helper는 owning module에 남긴다.

### Migration Strategy

- Repository search에서 기존 agentic-review Python surface의 consumer는 source, test와 live harness로 한정되므로 compatibility module이나 re-export shim을 남기지 않는다.
- `ChatMessage`, provider request/response/usage와 transport error는 capability-neutral contract로 `runtime_ai`에 이동한다.
- Canonical input/json, rendered messages, prompt digest와 prompt byte count를 묶는 rendered review object는 `review_ai`에 남기고, `runtime_ai` adapter에는 provider-neutral messages만 전달한다.
- Prompt identity, canonical input projection, review evidence/store와 `review_null_spike()`는 `review_ai`에 남긴다.
- 기존 settings는 provider/model/transport/output 설정의 `RuntimeAISettings`와 review-only prompt preflight의 `ReviewAISettings.max_prompt_bytes`로 분리한다. 기존 기본값, validation과 sanitized invocation configuration 의미는 유지한다.
- AST 기반 architecture test로 `runtime_ai -> no review_ai/reliability`, `reliability -> no review_ai/runtime_ai` import invariant를 고정한다.
- CI domain selector에 `review_ai`와 `runtime_ai`의 own/reverse-dependency test closure를 추가해 moved integration tests가 선택되도록 한다.
