---
type: openspec-spec-driven-tdd-design
category: design
title: "Bounded agentic review design"
description: "deterministic Reliability truth를 보존하면서 provider 호출, validation과 replay 가능한 invocation evidence를 분리한다."
---

## Approach

`reliability/agentic_review/`를 기존 detection, impact, remediation과 나란히 두는 read-only surface로 추가한다. `review_null_spike()`는 input preflight → canonical input projection → provider call → parse와 deterministic validation → invocation evidence persistence 순서로 실행한다. Input preflight가 실패하면 provider와 evidence store를 호출하지 않는다.

Provider SDK, prompt rendering, validator와 filesystem persistence는 서로 다른 책임으로 둔다. Public review surface는 approval, recovery 또는 data mutation API를 호출하지 않는다. Exact field, status, wire profile과 failure contract는 Spec이 소유하고, 이 문서는 구현을 제약하는 비자명한 결정만 기록한다.

## Boundaries

| Boundary | Owns | Does Not Own |
| --- | --- | --- |
| **Deterministic Reliability** | `Incident`, `Evidence`, `RemediationDraft`와 null-spike canonical facts | LLM 해석, provider 선택, approval 결정 |
| **Agentic Review** | snapshot, prompt projection, structured output와 deterministic validation | incident 탐지, RCA truth 변경, action 실행 |
| **OpenAI-compatible adapter** | SDK client와 bounded transport behavior | Reliability business rule, approval 또는 recovery |
| **Invocation Evidence Store** | logical invocation provenance의 create-only persistence | canonical Reliability state 변경, raw prompt/log 보존 |
| **Approval / Recovery** | 기존 exact proposal과 external approval 이후의 mutation | Agentic output 해석 또는 자동 실행 |

## Decisions

### D1. Snapshot once and derive one canonical target

- **Decision:** Review input은 기존 `Incident`, `Evidence`, `RemediationDraft`와 prompt metadata를 call-scoped snapshot으로 고정한다. Null-spike target fact는 제공된 Evidence 중 하나의 canonical target에서만 유도한다.
- **Rationale:** Caller mutation이나 model interpretation 때문에 prompt, validator와 provenance가 서로 다른 사실을 보지 않게 한다.
- **Trade-off:** 첫 slice는 하나의 `null_spike` target만 다룬다. 다른 incident type이나 multi-target review는 별도 contract가 필요하다.

### D2. Keep one thin provider adapter

- **Decision:** OpenAI Python SDK는 하나의 OpenAI-compatible adapter 뒤에서만 사용한다. SDK hidden retry는 끄고 transport retry ownership은 adapter 한 곳에 둔다. Reliability domain은 provider별 branch를 소유하지 않는다.
- **Rationale:** Local Ollama와 cloud endpoint가 공유하는 최소 wire profile을 한 경계에서 검증하고 retry 횟수와 failure classification을 예측 가능하게 만든다.
- **Trade-off:** Common profile을 지원하지 않는 model은 이 slice에서 사용할 수 없다. Provider-specific profile은 실제 필요가 생길 때 별도 변경으로 다룬다.

### D3. Use the canonical input projection as the replay boundary

- **Decision:** Prompt renderer는 Spec이 정의한 allowlist로 하나의 `canonical_input` object를 만든다. 같은 object를 provider user data block의 source로 사용하고 invocation evidence에도 bounded structured snapshot으로 저장한다. Raw rendered prompt는 저장하지 않는다. `PromptIdentity`, caller-provided `project_revision`, stored `canonical_input`으로 prompt를 다시 render한 뒤 실제 invocation의 `prompt_digest`와 비교한다.
- **Rationale:** Incident/Evidence reference와 digest만으로는 실제 input을 복원할 수 없고, raw prompt 전체 저장은 불필요한 중복과 leakage surface를 만든다. Provider에 실제 전달한 structured projection을 보존하면 replay 근거와 최소 저장 원칙을 함께 만족한다.
- **Trade-off:** 과거의 exact replay는 recorded `project_revision`에 해당하는 prompt implementation을 다시 사용할 수 있어야 한다. 해당 revision을 resolve할 수 없으면 structured input과 digest는 검토할 수 있지만 exact prompt reconstruction은 증명할 수 없다.

### D4. Keep a conservative action guard, not a semantic parser

- **Decision:** Parsed output은 provider와 무관한 deterministic validator가 input snapshot의 identity, canonical facts와 Evidence references에 대조한다. Action boundary는 명백한 standalone command/authority pattern만 bounded regex로 차단한다. Quote, negation, approval-condition의 자연어 scope를 정확히 판별하려 하지 않는다.
- **Rationale:** Evidence binding과 canonical fact 비교는 결정론적으로 증명할 수 있지만 자연어 의미의 정교한 분류는 MVP의 신뢰 경계가 아니다. 실제 mutation authority는 review surface 밖의 `RecoveryProposal` + human approval과 read-only execution boundary가 통제한다.
- **Trade-off:** `forbidden-action-policy-v1`은 보수적으로 false positive를 낼 수 있고 문맥이 복잡한 자연어를 완전하게 분류하지 않는다. 이 한계는 명시적으로 수용하며, semantic policy가 실제 필요하다는 evaluation evidence가 쌓일 때 별도 capability로 확장한다.

### D5. Persist one logical invocation and fail closed on provenance

- **Decision:** Provider call이 시작된 logical review마다 invocation identity 하나를 만들고 transport retry는 attempt count로 집계한다. Record는 canonical input, parsed output이 있으면 그 output, validation, sanitized configuration, prompt identity/digest, `project_revision`과 runtime metadata를 create-only로 저장한다. Directory 생성, temporary file write/link, fsync 등 persistence 필수 과정의 filesystem failure는 모두 `InvocationEvidenceStoreError`로 정규화하여 accepted result를 차단하고 typed `provenance_failed`로 종료한다. 성공적으로 기록된 후의 temporary cleanup 실패는 best-effort hygiene으로 처리하며 이미 확정된 provenance 성공을 번복하지 않는다. Input preflight failure는 provider invocation이 아니므로 record를 만들지 않는다.
- **Rationale:** 한 review의 input, output, validation과 runtime evidence를 한 record에 묶으면 failure investigation과 replay가 단순해진다. Provenance가 없는 accepted output을 허용하지 않아 observable AI operation이라는 경계를 유지한다.
- **Trade-off:** Local filesystem store는 distributed audit log, encryption 또는 retention policy를 제공하지 않는다. 이 slice는 local proof에 필요한 create-only semantics까지만 소유한다.

## Verification

Offline test는 snapshot invariants, canonical input rendering, provider-independent validation, conservative action guard, adapter transport behavior와 create-only evidence replay를 검증한다. Integration test는 accepted와 각 typed failure 전후 deterministic Reliability state가 같고 invocation evidence write 외 mutation이 없는지 확인한다. Ollama live proof는 같은 adapter와 validator를 사용하되 default suite와 분리한다.

## Risks

- **Ungrounded output:** canonical facts와 Evidence reference를 deterministic validator가 다시 비교한다.
- **Prompt injection:** Evidence와 model output을 untrusted data로 취급하고 review surface에 execution interface를 제공하지 않는다.
- **Natural-language ambiguity:** MVP action guard는 semantic completeness를 목표로 하지 않는다. 복잡한 문맥은 보수적으로 reject할 수 있으며 실제 mutation 안전성은 read-only + proposal-bound approval 경계가 소유한다.
- **Provenance leakage:** `base_url` 내 credential(userinfo, query parameter 및 URL fragment) 입력을 거부하고, provider에 전달한 allowlisted canonical input과 parsed output만 bounded record에 보존하며 raw prompt, raw log, credential과 raw provider error는 저장하지 않는다.
- **Provider drift:** common adapter contract 밖의 model behavior를 자동으로 흡수하지 않고 typed failure로 격리한다.
