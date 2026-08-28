---
type: openspec-spec-driven-tdd-spec
category: spec
title: "Reliability Agentic Review"
description: "Agentic review validation을 structured fact consistency에 한정하고 advisory output과 mutation authority를 분리합니다."
tags:
  - "capability:reliability-agentic-review"
---

## ADDED Requirements

### Requirement: Versioned validation provenance compatibility

새 invocation의 validation result는 `structured-fact-validation-v1` policy identity를 사용해야 한다(SHALL). 시스템은 이미 저장된 `forbidden-action-policy-v1` invocation evidence와 그 policy가 생성한 `authority_escalation`, `forbidden_action` violation을 historical provenance로 읽을 수 있어야 한다(SHALL). Legacy policy identity와 violation은 새 validation 결과에 생성되어서는 안 되며(MUST NOT), current acceptance policy 또는 authority boundary로 해석되어서는 안 된다(MUST NOT).

#### Scenario: Legacy accepted evidence remains readable

- **GIVEN** `forbidden-action-policy-v1`과 빈 violation 목록을 가진 기존 accepted invocation evidence가 저장되어 있을 때
- **WHEN** current evidence reader가 해당 record를 load할 때
- **THEN** historical validation policy, status와 provenance를 보존한 typed evidence로 읽을 수 있어야 한다.

#### Scenario: Legacy natural-language rejection remains readable

- **GIVEN** `forbidden-action-policy-v1`과 `authority_escalation` 또는 `forbidden_action` violation을 가진 기존 validation-failed evidence가 저장되어 있을 때
- **WHEN** current evidence reader가 해당 record를 load할 때
- **THEN** historical violation을 current structured-fact violation으로 바꾸지 않고 원래 policy 결과로 읽을 수 있어야 한다.

#### Scenario: New evidence uses only the current policy

- **WHEN** current validator result가 새 invocation evidence에 저장될 때
- **THEN** validation은 `structured-fact-validation-v1`을 식별하고 legacy natural-language violation을 포함해서는 안 된다(MUST NOT).

## MODIFIED Requirements

### Requirement: Deterministic review validation

Provider response가 schema validation을 통과한 뒤 시스템은 network 또는 외부 side effect가 없는 deterministic validator로 output과 immutable `AgenticReviewInput`을 비교해야 한다(SHALL). Validator가 authoritative하게 판정하는 violation은 다음 세 가지로 한정해야 하며(SHALL), stable order와 uniqueness를 유지해야 한다(SHALL).

| Violation | Deterministic condition |
| --- | --- |
| `fabricated_evidence` | `evidence_used` 또는 finding의 `evidence_refs`가 provided Evidence subset이 아님 |
| `incident_mismatch` | output의 `incident_id`가 input과 다름 |
| `deterministic_contradiction` | output의 `target_column` 또는 `deterministic_facts`가 canonical input과 다름 |

`AgenticReviewOutput.incident_type`은 schema에서 `null_spike`로 제한한다. 지원하지 않는 incident type은 schema-invalid response로 거부되며 deterministic validator에 도달하지 않는다.

Validation result는 `structured-fact-validation-v1` policy identity를 사용해야 한다(SHALL). Validator는 `review_summary`, finding description 또는 uncertainty의 command, approval, authority, negation, quotation, punctuation이나 다른 자연어 의미를 acceptance의 blocking oracle로 사용해서는 안 된다(MUST NOT). Structured violation이 없으면 free-text wording과 무관하게 validation을 accepted로 반환해야 하며(SHALL), 이 acceptance는 approval, recovery 또는 mutation authority를 생성하지 않는다(MUST NOT).

#### Scenario: Fabricated evidence is rejected

- **WHEN** output 또는 finding이 input에 제공되지 않은 Evidence ID를 참조할 때
- **THEN** validator는 `fabricated_evidence` violation을 포함한 rejected result를 반환하고 output을 accepted advisory result로 채택해서는 안 된다(MUST NOT).

#### Scenario: Identity or canonical fact contradiction is rejected

- **WHEN** schema-valid output의 `incident_id`, `target_column` 또는 `deterministic_facts`가 input의 deterministic facts와 다를 때
- **THEN** validator는 `incident_mismatch` 또는 `deterministic_contradiction` violation을 포함한 rejected result를 반환하고 model 주장을 deterministic Reliability 결과보다 우선해서는 안 된다(MUST NOT).

#### Scenario: Unsupported incident type is rejected by output schema

- **WHEN** provider response가 `null_spike`가 아닌 `incident_type`을 반환할 때
- **THEN** `AgenticReviewOutput` schema validation에서 response를 거부하고 deterministic validator를 실행해서는 안 된다(MUST NOT).

#### Scenario: Multiple structured violations keep stable order

- **WHEN** 하나의 schema-valid output이 fabricated Evidence, incident mismatch와 canonical fact contradiction을 함께 포함할 때
- **THEN** validator는 `fabricated_evidence`, `incident_mismatch`, `deterministic_contradiction` 순서의 중복 없는 violation을 반환해야 한다.

#### Scenario: Free-text action language does not change acceptance

- **GIVEN** output이 input identity, canonical facts와 provided Evidence subset을 보존할 때
- **WHEN** advisory text가 approval claim, recovery/backfill command 또는 shell/SQL/file/database/data mutation처럼 읽힐 수 있는 표현을 포함할 때
- **THEN** validator는 그 free-text 의미만으로 violation을 생성해서는 안 되며(MUST NOT) structured validation을 accepted로 반환해야 한다.

#### Scenario: Prompt-injection-like text remains untrusted data

- **GIVEN** input Evidence 또는 output free text에 instruction처럼 보이는 문장이 포함되어 있을 때
- **WHEN** structured review validation을 수행할 때
- **THEN** 시스템은 해당 문장을 instruction이나 authority로 실행해서는 안 되며(MUST NOT) Evidence reference, incident identity와 canonical facts만 판정해야 한다.

#### Scenario: Structured advisory output is accepted

- **WHEN** output이 input identity와 canonical facts를 보존하고 실제 Evidence subset만 사용할 때
- **THEN** validator는 `structured-fact-validation-v1` accepted result를 반환하되 approval, recovery 또는 mutation authority를 생성해서는 안 된다(MUST NOT).

### Requirement: Advisory and read-only boundary

> **Read-only guarantee:** Review가 반환할 수 있는 유일한 filesystem mutation은 invocation evidence의 create-only write다.

시스템은 `accepted`, `validation_failed`, `unavailable`, `input_rejected` 또는 `provenance_failed` Agentic review 어느 경우에도 `Incident` truth, `Evidence`, `RemediationDraft`, `RecoveryProposal`, `Approval`, recovery state 또는 data/database state를 변경해서는 안 된다(MUST NOT). Review 결과와 free-text wording은 사람의 판단을 돕는 advisory output이며 model output만으로 approval, recovery 또는 mutation을 유발해서는 안 된다(MUST NOT).

#### Scenario: Accepted review does not mutate reliability state

- **WHEN** valid `null_spike` review가 accepted되고 invocation evidence가 저장될 때
- **THEN** `Incident`, `Evidence`, `RemediationDraft`와 recovery/approval state 및 target data는 호출 전과 같아야 하고 invocation evidence 저장 외의 mutation이 없어야 한다.

#### Scenario: Action-like advisory remains non-executable

- **WHEN** structured validation을 통과한 accepted review가 action 또는 approval처럼 읽힐 수 있는 free text를 포함할 때
- **THEN** 시스템은 typed `Approval`, exact `RecoveryProposal` 또는 mutation request를 생성하거나 recovery executor를 호출해서는 안 된다(MUST NOT).

#### Scenario: Rejected or unavailable review remains contained

- **WHEN** fabricated Evidence, canonical contradiction, schema failure, provider unavailability 또는 provenance failure가 발생할 때
- **THEN** 시스템은 해당 review를 typed result와 evidence로 격리하고 deterministic Reliability 결과와 target data를 보존하며 recovery authority를 부여해서는 안 된다(MUST NOT).

### Requirement: Deterministic and adversarial evaluation

시스템은 provider network call 없이 input/output contract, typed result, structured-fact validator와 provenance replay contract를 반복 평가할 수 있어야 하며(SHALL), `null_spike` 기준으로 valid response, fabricated Evidence, canonical identity/fact mismatch, direct/indirect prompt-injection-like data, arbitrary free-text wording, schema-invalid response와 provider unavailability를 포함한 fixture를 다뤄야 한다(SHALL). Free-text advisory quality와 action/authority 의미 분류는 deterministic acceptance의 evaluation target이 아니며, 별도 필요성이 입증되지 않으면 blocking classifier를 추가하지 않아야 한다(SHALL). 적어도 하나의 local Ollama live invocation은 default suite와 분리된 opt-in path에서 같은 contract와 provenance 경계를 사용해 검증할 수 있어야 한다(SHALL).

| Evaluation path | Network | Required coverage |
| --- | --- | --- |
| Offline default suite | 사용하지 않음 | Input/output contract, canonical input projection, typed result, structured-fact validation, provenance replay와 authority separation |
| Opt-in Ollama live proof | 명시적으로 활성화한 경우에만 사용 | 실제 response, common adapter와 invocation provenance |

#### Scenario: Offline structured validation evaluation

- **WHEN** fake/stub response와 structured contradiction fixture를 provider 호출 없이 반복 검증할 때
- **THEN** 같은 structured fixture는 같은 status와 violation code를 생성해야 하고 input의 원문 Evidence, deterministic result와 target state를 변경해서는 안 된다.

#### Scenario: Free-text variation does not change structured result

- **GIVEN** identity, Evidence references와 canonical facts가 같은 schema-valid output들이 있을 때
- **WHEN** review summary, finding description 또는 uncertainty wording만 서로 다르게 평가할 때
- **THEN** 모든 output은 같은 accepted structured validation을 반환하고 외부 action을 수행해서는 안 된다(MUST NOT).

#### Scenario: Prompt injection is data, not instruction

- **WHEN** Evidence summary/payload 또는 provider output에 direct/indirect prompt-injection-like 문장이 포함되어 있을 때
- **THEN** 시스템은 그 문장을 Reliability instruction으로 실행하거나 권한으로 승격해서는 안 되며(MUST NOT), validation은 structured Evidence reference, identity와 canonical facts에만 의해 결정되어야 한다.

#### Scenario: Ollama live proof

- **WHEN** opt-in live proof가 명시적으로 활성화되고 configured Ollama OpenAI-compatible endpoint가 접근 가능하며 deterministic `null_spike` `Incident`/`Evidence`/`RemediationDraft`가 제공될 때
- **THEN** 실제 model response가 `AgenticReviewOutput`과 structured-fact validator를 통과하거나 typed failure로 종료되고, invocation evidence에 model/config, prompt identity/digest, `project_revision`, canonical input, output 또는 failure reason, validation, latency와 available usage가 남아야 한다.
