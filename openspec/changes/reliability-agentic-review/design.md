---
type: openspec-spec-driven-tdd-design
category: design
title: "Bounded agentic review design"
description: "기존 Reliability truth와 approval boundary를 보존하면서 null_spike review contract, typed result, OpenAI-compatible adapter와 invocation evidence를 분리한다."
---

## Design Summary

> **실행 경계:** `review_null_spike()`는 read-only input snapshot을 만든 뒤 provider를 호출하고, response를 parse·validate한 다음 invocation evidence를 저장한다. Input preflight가 실패하면 `input_rejected`를 반환하고 provider와 evidence store를 호출하지 않는다.

## Approach

`reliability/agentic_review/`를 기존 detection, impact, remediation과 나란히 두는 별도 read-only surface로 추가한다. `AgenticReviewInput`은 기존 `Incident`, `Evidence`와 `RemediationDraft`의 call-scoped snapshot, `PromptIdentity`와 caller-provided `project_revision`을 보존한다.

`review_null_spike()`의 처리 순서는 다음과 같다.

1. **Input preflight:** identity, Evidence linkage, canonical target Evidence와 prompt metadata를 검증한다.
1. **Canonical projection:** allowlisted fields만 canonical JSON data block으로 만든다.
1. **Provider call:** bounded OpenAI-compatible adapter로 non-streaming response를 받는다.
1. **Parse and validate:** response schema와 deterministic safety rules를 검사한다.
1. **Persist and return:** logical invocation evidence를 저장하고 typed result를 반환한다.

Provider SDK, prompt formatting, deterministic guard와 filesystem persistence는 서로 분리한다. 실제 SDK는 하나의 OpenAI-compatible adapter 뒤에 두고, test에서는 같은 adapter protocol에 fake client를 주입한다. 어떤 경로도 approval/recovery/mutation API를 호출하지 않는다.

## Boundaries

| Boundary | Owns | Does Not Own |
| --- | --- | --- |
| **Deterministic Reliability** | `Incident`, `Evidence`, `RemediationDraft`의 identity와 null-spike canonical facts 제공 | LLM 해석, provider 선택, approval 결정 |
| **Agentic Review contract/validator** | input/output schema, typed result, evidence subset, canonical fact 비교와 action guard | incident 탐지, RCA truth 변경, action 실행 |
| **OpenAI-compatible adapter** | SDK client, common `chat.completions` request/response, timeout과 bounded transport retry | provider별 business rule, recovery 또는 mutation |
| **Invocation Evidence Store** | sanitized provenance JSON serialization, logical invocation identity와 create-only write | raw prompt/log/provider error 보존, canonical reliability state 변경 |
| **Approval / Recovery** | 기존 exact proposal과 external approval 이후의 state mutation | Agentic output 해석과 invocation 실행 |

## Decisions

### D1. Use snapshots and one canonical null-spike target fact

#### D1 Decision

- `AgenticReviewInput`은 `Incident`, `Evidence` collection, `RemediationDraft`, `PromptIdentity`와 `project_revision`을 보존한다.
- Input 생성 시 nested collection/mapping을 deep snapshot하고, Evidence ID set을 Incident 및 Draft reference set과 exact match시킨다.
- Required rule, column과 numeric facts를 가진 `source=profile`의 `null_spike` Evidence는 정확히 하나만 허용한다. 이 Evidence의 `baseline_null_rate`, `current_null_rate`, `delta`, `threshold`를 `NullSpikeFacts` 형태의 canonical target fact로 사용한다.

#### D1 Rationale

기존 detector의 Evidence payload가 target column과 `baseline/current/delta/threshold`를 제공하므로 model이 target을 새로 결정하지 않게 한다. Caller가 이후 객체를 변경해도 prompt, validator와 provenance가 서로 다른 input을 보지 않게 한다.

#### D1 Trade-off

첫 slice는 단일 incident type과 하나의 canonical target Evidence에 한정된다. 여러 target 또는 다른 incident type은 별도 contract가 필요하다.

### D2. Return an explicit typed result

#### D2 Decision

Public orchestration은 `accepted`, `validation_failed`, `unavailable`, `input_rejected`와 `provenance_failed`를 `AgenticReviewResult` status로 사용한다. `accepted`는 parsed `AgenticReviewOutput`, accepted validation과 durable invocation evidence identity/path가 모두 있을 때만 반환한다.

Non-accepted result는 output을 advisory output으로 노출하지 않는다. Parsed output이 있더라도 invocation evidence 내부의 진단 정보로만 보존한다.

#### D2 Rationale

Schema failure, guard rejection, network failure와 observability failure를 하나의 rejected 값으로 합치면 caller가 재시도·조사·사람 검토를 구분할 수 없다.

#### D2 Trade-off

Guard-rejected response는 진단을 위해 invocation evidence에 저장될 수 있지만, public accepted output으로 재사용할 수 없다.

### D3. Use one common chat.completions wire profile

#### D3 Decision

`AgenticReviewSettings`는 explicit `base_url`, `SecretStr api_key`, `model`과 다음 bounded defaults를 갖는다.

| Setting | Default |
| --- | ---: |
| `timeout_seconds` | `30` |
| `max_retries` | `1` |
| `temperature` | `0` |
| `max_output_tokens` | `1024` |
| `max_prompt_bytes` | `65536` |
| `max_output_bytes` | `32768` |

Adapter는 `max_output_tokens`를 common wire field `max_tokens`로 매핑한다. Request는 non-streaming JSON object response, `stream=false`와 no-tools만 사용한다. OpenAI SDK client는 `max_retries=0`으로 만들며 adapter가 timeout/connection과 HTTP 5xx만 `max_retries` 이하로 재시도한다.

#### D3 Rationale

OpenAI와 Ollama가 공통으로 제공하는 가장 작은 `chat.completions` request를 고정하고 SDK hidden retry와 provider-specific domain branching을 제거한다. Domain 설정 이름과 wire protocol 이름을 분리해 향후 다른 compatibility profile을 추가할 여지를 남긴다.

#### D3 Trade-off

`max_tokens` common profile을 지원하지 않는 model은 이 slice의 configured model로 사용할 수 없다. `max_completion_tokens`만 필요한 model profile은 후속 Change에서 별도로 검증한다.

### D4. Render an allowlisted canonical data projection

#### D4 Decision

Prompt renderer는 다음 allowlisted fields만 canonical JSON data block으로 전달한다.

| Source | Fields |
| --- | --- |
| `Incident` | identity, type, asset, partition, status, severity |
| All `Evidence` | id, source, asset, partition, `observed_at`, summary, payload |
| `RemediationDraft` | identity, RCA, evidence refs, affected assets, action suggestions, `requires_approval` |
| Review facts | `deterministic_facts` |

System instruction과 user data를 분리하고 key order, separators와 UTF-8 encoding을 고정한다. `prompt_digest`는 실제 system/user messages의 SHA-256이며 raw prompt는 저장하지 않는다.

#### D4 Rationale

Review에 필요한 structured context는 보존하면서 불필요한 runtime object와 raw log를 provider와 provenance에 복제하지 않는다. Data block 안의 명령문은 항상 untrusted data로 남는다.

#### D4 Trade-off

Digest만으로 prompt를 복원할 수 없으므로 versioned fixture, input refs와 `project_revision`이 replay context를 제공해야 한다. Rendered prompt가 `max_prompt_bytes`를 넘으면 provider 전에 `input_rejected`로 종료한다.

### D5. Make the validator a provider-independent safety oracle

#### D5 Decision

순수 validator는 identity, target column, `deterministic_facts`와 Evidence reference set을 비교하고 violation code를 stable lexicographic order로 반환한다. `forbidden-action-policy-v1`은 authority claim과 실제 action execution instruction을 구분한다.

Draft action의 descriptive mention은 허용한다. Approval 부여, recovery 실행, shell/SQL/file/database/data mutation 명령만 차단한다.

#### D5 Rationale

Pydantic schema validity는 evidence binding이나 authority safety를 증명하지 않는다. Provider와 무관한 동일 oracle이 필요하며, 자연어 의미 전체를 보장한다고 과장하지 않아야 한다.

#### D5 Trade-off

정적 policy는 모든 자연어 공격을 탐지하는 semantic judge가 아니다. 따라서 execution path를 제공하지 않는 read-only boundary와 adversarial fixture를 함께 유지한다.

### D6. Store one create-only record per logical provider call

#### D6 Decision

Provider call이 시작된 logical `review_null_spike()` 호출마다 UUID `invocation_id` 하나를 생성한다. Retry는 `attempt_count`로 집계한다. Record에는 다음 정보를 저장한다.

- status, typed failure code와 parsed output(가능한 경우)
- validation, sanitized config, prompt identity/digest와 `project_revision`
- Incident/Evidence refs, latency, usage와 optional `trace_id`

Storage path는 `HMDA_RELIABILITY_ARTIFACTS_DIR` 또는 `.local/artifacts` 아래 `agentic-review/invocations/<invocation_id>.json`이다.

#### D6 Rationale

Retry마다 별도 identity를 만들지 않아 한 review의 결과와 비용을 한 provenance record에서 replay할 수 있다. Input preflight는 provider call이 아니므로 record를 만들지 않는다.

#### D6 Trade-off

Local filesystem store는 distributed audit log, encryption과 retention policy를 제공하지 않는다. Create-only write는 exclusive create와 atomic complete write로 구현하고 collision은 `provenance_failed`로 처리한다.

### D7. Keep configuration explicit and live proof opt-in

#### D7 Decision

Public review API는 environment를 암묵적으로 읽지 않고 `AgenticReviewSettings`를 명시적으로 받는다. Live harness의 환경 변수 이름은 다음으로 고정한다.

- `HMDA_RELIABILITY_AGENTIC_BASE_URL`
- `HMDA_RELIABILITY_AGENTIC_API_KEY`
- `HMDA_RELIABILITY_AGENTIC_MODEL`
- `HMDA_RELIABILITY_AGENTIC_TIMEOUT_SECONDS`
- `HMDA_RELIABILITY_AGENTIC_MAX_RETRIES`
- `HMDA_RELIABILITY_AGENTIC_MAX_OUTPUT_TOKENS`

Live proof는 명시적 opt-in command에서만 실행한다.

#### D7 Rationale

기본 pytest가 credential이나 network 상태에 의존하지 않게 하고, provider 설정과 deterministic Reliability code를 분리한다.

#### D7 Trade-off

Live proof의 model 품질과 availability는 CI correctness를 보장하지 않는다. Live evidence는 해당 실행 revision의 별도 observation으로 다룬다.

## Verification

- **Contracts:** Snapshot/input/output/result contract, bounded fields, `extra=forbid`, frozen semantics와 canonical fact invariant를 network 없이 확인한다.
- **Validator:** Evidence subset, identity/fact mismatch, action-policy mapping, safe descriptive action과 prompt-injection data handling을 반복 실행해 stable status/code를 확인한다.
- **Adapter:** Fake client로 canonical messages, prompt digest, `max_tokens` wire mapping, JSON response parsing, no-tools, timeout/5xx retry와 4xx/schema no-retry를 확인한다.
- **Evidence store:** Temporary artifact root에 logical success, validation failure, unavailable와 collision record를 쓰고 JSON reload, sanitized fields, attempt/latency/usage와 create-only semantics를 확인한다.
- **Integration:** Existing detector fixture와 deterministic `RemediationDraft`를 조합해 accepted 및 각 typed failure 전후 `Incident`, `Evidence`, Draft, `RecoveryProposal`, `Approval`과 target state snapshot이 같은지 확인한다.
- **Opt-in live proof:** Configured Ollama endpoint에 실제 call을 보내 common adapter와 provenance record를 확인한다. Default suite는 network와 credential을 사용하지 않는다.

## Risks

- **Ungrounded output:** LLM이 그럴듯하지만 근거 밖의 내용을 만들 수 있다. Canonical facts와 Evidence reference subset을 model output에서 다시 검증하고 deterministic truth를 우선한다.
- **Prompt injection:** Evidence 또는 model output에 prompt injection이 포함될 수 있다. Canonical data block으로 전달하고 execution interface를 제공하지 않으며 action intent만 policy로 차단한다.
- **Provider drift:** OpenAI와 Ollama의 model별 parameter 차이가 생길 수 있다. Common `max_tokens` profile을 계약하고 unsupported model은 typed configuration/provider failure로 종료한다.
- **Provenance leakage:** Invocation provenance가 secret 또는 민감한 raw content를 누출할 수 있다. Config allowlist, bounded output, typed failure code와 raw prompt/log/provider error 금지를 함께 적용한다.
- **Live availability:** Live provider가 없거나 model output이 schema-invalid일 수 있다. Live proof를 opt-in으로 분리하고 offline contract/guard suite를 독립적으로 유지한다.

## Migration

1. `openai` runtime dependency와 `uv.lock`을 추가하고, 기존 deterministic test path가 SDK network 없이 동작하는지 확인한다.
1. `HMDA_RELIABILITY_ARTIFACTS_DIR` convention을 재사용하고 `agentic-review/invocations` 경로에 create-only JSON evidence를 추가한다. `.env.example`에는 secret-free provider placeholder와 opt-in 환경 변수만 문서화한다.
1. `docs/domains/reliability.md`와 `docs/development/testing.md`에 Agentic review public surface, typed result, safety boundary와 live proof command를 추가한다.
1. 현재 lifecycle, `RecoveryProposal`, `Approval`과 recovery API는 수정하지 않는다. 구현·검증 후 `reliability-agentic-review` canonical Spec을 archive workflow로 반영한다.
