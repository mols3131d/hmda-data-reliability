---
type: openspec-spec-driven-tdd-spec
category: spec
title: reliability-agentic-review
description: "deterministic null_spike evidence를 근거로 제한된 advisory review를 생성하고 검증하며 invocation provenance를 보존한다."
tags:
  - "capability:reliability-agentic-review"
---

## Purpose

> **핵심 경계:** `null_spike`의 deterministic truth와 제공된 Evidence가 review의 기준이다. LLM은 advisory output만 만들며, `accepted` 결과도 deterministic validation과 durable provenance를 모두 통과해야 한다.

이 Change는 deterministic `Incident`, 실제 `Evidence`와 `RemediationDraft`를 LLM이 검토하더라도 결과가 canonical facts와 제공된 근거에 묶이고 advisory 경계를 넘지 않도록 한다. 각 provider 결과와 실패는 재현 가능한 evidence로 남긴다.

## ADDED Requirements

### Requirement: Structured null-spike review input

시스템은 `null_spike` `Incident`, 실제 제공된 하나 이상의 `Evidence`, 기존 `RemediationDraft`, `PromptIdentity`와 caller가 제공한 non-empty `project_revision`을 보존하는 call-scoped snapshot `AgenticReviewInput`을 받아야 한다(SHALL). Snapshot 생성 뒤 caller가 보유한 nested list 또는 mapping을 변경해도 prompt, validation과 provenance에 사용되는 input은 변하지 않아야 한다(SHALL).

Input은 다음 invariant를 모두 만족할 때만 provider review 대상으로 인정해야 한다(SHALL).

- **Incident and draft identity:** `incident.incident_type`와 `draft.incident_type`는 정확히 `null_spike`이고, incident와 draft의 `incident_id`, `asset_name`과 `partition`이 일치한다.
- **Evidence linkage:** 제공된 Evidence ID는 unique하고 `incident.evidence_refs` 및 `draft.evidence_refs`와 같은 set이다. 각 Evidence의 `evidence_id`, `asset_name`과 `partition`은 incident와 일치한다.
- **Canonical target:** 정확히 하나의 canonical target Evidence가 있어야 한다. 이 Evidence는 `source=profile`, `payload.rule=null_spike`, non-empty string `column`, finite numeric `baseline_null_rate`, `current_null_rate`, `delta`와 `threshold`를 가져야 한다. Target column과 numeric facts는 이 Evidence에서만 유도한다.
- **Prompt metadata:** `PromptIdentity`는 `template_id=reliability-agentic-review.null-spike`, `version=v1`이어야 하고, Evidence payload는 canonical JSON으로 표현 가능해야 한다.

이 Change의 review entry point는 `null_spike` 외 incident type을 지원해서는 안 된다(MUST NOT).

#### Scenario: Valid evidence-bound input

- **WHEN** 위의 identity 관계, complete Evidence set, unique canonical target Evidence, `PromptIdentity`와 `project_revision`을 만족하는 `null_spike` 입력이 제공될 때
- **THEN** 시스템은 snapshot `AgenticReviewInput`을 만들고 provider invocation을 진행할 수 있어야 한다.

#### Scenario: Mismatched input is rejected before invocation

- **WHEN** Evidence가 incident 또는 draft의 reference set에서 누락되거나 incident/draft의 identity, type, asset 또는 partition이 다를 때
- **THEN** 시스템은 `input_rejected` result를 반환하고 provider invocation 또는 invocation evidence 생성을 수행해서는 안 된다(MUST NOT).

#### Scenario: Invalid canonical target evidence

- **WHEN** canonical target Evidence가 없거나 둘 이상이거나 rule, column 또는 required numeric fact가 없거나 non-finite일 때
- **THEN** 시스템은 `input_rejected` result를 반환하고 provider invocation을 수행해서는 안 된다(MUST NOT).

#### Scenario: Unsupported incident type

- **WHEN** `volume_drop`, `schema_drift` 또는 `freshness_delay` Incident를 이 Change의 review entry point에 제공할 때
- **THEN** 시스템은 명시적인 `input_rejected` result를 반환하고 provider invocation, approval 또는 recovery를 수행해서는 안 된다(MUST NOT).

### Requirement: Structured advisory review output

시스템은 provider response를 다음 immutable `AgenticReviewOutput`으로 표현해야 한다(SHALL).

- **Identity:** `incident_id`, `incident_type`, `target_column`
- **Deterministic facts:** canonical target Evidence의 `baseline_null_rate`, `current_null_rate`, `delta`와 `threshold`를 복사한 `NullSpikeFacts` 형태의 `deterministic_facts`
- **Review content:** non-empty `review_summary`, 하나 이상의 `evidence_used`, `findings`와 `uncertainties`
- **Recommendation:** `support`, `needs_human_review`, `insufficient_evidence` 중 하나인 `advisory_recommendation`

Output invariant는 다음과 같다.

- 각 finding의 `kind`는 `observation`, `concern`, `omission` 또는 `uncertainty` 중 하나이고, non-empty `description`과 optional `evidence_refs`를 가져야 한다(SHALL).
- Output은 `extra=forbid`에 해당하는 closed shape여야 한다.
- Approval, `RecoveryProposal`, recovery, shell, SQL, file, database 또는 data mutation action을 명령하거나 부여하는 field를 제공해서는 안 된다(MUST NOT).
- Text와 collection은 configured bounded limit을 넘어서는 안 된다(SHALL).

#### Scenario: Valid advisory response

- **WHEN** provider가 input identity, canonical target column과 deterministic facts를 보존하고 실제 Evidence reference를 사용하는 response를 반환할 때
- **THEN** 시스템은 summary, finding/concern, uncertainty와 advisory recommendation을 structured output으로 parse할 수 있어야 한다.

#### Scenario: Invalid response shape

- **WHEN** response에 required field가 없거나 허용되지 않은 field, 허용되지 않은 finding kind/recommendation, 빈 summary 또는 canonical facts가 포함되지 않을 때
- **THEN** 시스템은 `validation_failed` result를 반환하고 response를 accepted review로 노출해서는 안 된다(MUST NOT).

### Requirement: Deterministic review validation

시스템은 parsed model output을 외부 action 또는 accepted advisory result로 사용하기 전에 deterministic validator로 `AgenticReviewInput`과 대조해야 한다(SHALL). Validator는 identity, canonical target column, `deterministic_facts`, `evidence_used`와 finding `evidence_refs`를 비교하고 다음 minimum violation code를 사용해야 한다(SHALL).

| Violation code | 생성 조건 |
| --- | --- |
| `fabricated_evidence` | Input에 제공되지 않은 Evidence ID가 `evidence_used` 또는 finding reference에 포함됨 |
| `incident_mismatch` | Incident ID 또는 type이 input과 다름 |
| `deterministic_contradiction` | Target column 또는 canonical numeric facts가 input과 다름 |
| `authority_escalation` | Output이 approval을 부여하거나 model output만으로 권한이 생겼다고 주장함 |
| `forbidden_action` | Recovery, backfill execution, shell/SQL/file/database/data mutation 실행을 명령함 |

Violation code는 중복 없이 deterministic order로 반환해야 하며, 하나라도 있으면 validation status는 rejected여야 한다(MUST NOT).

Action policy는 `forbidden-action-policy-v1`로 식별해야 한다(SHALL). 단순히 draft의 action을 인용하거나 backfill을 human approval이 필요한 항목으로 설명하는 것은 violation이 아니다. Output이 approval을 부여하거나 실행을 명령·주장할 때만 각각 `authority_escalation` 또는 `forbidden_action`을 생성해야 한다(SHALL).

#### Scenario: Fabricated evidence is rejected

- **WHEN** schema-valid output이 input에 제공되지 않은 `evidence_id`를 `evidence_used` 또는 finding reference로 포함할 때
- **THEN** validator는 `fabricated_evidence` violation을 포함한 rejected result를 반환하고 output을 accepted advisory result로 채택해서는 안 된다(MUST NOT).

#### Scenario: Identity or canonical fact contradiction is rejected

- **WHEN** output의 `incident_id`, `incident_type`, `target_column` 또는 `deterministic_facts`가 input의 deterministic facts와 다를 때
- **THEN** validator는 `incident_mismatch` 또는 `deterministic_contradiction` violation을 반환하고 model 주장을 deterministic Reliability 결과보다 우선해서는 안 된다(MUST NOT).

#### Scenario: Schema-valid dangerous output is rejected

- **WHEN** schema-valid output이 approval, `RecoveryProposal`, recovery, backfill execution, shell/SQL/file/database/data mutation을 수행하라고 명령하거나 model output만으로 권한이 생겼다고 주장할 때
- **THEN** validator는 `authority_escalation` 또는 `forbidden_action` violation을 반환하고 output을 외부 action에 전달해서는 안 된다(MUST NOT).

#### Scenario: Descriptive draft action is not itself forbidden

- **WHEN** output이 `RemediationDraft`의 backfill 또는 validation action을 human approval이 필요한 draft 내용으로 설명하지만 실행을 명령하거나 authority를 주장하지 않을 때
- **THEN** validator는 그 단어만으로 `forbidden_action` 또는 `authority_escalation`을 생성해서는 안 된다(MUST NOT).

#### Scenario: Safe advisory output is accepted

- **WHEN** output이 input identity와 canonical facts를 보존하고 실제 Evidence subset을 사용하며 violation을 포함하지 않을 때
- **THEN** validator는 accepted result를 반환하되 승인·복구 권한이나 data mutation 권한을 생성해서는 안 된다(MUST NOT).

### Requirement: Typed review result boundary

시스템은 review call의 결과를 다음 중 하나의 status를 가진 typed `AgenticReviewResult`로 반환해야 한다(SHALL).

| Status | 의미와 반환 경계 |
| --- | --- |
| `accepted` | Parsed output, accepted validation과 durable invocation evidence identity/path가 모두 존재할 때만 허용 |
| `validation_failed` | Schema 또는 deterministic guard 실패 |
| `unavailable` | Bounded transport failure |
| `input_rejected` | Provider call 전의 input preflight 실패. Provider와 invocation evidence를 만들지 않음 |
| `provenance_failed` | Provider 결과를 durable evidence로 보존하지 못함 |

Non-accepted result의 output은 비어 있어야 한다. Parsed output이 있더라도 invocation evidence 내부에서만 진단 목적으로 보존할 수 있다(SHALL). Accepted output, approval, recovery 또는 mutation authority는 non-accepted status에서 반환해서는 안 된다(MUST NOT).

#### Scenario: Accepted result requires validation and provenance

- **WHEN** provider response가 schema parse와 deterministic validation을 통과하고 invocation evidence가 create-only로 저장될 때
- **THEN** 시스템은 accepted result와 output 및 invocation evidence identity/path를 반환해야 한다.

#### Scenario: Validation failure is contained

- **WHEN** schema parse 또는 deterministic guard가 실패할 때
- **THEN** 시스템은 `validation_failed` result를 반환하고 accepted output, approval, recovery 또는 mutation authority를 반환해서는 안 된다(MUST NOT).

#### Scenario: Provider unavailability is typed

- **WHEN** timeout, connection failure 또는 bounded retry 이후 provider unavailable 상태가 될 때
- **THEN** 시스템은 `unavailable` result를 반환하고 accepted output, approval, recovery 또는 mutation authority를 생성해서는 안 된다(MUST NOT).

#### Scenario: Provenance failure blocks acceptance

- **WHEN** provider result가 있었지만 invocation evidence를 durable하게 저장할 수 없을 때
- **THEN** 시스템은 `provenance_failed` result를 반환하고 accepted output, approval, recovery 또는 mutation authority를 반환해서는 안 된다(MUST NOT).

### Requirement: Provider-compatible bounded invocation

시스템은 동일한 review contract와 configuration boundary를 사용해 OpenAI-compatible `chat.completions` endpoint를 제공하는 local Ollama model과 OpenAI API를 호출할 수 있어야 한다(SHALL). Provider 차이는 `base_url`, credential, model과 bounded configuration으로 표현해야 하며 Reliability domain의 incident/evidence/recovery code가 provider별 business rule을 소유해서는 안 된다(MUST NOT).

이 Change의 common wire profile은 다음 조건을 만족해야 한다(SHALL).

| Request / behavior | Contract |
| --- | --- |
| Response | Non-streaming JSON object |
| Sampling | `temperature=0` |
| Token limit | Domain `max_output_tokens`를 wire `max_tokens`로 매핑 |
| Tools and stream | `stream=false`, no-tools |
| Retry | 유한한 timeout과 `max_retries` 이하의 transport retry만 허용 |
| No-retry cases | SDK hidden retry, schema failure, guard failure와 client 4xx retry 금지 |

#### Scenario: Local and cloud-compatible configuration

- **WHEN** 같은 `AgenticReviewInput`에 Ollama의 OpenAI-compatible base URL 또는 OpenAI base URL과 각각의 model/credential을 설정할 때
- **THEN** 시스템은 동일한 review adapter boundary에서 common wire profile request를 만들고 provider-specific Reliability/domain code 변경 없이 structured response를 검증해야 한다.

#### Scenario: Provider timeout or unavailability

- **WHEN** configured endpoint가 timeout, connection failure 또는 bounded retry 이후 unavailable 상태를 반환할 때
- **THEN** 시스템은 unavailable invocation result와 failure provenance를 반환하고 review output, approval, recovery 또는 mutation authority를 생성해서는 안 된다(MUST NOT).

#### Scenario: Provider returns schema-invalid content

- **WHEN** provider가 HTTP-level success를 반환했지만 JSON 또는 `AgenticReviewOutput`으로 검증할 수 없는 content를 반환할 때
- **THEN** 시스템은 validation_failed result와 failure provenance를 반환하고 accepted advisory review 또는 외부 action을 반환해서는 안 된다(MUST NOT).

### Requirement: Durable invocation evidence

Provider call이 실제로 시작된 각 logical `review_null_spike()` invocation은 하나의 immutable-by-identity `AgenticInvocationEvidence` record를 `HMDA_RELIABILITY_ARTIFACTS_DIR` 아래 `agentic-review/invocations/<invocation_id>.json`에 create-only로 저장해야 한다(SHALL). Network retry는 별도 record가 아니라 `attempt_count`로 기록해야 한다(SHALL). Input preflight에서 `input_rejected`로 종료된 call에는 provider invocation evidence를 만들지 않아야 한다.

Record 계약은 다음과 같다.

| Category | Must retain |
| --- | --- |
| Identity and context | `invocation_id`, sanitized model/configuration, prompt identity/digest, caller-provided `project_revision`, incident/evidence references |
| Result | status, parsed structured output(가능한 경우), validation result 또는 typed failure code |
| Runtime | latency, attempt count, available token/usage/cost |
| Safety | API key, credential, raw prompt, raw log와 raw provider exception/response는 기록하지 않음 |

Sanitized record와 stored output은 configured size limit을 넘어서는 안 된다(SHALL).

#### Scenario: Successful invocation provenance

- **WHEN** local 또는 cloud-compatible provider가 schema-valid response를 반환하고 deterministic validation이 accepted이며 evidence store가 성공할 때
- **THEN** 저장된 invocation evidence에서 model/config, prompt identity/digest, `project_revision`, incident/evidence refs, structured output, validation status, latency와 attempt count를 다시 확인할 수 있어야 한다.

#### Scenario: Failed invocation provenance

- **WHEN** provider가 unavailable이거나 response schema/guard validation에 실패할 때
- **THEN** invocation evidence는 실패 status, typed failure reason, attempt/latency와 가능한 structured output을 보존해야 하며 secret과 raw prompt/log/provider error를 포함해서는 안 된다.

#### Scenario: Evidence persistence failure

- **WHEN** invocation result를 durable evidence로 저장할 수 없을 때
- **THEN** 시스템은 `provenance_failed` result를 반환하고 accepted review, approval, recovery 또는 mutation을 수행해서는 안 된다(MUST NOT).

#### Scenario: Invocation evidence is immutable by identity

- **WHEN** 이미 사용된 `invocation_id`로 다른 invocation evidence를 덮어쓰려 하거나 동시 create가 충돌할 때
- **THEN** 시스템은 overwrite를 거부하고 기존 evidence를 보존하며 두 번째 call을 `provenance_failed`로 반환해야 한다.

### Requirement: Advisory and read-only boundary

> **Read-only guarantee:** Review가 반환할 수 있는 유일한 filesystem mutation은 invocation evidence의 create-only write다.

시스템은 `accepted`, `validation_failed`, `unavailable`, `input_rejected` 또는 `provenance_failed` Agentic review 어느 경우에도 `Incident` truth, `Evidence`, `RemediationDraft`, `RecoveryProposal`, `Approval`, recovery state 또는 data/database state를 변경해서는 안 된다(MUST NOT). Review 결과는 사람의 판단을 돕는 advisory output이며 model output만으로 approval, recovery 또는 mutation을 유발해서는 안 된다(MUST NOT).

#### Scenario: Accepted review does not mutate reliability state

- **WHEN** valid `null_spike` review가 accepted되고 invocation evidence가 저장될 때
- **THEN** `Incident`, `Evidence`, `RemediationDraft`와 recovery/approval state 및 target data는 호출 전과 같아야 하고 invocation evidence 저장 외의 mutation이 없어야 한다.

#### Scenario: Rejected or unavailable review remains contained

- **WHEN** fabricated evidence, prompt injection, authority escalation, schema failure, provider unavailability 또는 provenance failure가 발생할 때
- **THEN** 시스템은 해당 review를 typed result와 evidence로 격리하고 deterministic Reliability 결과와 target data를 보존하며 recovery authority를 부여해서는 안 된다(MUST NOT).

### Requirement: Deterministic and adversarial evaluation

시스템은 provider network call 없이 input/output contract, typed result와 validator를 반복 평가할 수 있어야 하며(SHALL), `null_spike` 기준으로 valid response, fabricated evidence, canonical fact mismatch, direct/indirect prompt injection, authority escalation, descriptive draft action, schema-invalid response와 provider unavailability를 포함한 adversarial fixture를 다뤄야 한다(SHALL). 적어도 하나의 local Ollama live invocation은 default suite와 분리된 opt-in path에서 같은 contract와 provenance 경계를 사용해 검증할 수 있어야 한다(SHALL).

| Evaluation path | Network | Required coverage |
| --- | --- | --- |
| Offline default suite | 사용하지 않음 | Input/output contract, typed result, validator와 adversarial fixture |
| Opt-in Ollama live proof | 명시적으로 활성화한 경우에만 사용 | 실제 response, common adapter와 invocation provenance |

#### Scenario: Offline contract and guard evaluation

- **WHEN** fake/stub response와 adversarial fixture를 provider 호출 없이 반복 검증할 때
- **THEN** 같은 fixture는 같은 status와 violation code를 생성해야 하고 input의 원문 Evidence, deterministic result와 target state를 변경해서는 안 된다.

#### Scenario: Prompt injection is data, not instruction

- **WHEN** Evidence summary/payload 또는 provider output에 direct/indirect prompt injection 문장이 포함될 때
- **THEN** 시스템은 그 문장을 Reliability instruction으로 실행하거나 권한으로 승격하지 않고 data로만 전달하거나 validation violation으로 처리해야 한다(MUST NOT).

#### Scenario: Ollama live proof

- **WHEN** opt-in live proof가 명시적으로 활성화되고 configured Ollama OpenAI-compatible endpoint가 접근 가능하며 deterministic `null_spike` `Incident`/`Evidence`/`RemediationDraft`가 제공될 때
- **THEN** 실제 model response가 `AgenticReviewOutput`과 deterministic validator를 통과하거나 typed failure로 종료되고, invocation evidence에 model/config, prompt identity/digest, `project_revision`, output 또는 failure reason, validation, latency와 available usage가 남아야 한다.
