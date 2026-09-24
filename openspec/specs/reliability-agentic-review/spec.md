# reliability-agentic-review Specification

## Purpose

> **핵심 경계:** `null_spike`의 deterministic truth와 제공된 Evidence가 review의 기준이다. LLM은 advisory output만 만들며, `accepted` 결과도 deterministic validation과 durable provenance를 모두 통과해야 한다.

이 Capability는 deterministic `Incident`, 실제 `Evidence`와 `RemediationDraft`를 LLM이 검토하더라도 결과가 canonical facts와 제공된 근거에 묶이고 advisory 경계를 넘지 않도록 한다. 각 provider 결과와 실패는 replay 가능한 evidence로 남긴다.

## Requirements

### Requirement: Structured null-spike review input

시스템은 `null_spike` `Incident`, 실제 제공된 하나 이상의 `Evidence`, 기존 `RemediationDraft`, `PromptIdentity`와 caller가 제공한 non-empty `project_revision`을 보존하는 call-scoped snapshot `AgenticReviewInput`을 받아야 한다(SHALL). Snapshot 생성 뒤 caller가 보유한 nested list 또는 mapping을 변경해도 prompt, validation과 provenance에 사용되는 input은 변하지 않아야 한다(SHALL).

Input은 다음 invariant를 모두 만족할 때만 provider review 대상으로 인정해야 한다(SHALL).

- **Incident and draft identity:** `incident.incident_type`와 `draft.incident_type`는 정확히 `null_spike`이고, incident와 draft의 `incident_id`, `asset_name`과 `partition`이 일치한다.
- **Evidence linkage:** 제공된 Evidence ID는 unique하고 `incident.evidence_refs` 및 `draft.evidence_refs`와 같은 set이어야 한다. 각 Evidence는 자신이 나타내는 asset과 partition identity를 보존해야 한다.
- **Canonical target:** 정확히 하나의 canonical target Evidence가 있어야 하며, 그 asset과 partition은 incident와 일치해야 한다. 이 Evidence는 `source=profile`, `payload.rule=null_spike`, non-empty string `column`, finite numeric `baseline_null_rate`, `current_null_rate`, `delta`와 `threshold`를 가져야 한다. Target column과 numeric facts는 이 Evidence에서만 유도한다. 명시적으로 참조된 bounded contextual Evidence는 다른 asset 또는 partition을 나타낼 수 있다.
- **Prompt metadata:** `PromptIdentity`는 `template_id=reliability-agentic-review.null-spike`, `version=v1`이어야 하고, Evidence payload는 canonical JSON으로 표현 가능해야 한다.

이 Capability의 review entry point는 `null_spike` 외 incident type을 지원해서는 안 된다(MUST NOT).

#### Scenario: Valid evidence-bound input

- **WHEN** 위의 identity 관계, complete Evidence set, unique canonical target Evidence, `PromptIdentity`와 `project_revision`을 만족하는 `null_spike` 입력이 제공될 때
- **THEN** 시스템은 snapshot `AgenticReviewInput`을 만들고 provider invocation을 진행할 수 있어야 한다.

#### Scenario: Mismatched input is rejected before invocation

- **WHEN** Evidence가 incident 또는 draft의 reference set에서 누락되거나 incident/draft의 identity 또는 type이 다르거나 canonical target Evidence의 asset/partition이 incident와 다를 때
- **THEN** 시스템은 `input_rejected` result를 반환하고 provider invocation 또는 invocation evidence 생성을 수행해서는 안 된다(MUST NOT).

#### Scenario: Referenced contextual evidence retains its own identity

- **GIVEN** incident identity와 일치하는 canonical target Evidence 및 incident/draft가 명시적으로 참조한 다른 asset의 contextual Evidence가 주어질 때
- **WHEN** review input을 생성할 때
- **THEN** canonical target의 asset과 partition은 incident와 일치해야 하고 contextual Evidence는 자체 identity를 보존한 채 input 및 bounded context에 포함될 수 있어야 한다.

#### Scenario: Invalid canonical target evidence

- **WHEN** canonical target Evidence가 없거나 둘 이상이거나 rule, column 또는 required numeric fact가 없거나 non-finite일 때
- **THEN** 시스템은 `input_rejected` result를 반환하고 provider invocation을 수행해서는 안 된다(MUST NOT).

#### Scenario: Unsupported incident type

- **WHEN** `volume_drop`, `schema_drift` 또는 `freshness_delay` Incident를 이 Capability의 review entry point에 제공할 때
- **THEN** 시스템은 명시적인 `input_rejected` result를 반환하고 provider invocation, approval 또는 recovery를 수행해서는 안 된다(MUST NOT).

### Requirement: Canonical provider input projection

시스템은 provider user data와 invocation provenance에 사용할 `canonical_input`을 `AgenticReviewInput`에서 결정적으로 투영해야 하며(SHALL), 다음 allowlisted field 외의 runtime field를 포함해서는 안 된다(MUST NOT).

| Source | Allowed fields |
| --- | --- |
| `Incident` | `incident_id`, `incident_type`, `asset_name`, `partition`, `status`, `severity` |
| Each `Evidence` | `evidence_id`, `source`, `asset_name`, `partition`, `observed_at`, `summary`, `payload` |
| `RemediationDraft` | `incident_id`, `incident_type`, `asset_name`, `partition`, `rca_summary`, `evidence_refs`, `affected_assets`, `recommended_actions`, `dbt_test_suggestions`, `backfill_actions`, `validation_actions`, `requires_approval` |
| Review facts | `deterministic_facts` |

`canonical_input`은 같은 snapshot에서 같은 canonical JSON byte sequence를 생성해야 한다(SHALL). System instruction과 user data는 분리해야 하며(SHALL), `canonical_input` 안의 Evidence summary/payload와 draft text는 instruction이 아니라 untrusted data로 취급해야 한다(SHALL).

Rendered messages가 configured `max_prompt_bytes`를 넘으면 시스템은 provider call 전에 `input_rejected`를 반환하고 invocation evidence를 만들지 않아야 한다(MUST NOT).

#### Scenario: Canonical projection is deterministic and bounded

- **WHEN** 같은 valid `AgenticReviewInput`을 반복 render할 때
- **THEN** 같은 allowlisted `canonical_input`과 같은 prompt digest가 생성되어야 하며 allowlist 밖의 Incident, Evidence, Draft 또는 runtime field는 provider user data에 포함되지 않아야 한다(MUST NOT).

#### Scenario: Prompt-injection text remains data

- **WHEN** Evidence summary/payload 또는 draft text에 명령문 형태의 문자열이 있을 때
- **THEN** 문자열은 `canonical_input`의 data로만 serialize되어야 하며 system instruction 또는 execution command로 승격되어서는 안 된다(MUST NOT).

#### Scenario: Oversized prompt is rejected before provider invocation

- **WHEN** canonical input을 포함한 rendered messages가 configured `max_prompt_bytes`를 넘을 때
- **THEN** 시스템은 `input_rejected` result를 반환하고 provider invocation 또는 invocation evidence 생성을 수행해서는 안 된다(MUST NOT).

### Requirement: Structured advisory review output

시스템은 provider response를 다음 immutable `AgenticReviewOutput`으로 표현해야 한다(SHALL).

- **Identity:** `incident_id`, `incident_type`, `target_column`
- **Deterministic facts:** canonical target Evidence의 `baseline_null_rate`, `current_null_rate`, `delta`와 `threshold`를 복사한 `NullSpikeFacts` 형태의 `deterministic_facts`
- **Review content:** non-empty `review_summary`, 하나 이상의 `evidence_used`, `findings`와 `uncertainties`
- **Recommendation:** `support`, `needs_human_review`, `insufficient_evidence` 중 하나인 `advisory_recommendation`
- **Utility contribution:** optional `utility_contributions` containing bounded, structured contributions of kind `evidence_gap`, `investigation_priority`, `remediation_critique` or `material_uncertainty`; `investigation_priority` requires a priority and other kinds must not carry one.

Output invariant는 다음과 같다.

- 각 finding의 `kind`는 `observation`, `concern`, `omission` 또는 `uncertainty` 중 하나이고, non-empty `description`과 optional `evidence_refs`를 가져야 한다(SHALL).
- Output은 `extra=forbid`에 해당하는 closed shape여야 한다.
- Approval, `RecoveryProposal`, recovery, shell, SQL, file, database 또는 data mutation action을 명령하거나 부여하는 dedicated field를 제공해서는 안 된다(MUST NOT).
- Text와 collection은 configured bounded limit을 넘어서는 안 된다(SHALL).
- Utility contribution은 사람의 다음 판단을 돕는 advisory content이며 approval, recovery 또는 mutation authority를 생성해서는 안 된다(MUST NOT).

Free-text가 advisory instruction을 얼마나 잘 따르는지는 prompt/evaluation concern이다. Deterministic validator는 자연어 의미 전체를 authoritative safety oracle로 취급하지 않는다. 실제 action authority는 review output shape와 분리된 read-only execution boundary 및 proposal-bound human approval이 통제한다.

#### Scenario: Valid advisory response

- **WHEN** provider가 input identity, canonical target column과 deterministic facts를 보존하고 실제 Evidence reference를 사용하는 response를 반환할 때
- **THEN** 시스템은 summary, finding/concern, uncertainty와 advisory recommendation을 structured output으로 parse할 수 있어야 한다.

#### Scenario: Invalid response shape

- **WHEN** response에 required field가 없거나 허용되지 않은 field, 허용되지 않은 finding kind/recommendation, 빈 summary 또는 canonical facts가 포함되지 않을 때
- **THEN** 시스템은 `validation_failed` result를 반환하고 response를 accepted review로 노출해서는 안 된다(MUST NOT).

#### Scenario: Utility contribution adds a decision aid

- **WHEN** provider output이 제공된 Evidence의 gap 또는 불확실성을 식별하고 investigation priority나 remediation critique를 반환할 때
- **THEN** 시스템은 contribution kind, bounded description, optional Evidence reference와 필요한 priority를 structured advisory output으로 보존해야 한다(SHALL).

#### Scenario: Utility output remains advisory

- **WHEN** utility contribution이 recovery 또는 backfill을 추천하거나 비판할 때
- **THEN** output은 advisory content로만 남고 approval, recovery 또는 target mutation을 직접 수행하거나 권한을 부여해서는 안 된다(MUST NOT).

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

### Requirement: Bounded review context

시스템은 유효한 `AgenticReviewInput`에서 incident 판단에 직접 관련된 Evidence만 결정론적으로 선택·투영하는 immutable `BoundedReviewContext`를 제공해야 한다(SHALL). Context는 각 선택 Evidence의 `evidence_id`, source, asset, partition, observation time, bounded facts와 provenance를 보존해야 하며 raw log, 전체 row, 전체 database 또는 allowlist 밖의 unbounded payload를 포함해서는 안 된다(MUST NOT).

Context selection은 stable priority와 evidence identity로 반복 실행해도 같은 순서와 projection을 생성해야 한다(SHALL). 요청된 context source가 제공되지 않으면 `missing_evidence` gap으로, 제공된 Evidence만으로 확인할 수 없는 root cause 또는 semantic context는 `unconfirmed_context` gap으로 구분해야 한다(SHALL).

#### Scenario: Context selects bounded evidence and preserves provenance

- **GIVEN** canonical null-spike Evidence 및 관련 metadata, lineage 또는 validation Evidence가 review input에 포함될 때
- **WHEN** bounded context를 생성할 때
- **THEN** canonical target을 포함해 limit 안의 관련 Evidence가 stable order로 선택되고 각 항목의 source, identity, observation time과 provenance가 보존되어야 한다(SHALL).

#### Scenario: Missing and unconfirmed context remain distinct

- **GIVEN** 일부 context source가 제공되지 않고 root cause가 Evidence에서 확정되지 않을 때
- **WHEN** bounded context를 생성할 때
- **THEN** 누락된 source는 `missing_evidence`, Evidence만으로 확인할 수 없는 내용은 `unconfirmed_context`로 각각 기록되어야 한다(SHALL).

#### Scenario: Context projection is bounded and replayable

- **WHEN** 같은 review input으로 bounded context를 반복 생성할 때
- **THEN** 같은 canonical projection과 digest가 생성되고 serialized size와 선택 Evidence 수가 configured bound를 초과해서는 안 된다(MUST NOT).

#### Scenario: Oversized context is rejected before invocation

- **WHEN** bounded context가 configured size limit을 초과할 때
- **THEN** 시스템은 `input_rejected`와 `context_too_large` failure code를 반환하고 provider invocation 또는 invocation evidence 생성을 수행해서는 안 된다(MUST NOT).

#### Scenario: Prompt-visible evidence references match the bounded allowlist

- **WHEN** bounded context에서 canonical prompt input을 생성할 때
- **THEN** draft의 citable Evidence reference는 선택된 context Evidence ID와 일치하고 deterministic validator의 allowlist 밖 reference를 노출해서는 안 된다(MUST NOT).

### Requirement: Versioned human utility evaluation

시스템은 Review AI utility를 `rubric_v1`로 식별되는 immutable human rubric으로 평가해야 한다(SHALL). Rubric은 `added_value`, `actionability`, `evidence_awareness`, `uncertainty_handling`, `prioritization`의 다섯 criterion을 모두 포함해야 하며(SHALL), 각 criterion의 human score는 0–2 범위이고 non-empty rationale을 가져야 한다(SHALL). 자동 LLM judge 또는 외부 평가 플랫폼은 quality evaluation authority로 사용해서는 안 된다(MUST NOT).

#### Scenario: Rubric scores all utility dimensions

- **WHEN** human evaluator가 representative output을 평가할 때
- **THEN** 다섯 criterion 각각에 bounded score와 non-empty rationale가 있어야 evaluation을 유효한 quality evidence로 취급할 수 있다(SHALL).

#### Scenario: Rubric fixtures distinguish utility from restatement and hedging

- **WHEN** positive, deterministic-fact restatement 및 actionable next step이 없는 hedging control을 rubric test fixture로 평가할 때
- **THEN** fixture score는 추가 가치와 행동 가능성의 차이를 구분해야 하고 control 결과는 runtime 또는 durable quality-basis contract로 취급되어서는 안 된다(MUST NOT).

### Requirement: Baseline and candidate utility comparison evidence

시스템은 동일한 retained representative case와 rubric identity에서 baseline 및 candidate output의 human evaluation을 비교하는 immutable `UtilityComparisonEvidence`를 생성할 수 있어야 한다(SHALL). Comparison은 baseline/candidate invocation identity, case identity/version, rubric identity, change-under-test, criterion별 정확히 하나의 score delta와 human `accept`, `reject` 또는 `no_change` decision 및 rationale을 연결해야 한다(SHALL). Criterion delta aggregate는 recorded baseline/candidate total과 total delta에 일치해야 한다(SHALL).

Comparison은 baseline output role이 `baseline`, candidate output role이 `candidate`이고 둘이 동일 case/version/rubric/revision 및 deterministic facts에서 평가된 경우에만 valid로 표시해야 한다(SHALL). 비교 조건이나 attribution evidence가 맞지 않으면 candidate를 accept 또는 baseline promotion하지 않고 `blocked`/`inconclusive`로 기록해야 한다(MUST NOT).

#### Scenario: Same case and rubric are compared

- **WHEN** 명시적 baseline/candidate evaluation이 동일 case/version, `rubric_v1`, deterministic facts와 project revision을 사용해 생성될 때
- **THEN** criterion 및 total delta, invocation identity, change-under-test와 human decision/rationale을 복원할 수 있어야 한다(SHALL).

#### Scenario: Mismatched or incomplete comparison is blocked

- **WHEN** output role, case/version, rubric, criterion score, deterministic facts 또는 project revision이 비교 조건을 만족하지 않을 때
- **THEN** evidence는 invalid 또는 `blocked`/`inconclusive`로 남고 candidate acceptance나 baseline promotion을 허용해서는 안 된다(MUST NOT).

### Requirement: Deterministic review validation

Provider response가 schema validation을 통과한 뒤 시스템은 network 또는 외부 side effect가 없는 deterministic validator로 output과 immutable `AgenticReviewInput`을 비교해야 한다(SHALL). Validator가 authoritative하게 판정하는 violation은 다음 세 가지로 한정해야 하며(SHALL), stable order와 uniqueness를 유지해야 한다(SHALL).

| Violation | Deterministic condition |
| --- | --- |
| `fabricated_evidence` | `evidence_used`, finding 또는 utility contribution의 `evidence_refs`가 provided Evidence subset이 아님 |
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

#### Scenario: Utility contribution references are validated

- **WHEN** utility contribution이 제공되지 않은 Evidence ID를 참조할 때
- **THEN** validator는 `fabricated_evidence` violation을 반환하고 output을 accepted advisory result로 채택해서는 안 된다(MUST NOT).

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

시스템은 동일한 review contract와 configuration boundary를 사용해 OpenAI-compatible `chat.completions` endpoint를 제공하는 local Ollama model과 OpenAI API를 호출할 수 있어야 한다(SHALL). `base_url`은 userinfo(username/password), query parameter 또는 URL fragment를 포함해서는 안 되며(MUST NOT), Provider 차이는 credentials-free `base_url`, `SecretStr` credential(`api_key`), model과 bounded configuration으로 표현해야 하며 Reliability domain의 incident/evidence/recovery code가 provider별 business rule을 소유해서는 안 된다(MUST NOT).

이 Capability의 common wire profile은 다음 조건을 만족해야 한다(SHALL).

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

Provider call이 실제로 시작된 각 logical `review_null_spike()` invocation은 하나의 immutable-by-identity `AgenticInvocationEvidence` record를 `HMDA_RELIABILITY_ARTIFACTS_DIR` 아래 `agentic-review/invocations/<invocation_id>.json`에 create-only로 저장해야 한다(SHALL). Network retry는 별도 record가 아니라 `attempt_count`로 기록해야 한다(SHALL). Input preflight에서 `input_rejected`로 종료된 call에는 provider invocation evidence를 만들지 않아야 한다. Directory 생성, 임시 파일 생성/쓰기/링크, fsync를 포함한 persistence 필수 과정의 filesystem failure는 raw exception을 탈출시키지 않고 `provenance_failed` result로 정규화해야 한다(SHALL). 성공적으로 기록된 후의 임시 파일 cleanup 실패는 accepted 결과에 영향을 주지 않는 best-effort hygiene으로 처리한다.

Record 계약은 다음과 같다.

| Category | Must retain |
| --- | --- |
| Identity and context | `invocation_id`, sanitized model/configuration, prompt identity/digest, caller-provided `project_revision`, incident/evidence references, provider user data의 source인 bounded `canonical_input` |
| Result | status, parsed structured output(가능한 경우), validation result 또는 typed failure code |
| Runtime | latency, attempt count, available token/usage/cost |
| Safety | API key, credential, raw system/user prompt, raw log와 raw provider exception/response는 기록하지 않음 |

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

- **WHEN** Evidence summary/payload 또는 provider output에 direct/indirect prompt-injection-like 문장이 포함될 때
- **THEN** 시스템은 그 문장을 Reliability instruction으로 실행하거나 권한으로 승격해서는 안 되며(MUST NOT), validation은 structured Evidence reference, identity와 canonical facts에만 의해 결정되어야 한다.

#### Scenario: Ollama live proof

- **WHEN** opt-in live proof가 명시적으로 활성화되고 configured Ollama OpenAI-compatible endpoint가 접근 가능하며 deterministic `null_spike` `Incident`/`Evidence`/`RemediationDraft`가 제공될 때
- **THEN** 실제 model response가 `AgenticReviewOutput`과 structured-fact validator를 통과하거나 typed failure로 종료되고, invocation evidence에 model/config, prompt identity/digest, `project_revision`, canonical input, output 또는 failure reason, validation, latency와 available usage가 남아야 한다.
