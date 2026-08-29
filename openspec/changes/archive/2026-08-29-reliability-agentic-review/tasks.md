---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: reliability-agentic-review
description: "evidence-bound null_spike advisory review, deterministic validation과 replay 가능한 invocation provenance를 OpenAI-compatible provider 위에 구현한다."
tasks_completed: 8
tasks_total: 8
tags:
  - "capability:reliability-agentic-review"
---

## Tasks

### Contracts and validation

- [x] 1. OpenAI-compatible runtime configuration과 dependency contract를 추가한다
  - **Covers:** Provider-compatible bounded invocation, Durable invocation evidence의 sanitized configuration
  - **Test first:**
    - explicit `base_url`, `SecretStr api_key`, `model`, `timeout_seconds`, `max_retries`, `temperature`, `max_output_tokens`, review-owned `max_prompt_bytes`와 `max_output_bytes`의 validation 및 기본값을 고정한다.
    - Environment를 암묵적으로 읽지 않는 public runtime settings와 live harness용 환경 변수 이름을 고정한다.
  - **Done when:**
    - `openai`가 project runtime dependency와 `uv.lock`에 반영된다.
    - `RuntimeAISettings`가 `timeout_seconds=30`, `max_retries=1`, `temperature=0`, `max_output_tokens=1024`, `max_output_bytes=32768`을 사용하고 `ReviewAISettings`가 `max_prompt_bytes=65536`을 사용한다.
    - Invalid/empty configuration을 거부하고 sanitized invocation configuration에 API key/credential이 포함되지 않는다.
    - Network 없이 contract test가 통과한다.

- [x] 2. `AgenticReviewInput`·`AgenticReviewOutput`·`AgenticReviewResult` contract를 구현한다
  - **Covers:** Structured null-spike review input, Structured advisory review output, Typed review result boundary
  - **Test first:**
    - 기존 detector fixture와 `RemediationDraft`를 이용해 snapshot input, exact evidence reference set, identity/asset/partition match를 고정한다.
    - Unique canonical target `Evidence`, `project_revision`, `deterministic_facts`, finding kind, recommendation enum과 result status를 고정한다.
  - **Done when:**
    - `PromptIdentity`, `AgenticReviewInput`, `NullSpikeFacts`, finding, `AgenticReviewOutput`, `AgenticReviewResult`가 `extra=forbid`와 frozen semantics를 지킨다.
    - Nested input snapshot이 caller mutation에 영향을 받지 않는다.
    - `accepted`, `validation_failed`, `unavailable`, `input_rejected`, `provenance_failed`의 output/path/failure field invariants가 provider 호출 없이 검증된다.

- [x] 3. Provider-independent deterministic validator와 bounded action guard를 구현한다
  - **Covers:** Deterministic review validation, Deterministic and adversarial evaluation의 offline scenarios
  - **Test first:** 제공되지 않은 evidence ID, incident/type/target-column mismatch, canonical numeric fact mismatch, 명백한 authority claim/standalone action command, descriptive non-command text와 prompt injection data를 fake output으로 작성한다.
  - **Done when:**
    - 순수 validator가 `fabricated_evidence`, `incident_mismatch`, `deterministic_contradiction`, `authority_escalation`, `forbidden_action` code를 중복 없이 stable order로 반환한다.
    - `forbidden-action-policy-v1`은 명백한 standalone command/authority pattern만 bounded regex로 다룬다.
    - Quote, negation, approval-condition의 자연어 scope를 정확히 판별하는 semantic parser를 구현하지 않는다.
    - 문맥이 복잡한 action text의 보수적 reject는 MVP trade-off로 허용한다.
    - 같은 fixture를 반복 실행해도 결과와 input `Evidence`/target state가 변하지 않는다.

### Provider and evidence

- [x] 4. Canonical prompt renderer와 thin OpenAI-compatible adapter를 구현한다
  - **Covers:** Canonical provider input projection, Provider-compatible bounded invocation, Prompt injection is data, not instruction
  - **Test first:**
    - Spec-defined allowlist만 가진 `canonical_input`과 allowlist 밖 field exclusion, canonical serialization, prompt digest를 고정한다.
    - Fake client가 받는 `canonical_input` 기반 messages, common `max_tokens` wire mapping, JSON object response, `stream=false`, no-tools를 고정한다.
    - Ollama/OpenAI base URL 교체, timeout, connection/5xx bounded retry, 4xx/schema failure no-retry를 고정한다.
  - **Done when:**
    - `review_ai` prompt renderer가 Spec-defined allowlist로 하나의 `canonical_input`을 만들고 같은 projection을 provider user data block과 invocation evidence input으로 전달한다.
    - `runtime_ai` adapter는 OpenAI Python SDK를 한 곳에서만 사용하고 SDK hidden retry는 `0`이다.
    - `max_output_tokens`는 common `chat.completions` profile의 `max_tokens`로 매핑된다.
    - Evidence payload는 data block으로 전달되고 prompt renderer/adapter가 shell, SQL, file, recovery 또는 mutation action을 실행하지 않는다.
    - Prompt가 review-owned `max_prompt_bytes`를 넘으면 provider 전에 `input_rejected`로 종료된다.

- [x] 5. Logical-call 기준 create-only `AgenticInvocationEvidence` model과 local JSON store를 구현한다
  - **Covers:** Durable invocation evidence
  - **Test first:**
    - Temporary artifact root의 logical success/validation-failure/unavailable record와 JSON reload를 고정한다.
    - `canonical_input`, prompt identity/digest, `project_revision`, incident/evidence refs, latency, attempt count, optional usage/trace, sanitized configuration, raw prompt/error 부재와 concurrent duplicate ID를 고정한다.
    - Stored `PromptIdentity`, `project_revision`와 `canonical_input`을 같은 application revision에서 다시 render했을 때 prompt digest가 일치하는지 고정한다.
  - **Done when:**
    - `review_ai`가 provider call마다 logical invocation 하나를 `HMDA_RELIABILITY_ARTIFACTS_DIR` 또는 `.local/artifacts` 아래 `agentic-review/invocations/<invocation_id>.json`에 create-only atomic write한다.
    - Record는 provider에 전달한 bounded `canonical_input`을 보존하고 raw rendered prompt, credential, raw log와 raw provider error를 보존하지 않는다.
    - Stored canonical input으로 replay한 message digest가 recorded `prompt_digest`와 일치한다.
    - Retry는 `attempt_count`로 보존된다.
    - 동일 ID overwrite 및 collision은 `provenance_failed`가 되며, write failure는 accepted result를 허용하지 않는다.

### Orchestration and product surface

- [x] 6. `review_null_spike()` orchestration과 typed failure boundary를 연결한다
  - **Covers:** Structured null-spike review input, Provider-compatible bounded invocation, Advisory and read-only boundary
  - **Test first:** input preflight reject, accepted review, provider unavailable, response/guard validation failure와 provenance failure를 fake provider/store로 연결하고 provider/store call ordering 및 input/recovery state 불변을 고정한다.
  - **Done when:**
    - `input_rejected`는 provider와 invocation evidence write를 시작하지 않는다.
    - Provider-started logical review는 하나의 invocation ID를 유지하고 provider 결과를 validation 후 create-only provenance로 저장한다.
    - `accepted`는 valid output + accepted validation + durable provenance가 모두 있을 때만 반환된다.
    - 어떤 review result도 approval, recovery 또는 data mutation authority를 생성하지 않는다.

- [x] 7. Public review surface와 opt-in live harness를 연결한다
  - **Covers:** Local and cloud-compatible configuration, Advisory and read-only boundary
  - **Test first:** public package surface, live-disabled default, required environment, invalid configuration과 provenance verification failure를 network 없이 검증한다.
  - **Done when:**
    - `review_ai` package root가 review consumer에 필요한 최소 contract와 use case만 export하고, `runtime_ai` root는 explicit settings contract만 export하며, `reliability`는 AI-specific surface를 re-export하지 않는다.
    - `.env.example`, `docs/domains/review-ai.md`, `docs/domains/runtime-ai.md`, `docs/domains/reliability.md`와 `docs/development/testing.md`가 provider configuration, secret 비저장, typed failure, ownership과 opt-in live proof를 설명한다.
    - 기존 deterministic lifecycle/recovery contract와 충돌하지 않는다.

- [x] 8. Offline regression과 live proof 경계를 검증한다
  - **Covers:** Deterministic and adversarial evaluation, Local and cloud-compatible configuration
  - **Test first:** default pytest가 network를 사용하지 않고 동일 fixture를 반복 검증하며 live command만 명시적 opt-in에서 provider를 호출하는지 확인한다.
  - **Done when:**
    - focused `tests/review_ai tests/runtime_ai`, 영향받는 Reliability regression, Ruff와 project type check가 통과한다.
    - 실제 Ollama proof는 default suite에서 분리하고 실행하지 않은 경우 미검증으로 명시한다.
