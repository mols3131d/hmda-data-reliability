## ADDED Requirements

### Requirement: Local provider response retention

Review AI는 Runtime이 반환한 bounded 응답 본문을 JSON 파싱 및 출력 검증 전에 `HMDA_RELIABILITY_ARTIFACTS_DIR/agentic-review/responses/<invocation_id>.txt`에 저장해야 한다(SHALL). 저장 내용은 응답 문자열의 UTF-8 바이트와 정확히 같아야 하며(SHALL), 개행 추가·공백 제거·JSON 재직렬화를 해서는 안 된다(MUST NOT). 빈 본문도 0-byte 파일로 남겨야 한다(SHALL).

응답 파일은 invocation별 create-only로 저장하고, 기존 response 또는 invocation identity를 덮어써서는 안 된다(MUST NOT). 결과는 저장한 파일의 `response_path`를 제공해야 한다(SHALL). 응답 저장 실패는 `provenance_failed / invocation_response_write_failed`로 종료하고 accepted output을 반환해서는 안 된다(MUST NOT). 응답 저장 후 invocation record 쓰기가 실패해도 회수 가능한 `response_path`는 유지해야 한다(SHALL).

로컬 응답은 검증을 통과한 review가 아니다. Schema/guard 실패의 status와 typed failure는 유지해야 한다(SHALL). 원문은 sanitized invocation JSON, 진단, 콘솔, logger 또는 Langfuse projection에 추가해서는 안 된다(MUST NOT). Provider가 본문을 반환하지 않은 실패와 input preflight에는 응답 경로를 생성해서는 안 된다(MUST NOT). 이전 응답 파일이 없는 record도 계속 읽을 수 있어야 한다(SHALL).

#### Scenario: Schema-invalid response remains inspectable

- **WHEN** Runtime이 잘린 JSON 또는 출력 계약을 위반한 유효 JSON을 반환할 때
- **THEN** 검증 전 응답 파일을 저장하고 validation_failed 결과의 response_path에서 원래 UTF-8 본문을 읽을 수 있어야 한다(SHALL).

#### Scenario: Accepted and guard-failed responses are retained

- **WHEN** Runtime 응답이 schema를 통과하고 사실 검증이 성공하거나 실패할 때
- **THEN** 각 status를 유지하면서 같은 방식의 원문 응답 파일 경로를 제공해야 한다(SHALL).

#### Scenario: Capture is bounded and create-only

- **WHEN** 응답이 설정된 UTF-8 byte 한도를 넘거나 identity가 이미 존재하거나 쓰기가 실패할 때
- **THEN** 기존 파일을 보존하고 accepted 결과를 차단하며 정제된 provenance failure를 반환해야 한다(SHALL).

#### Scenario: Invocation persistence fails after response capture

- **WHEN** 응답 파일 저장은 성공했지만 sanitized invocation record 쓰기가 I/O 오류로 실패할 때
- **THEN** provenance_failed 결과가 이미 저장된 response_path를 제공해야 한다(SHALL).

#### Scenario: Unavailable calls have no response file

- **WHEN** input preflight가 거부되거나 Runtime이 본문 없이 unavailable/oversized failure를 반환할 때
- **THEN** response_path는 null이어야 한다(SHALL).

## MODIFIED Requirements

### Requirement: Durable invocation evidence

Provider call이 실제로 시작된 각 logical `review_null_spike()` invocation은 하나의 immutable-by-identity `AgenticInvocationEvidence` record를 `HMDA_RELIABILITY_ARTIFACTS_DIR` 아래 `agentic-review/invocations/<invocation_id>.json`에 create-only로 저장해야 한다(SHALL). Network retry는 별도 record가 아니라 `attempt_count`로 기록해야 한다(SHALL). Input preflight에서 `input_rejected`로 종료된 call에는 provider invocation evidence를 만들지 않아야 한다. Directory 생성, 임시 파일 생성/쓰기/링크, fsync를 포함한 persistence 필수 과정의 filesystem failure는 raw exception을 탈출시키지 않고 `provenance_failed` result로 정규화해야 한다(SHALL). 성공적으로 기록된 후의 임시 파일 cleanup 실패는 accepted 결과에 영향을 주지 않는 best-effort hygiene으로 처리한다.

Record 계약은 다음과 같다.

| Category | Must retain |
| --- | --- |
| Identity and context | `invocation_id`, sanitized model/configuration, prompt identity/digest, caller-provided `project_revision`, incident/evidence references, provider user data의 source인 bounded `canonical_input` |
| Result | status, parsed structured output(가능한 경우), validation result 또는 typed failure code |
| Runtime | latency, attempt count, available token/usage/cost, available bounded response metadata and parse diagnosis |
| Safety | Sanitized JSON record에는 API key, credential, raw system/user prompt, raw log와 raw provider exception/response를 기록하지 않음. 응답 본문은 별도 로컬 response 파일에 보존 |

Stored `canonical_input`은 prompt renderer가 provider user data block을 만들 때 사용한 allowlisted structured projection과 같아야 한다(SHALL). Recorded `project_revision`에 해당하는 prompt implementation을 사용할 수 있을 때 `PromptIdentity`와 stored `canonical_input`으로 messages를 다시 render하면 stored `prompt_digest`와 일치해야 한다(SHALL). Raw rendered prompt를 replay 목적으로 저장해서는 안 된다(MUST NOT).

Sanitized record, stored `canonical_input`과 stored output은 configured size limit을 넘어서는 안 된다(SHALL).

#### Scenario: Successful invocation provenance

- **WHEN** local 또는 cloud-compatible provider가 schema-valid response를 반환하고 deterministic validation이 accepted이며 evidence store가 성공할 때
- **THEN** 저장된 invocation evidence에서 model/config, prompt identity/digest, `project_revision`, canonical input, incident/evidence refs, structured output, validation status, latency와 attempt count를 다시 확인할 수 있어야 한다.

#### Scenario: Invocation can be replayed without raw prompt storage

- **WHEN** stored `PromptIdentity`, `project_revision`와 `canonical_input`을 recorded application revision의 prompt implementation으로 다시 render할 때
- **THEN** 생성한 message digest는 stored `prompt_digest`와 일치해야 하고 raw rendered prompt를 provenance에 요구해서는 안 된다(MUST NOT).

#### Scenario: Failed invocation provenance

- **WHEN** provider가 unavailable이거나 response schema/guard validation에 실패할 때
- **THEN** invocation evidence는 canonical input, 실패 status, typed failure reason, attempt/latency와 가능한 structured output을 보존해야 하며 secret과 raw prompt/log/provider error를 포함해서는 안 된다.

#### Scenario: Evidence persistence failure

- **WHEN** invocation result의 directory 생성 실패, 권한 오류 또는 I/O failure로 인해 durable evidence로 저장할 수 없을 때
- **THEN** 시스템은 raw exception 탈출 없이 `provenance_failed` result를 반환하고 accepted review, approval, recovery 또는 mutation을 수행해서는 안 된다(MUST NOT).

#### Scenario: Invocation evidence is immutable by identity

- **WHEN** 이미 사용된 `invocation_id`로 다른 invocation evidence를 덮어쓰려 하거나 동시 create가 충돌할 때
- **THEN** 시스템은 overwrite를 거부하고 기존 evidence를 보존하며 두 번째 call을 `provenance_failed`로 반환해야 한다.

### Requirement: Advisory and read-only boundary

> **Read-only guarantee:** Review가 수행할 수 있는 filesystem mutation은 로컬 invocation evidence와 응답 파일의 create-only write다.

시스템은 `accepted`, `validation_failed`, `unavailable`, `input_rejected` 또는 `provenance_failed` Agentic review 어느 경우에도 `Incident` truth, `Evidence`, `RemediationDraft`, `RecoveryProposal`, `Approval`, recovery state 또는 data/database state를 변경해서는 안 된다(MUST NOT). Review 결과와 free-text wording은 사람의 판단을 돕는 advisory output이며 model output만으로 approval, recovery 또는 mutation을 유발해서는 안 된다(MUST NOT).

#### Scenario: Accepted review does not mutate reliability state

- **WHEN** valid `null_spike` review가 accepted되고 invocation evidence가 저장될 때
- **THEN** `Incident`, `Evidence`, `RemediationDraft`와 recovery/approval state 및 target data는 호출 전과 같아야 하고 invocation evidence와 응답 파일 저장 외의 mutation이 없어야 한다.

#### Scenario: Action-like advisory remains non-executable

- **WHEN** structured validation을 통과한 accepted review가 action 또는 approval처럼 읽힐 수 있는 free text를 포함할 때
- **THEN** 시스템은 typed `Approval`, exact `RecoveryProposal` 또는 mutation request를 생성하거나 recovery executor를 호출해서는 안 된다(MUST NOT).

#### Scenario: Rejected or unavailable review remains contained

- **WHEN** fabricated Evidence, canonical contradiction, schema failure, provider unavailability 또는 provenance failure가 발생할 때
- **THEN** 시스템은 해당 review를 typed result와 evidence로 격리하고 deterministic Reliability 결과와 target data를 보존하며 recovery authority를 부여해서는 안 된다(MUST NOT).
