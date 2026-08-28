---
type: openspec-spec-driven-tdd-design
category: design
title: "Review AI와 Runtime AI ownership boundary"
description: "Review semantics와 provider-neutral runtime 사이의 단방향 dependency와 migration boundary를 고정합니다."
---

## Technical Delta

### Boundary Changes

| Boundary | Owns | Does Not Own |
| --- | --- | --- |
| `reliability` | deterministic Incident/Evidence/Remediation/Recovery truth | prompt, model/provider integration, AI invocation |
| `review_ai` | review contracts, prompt projection, validation, orchestration, review provenance/store | provider SDK transport, approval/recovery authority |
| `runtime_ai` | provider-neutral rendered message/request/response/usage contract, runtime settings, OpenAI-compatible adapter | Reliability contract, review policy, provenance meaning |

`review_ai`는 `reliability`와 `runtime_ai`를 사용할 수 있지만, `runtime_ai`는 두 package를 import하지 않는다. Runtime model은 Reliability의 Pydantic base를 재사용하지 않고 package-local frozen/forbid base를 사용해 dependency inversion을 지킨다.

### Migration Strategy

- Repository search에서 기존 agentic-review Python surface의 consumer는 source, test와 live harness로 한정되므로 compatibility module이나 re-export shim을 남기지 않는다.
- `ChatMessage`, `RenderedPrompt`, provider request/response/usage와 transport error는 capability-neutral contract로 `runtime_ai`에 이동한다.
- Prompt identity, canonical input projection, review evidence/store와 `review_null_spike()`는 `review_ai`에 남긴다.
- `AgenticReviewSettings`는 runtime ownership을 드러내는 `RuntimeAISettings`로 rename하되 field/default/sanitization behavior는 유지한다.
