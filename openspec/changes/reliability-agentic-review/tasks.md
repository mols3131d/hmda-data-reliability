---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: "Implement bounded null-spike agentic review"
description: "null_spike evidence-bound review contract, typed result, deterministic guard, OpenAI-compatible adapter와 invocation provenance를 test-first로 구현한다."
tasks_completed: 0
tasks_total: 8
tags:
  - "domain:reliability"
  - "capability:reliability-agentic-review"
  - "null-spike"
---

## Tasks

> **Status:** `0/8` tasks complete. 각 task는 `Test first`로 계약을 고정한 뒤 `Done when` 조건을 충족하는 순서로 진행한다.

### Contracts and validation

- [ ] 1. OpenAI-compatible runtime configuration과 dependency contract를 추가한다
  - **Covers:** Provider-compatible bounded invocation, Durable invocation evidence의 sanitized configuration
  - **Test first:**
    - explicit `base_url`, `SecretStr api_key`, `model`, `timeout_seconds`, `max_retries`, `temperature`, `max_output_tokens`, `max_prompt_bytes`와 `max_output_bytes`의 validation 및 기본값을 고정한다.
    - Environment를 암묵적으로 읽지 않는 public settings와 live harness용 환경 변수 이름을 고정한다.
  - **Done when:**
    - `openai`가 project runtime dependency와 `uv.lock`에 반영된다.
    - `AgenticReviewSettings`가 `timeout_seconds=30`, `max_retries=1`, `temperature=0`, `max_output_tokens=1024`, `max_prompt_bytes=65536`, `max_output_bytes=32768`을 사용한다.
    - Invalid/empty configuration을 거부하고 sanitized configuration serialization에 API key/credential이 포함되지 않는다.
    - Network 없이 contract test가 통과한다.

- [ ] 2. `AgenticReviewInput`·`AgenticReviewOutput`·`AgenticReviewResult` contract를 구현한다
  - **Covers:** Structured null-spike review input, Structured advisory review output, Typed review result boundary
  - **Test first:**
    - 기존 detector fixture와 `RemediationDraft`를 이용해 snapshot input, exact evidence reference set, identity/asset/partition match를 고정한다.
    - Unique canonical target `Evidence`, `project_revision`, `deterministic_facts`, finding kind, recommendation enum과 result status를 고정한다.
  - **Done when:**
    - `PromptIdentity`, `AgenticReviewInput`, `NullSpikeFacts`, finding, `AgenticReviewOutput`, `AgenticReviewResult`가 `extra=forbid`와 frozen semantics를 지킨다.
    - Nested input snapshot이 caller mutation에 영향을 받지 않는다.
    - `accepted`, `validation_failed`, `unavailable`, `input_rejected`, `provenance_failed`의 output/path/failure field invariants가 provider 호출 없이 검증된다.

- [ ] 3. Provider-independent deterministic validator와 adversarial fixture를 구현한다
  - **Covers:** Deterministic review validation, Deterministic and adversarial evaluation의 offline scenarios
  - **Test first:** 제공되지 않은 evidence ID, incident/type/target-column mismatch, canonical numeric fact mismatch, schema-valid authority escalation, forbidden action, descriptive draft action, direct/indirect prompt injection과 safe advisory output을 fake output으로 작성한다.
  - **Done when:**
    - 순수 validator가 `fabricated_evidence`, `incident_mismatch`, `deterministic_contradiction`, `authority_escalation`, `forbidden_action` code를 중복 없이 stable order로 반환한다.
    - `forbidden-action-policy-v1`이 descriptive backfill mention과 실행 명령을 구분한다.
    - 같은 fixture를 반복 실행해도 결과와 input `Evidence`/target state가 변하지 않는다.

### Provider and evidence

- [ ] 4. Canonical prompt renderer와 thin OpenAI-compatible adapter를 구현한다
  - **Covers:** Canonical provider input projection, Provider-compatible bounded invocation, Prompt injection is data, not instruction
  - **Test first:**
    - Spec-defined allowlist만 가진 `canonical_input`과 allowlist 밖 field exclusion, canonical serialization, prompt digest를 고정한다.
    - Fake client가 받는 `canonical_input` 기반 messages, common `max_tokens` wire mapping, JSON object response, `stream=false`, no-tools를 고정한다.
    - Ollama/OpenAI base URL 교체, timeout, connection/5xx bounded retry, 4xx/schema failure no-retry를 고정한다.
  - **Done when:**
    - Prompt renderer가 Spec-defined allowlist로 하나의 `canonical_input`을 만들고 같은 projection을 provider user data block과 invocation evidence input으로 전달한다.
    - Adapter는 OpenAI Python SDK를 한 곳에서만 사용하고 SDK hidden retry는 `0`이다.
    - `max_output_tokens`는 common `chat.completions` profile의 `max_tokens`로 매핑된다.
    - Evidence payload는 data block으로 전달되고 prompt renderer/adapter가 shell, SQL, file, recovery 또는 mutation action을 실행하지 않는다.
    - Prompt가 `max_prompt_bytes`를 넘으면 provider 전에 `input_rejected`로 종료된다.

- [ ] 5. Logical-call 기준 create-only `AgenticInvocationEvidence` model과 local JSON store를 구현한다
  - **Covers:** Durable invocation evidence
  - **Test first:**
    - Temporary artifact root의 logical success/validation-failure/unavailable record와 JSON reload를 고정한다.
    - `canonical_input`, prompt identity/digest, `project_revision`, incident/evidence refs, latency, attempt count, optional usage/trace, sanitized configuration, raw prompt/error 부재와 concurrent duplicate ID를 고정한다.
    - Stored `PromptIdentity`, `project_revision`와 `canonical_input`을 같은 application revision에서 다시 render했을 때 prompt digest가 일치하는지 고정한다.
  - **Done when:**
    - Provider call마다 logical invocation 하나가 `HMDA_RELIABILITY_ARTIFACTS_DIR` 또는 `.local/artifacts` 아래 `agentic-review/invocations/<invocation_id>.json`에 create-only atomic write된다.
    - Record는 provider에 전달한 bounded `canonical_input`을 보존하고 raw rendered prompt, credential, raw log와 raw provider error를 보존하지 않는다.
    - Stored canonical input으로 replay한 message digest가 recorded `prompt_digest`와 일치한다.
    - Retry는 `attempt_count`로 보존된다.
    - 동일 ID overwrite 및 collision은 `provenance_failed`가 되며, write failure는 accepted result를 허용하지 않는다.

### Orchestration and product surface

- [ ] 6. `review_null_spike()` orchestration과 typed failure boundary를 연결한다
  - **Covers:** Structured null-spike review input, Provider-compatible bounded invocation, Advisory and read-only boundary
  - **Test first:** Valid input의 input preflight → canonical projection → prompt → adapter → parse → deterministic validation → evidence persistence 순서와 `input_rejected`/`validation_failed`/`unavailable`/`provenance_failed` 결과를 fake adapter로 고정한다. `Incident`/`Evidence`/`RemediationDraft`/`RecoveryProposal`/`Approval`/database state snapshot을 전후 비교한다.
  - **Done when:**
    - `accepted` result만 structured output, accepted validation과 invocation evidence path/id를 반환한다.
    - Non-accepted result은 accepted output 또는 authority를 반환하지 않는다.
    - `input_rejected`는 provider/evidence를 만들지 않는다.
    - `run_incident_lifecycle()`은 자동 호출되지 않으며 어떤 review 경로도 approval, recovery, mutation을 수행하지 않는다.

- [ ] 7. Offline/integration public surface와 provider configuration 문서를 정렬한다
  - **Covers:** Deterministic and adversarial evaluation, Local and cloud-compatible configuration
  - **Test first:** Public export smoke test, fake-client integration, existing reliability regression과 network 없는 기본 pytest 실행을 고정한다.
  - **Done when:**
    - Reliability package가 새 contract, typed result, validator, settings, adapter와 store를 명시적으로 export한다.
    - `.env.example`, `docs/domains/reliability.md`와 `docs/development/testing.md`가 exact provider environment, secret 비저장, typed failure와 opt-in live proof를 설명한다.
    - 기존 deterministic lifecycle/recovery contract와 충돌하지 않는다.

### Live proof

- [ ] 8. Opt-in Ollama live invocation proof를 제공한다
  - **Covers:** Ollama live proof, Successful invocation provenance
  - **Test first:** 명시적 opt-in과 필수 endpoint/model configuration이 없을 때 default suite가 network 없이 유지되는지 고정한다. 설정이 있을 때 실제 response shape와 provenance assertions가 실행되는 별도 live command를 고정한다.
  - **Done when:**
    - `scripts/run_agentic_review_live.py` 또는 동등한 opt-in command가 실제 Ollama OpenAI-compatible endpoint에서 deterministic `null_spike` `Incident`/`Evidence`/`RemediationDraft`를 같은 adapter boundary로 검증한다.
    - Invocation JSON에 model/config, prompt identity/digest, `project_revision`, canonical input, structured output 또는 typed failure, validation, latency와 available usage가 남는다.
    - Approval/recovery/mutation은 발생하지 않는다.
