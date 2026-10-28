# reliability-agentic-review Specification

## Purpose

> **핵심 경계:** `null_spike`의 deterministic truth와 제공된 Evidence가 review의 기준이다. LLM은 advisory output만 만들며, `accepted` 결과도 deterministic validation과 durable provenance를 모두 통과해야 한다.

이 Capability는 deterministic `Incident`, 실제 `Evidence`와 `RemediationDraft`를 LLM이 검토하더라도 결과가 canonical facts와 제공된 근거에 묶이고 advisory 경계를 넘지 않도록 한다. 각 provider 결과와 실패는 replay 가능한 evidence로 남긴다.

기존 `PromptIdentity`, `AgenticReviewOutput`과 `accepted` 검증·version 기본값은 structured 경로의 계약이다. 기본 live는 아래 staged collection 계약을 사용하며, 세 텍스트의 수집·저장 완료를 `completed`로 구분한다.

## Requirements

### Requirement: Staged prose review collection

시스템은 같은 immutable 사례의 근거 검토·초안 비판·종합을 고정 순서로 실행하고 모델에 JSON 생성 대신 한국어 텍스트를 요청해야 한다(SHALL). 호출마다 원래 canonical input과 완료된 이전 assistant 응답을 유지하고 전체 요청의 byte cap과 digest를 계산해야 한다(SHALL). 사례 데이터나 이전 모델 답변이 단계·system 지시를 선택해서는 안 된다(MUST NOT).

시스템은 원입력 식별자·대상·수치와 단계 ID·순서·반환된 텍스트를 코드로 결합해 별도 JSON collection을 생성해야 한다(SHALL). 답변의 공백·개행을 보존하며(SHALL), prose에서 기존 structured output의 분류·근거 참조·권고 enum을 추측해 생성해서는 안 된다(MUST NOT). 완료 상태는 수집·저장 완료로 한정하며 기존 accepted나 사람의 품질 평가를 의미해서는 안 된다(MUST NOT).

#### Scenario: Three text answers are mechanically collected

- **WHEN** 같은 사례의 세 단계가 비어 있지 않은 정상 텍스트를 반환할 때
- **THEN** 코드는 고정 순서의 원문과 원입력 facts를 JSON으로 저장하고 completed 및 저장 경로를 반환해야 한다(SHALL).
- **AND** provider 요청은 JSON response_format을 강제해서는 안 된다(MUST NOT).

#### Scenario: Later turns retain the same case and prior answers

- **WHEN** 두 번째 또는 세 번째 단계를 호출할 때
- **THEN** 원본 canonical input과 완료 단계 원문을 대화 자료로 유지하고, 누적 요청 전체의 한도를 호출 전에 확인해야 한다(SHALL).

#### Scenario: A failed or incomplete answer stops the workflow

- **WHEN** 단계 호출이 unavailable, oversized, empty 또는 알려진 length·filter·tool 종료로 완료될 때
- **THEN** 후속 호출을 중단하고 원문이 반환된 경우 검증 전에 보존하며, 실패 단계와 완료된 단계 정보를 반환해야 한다(SHALL).
- **AND** 세 단계를 완료한 output을 생성하거나 completed를 반환해서는 안 된다(MUST NOT).

#### Scenario: Existing structured review remains explicit

- **WHEN** 기존 structured API 또는 명시적 structured live 모드를 사용할 때
- **THEN** 기존 JSON 출력·검증·invocation 계약을 유지해야 한다(SHALL).
- **AND** live 모드가 생략되면 단계별 텍스트 경로를 사용해야 한다(SHALL).

### Requirement: Staged review provenance and failure retention

시스템은 workflow·stage identity, revision·설정·원입력, 요청·응답 digest·상태·usage·attempt·원문 경로 및 코드 조립 결과 digest를 연결해야 한다(SHALL). 각 단계가 끝나면 기록을 보존하고 실패 시 이전 기록·원문을 덮어써서는 안 된다(MUST NOT). 모델 원문과 코드가 조립한 JSON의 출처를 구별해야 한다(SHALL).

기록과 collection은 bounded create-only atomic private 파일로 저장해야 하며(SHALL), identity 충돌은 provider 호출 전에 거부해야 한다(SHALL). 저장 실패는 provenance_failed로 반환하고 생성된 진단 경로를 가능한 범위에서 제공해야 한다(SHALL). 기존 invocation 또는 외부 projection에 단계 원문을 추가해서는 안 된다(MUST NOT). 호출 수는 세 단계와 설정된 per-call retry 범위로 제한해야 한다(SHALL).

#### Scenario: A later failure preserves earlier evidence

- **WHEN** 첫 단계가 저장된 뒤 두 번째 단계가 실패할 때
- **THEN** 첫 단계 원문·요청 digest·checkpoint와 두 번째 단계의 반환된 원문·실패 기록을 보존하고 세 번째 단계는 호출하지 않아야 한다(SHALL).

#### Scenario: Collection or manifest persistence fails

- **WHEN** 단계 원문 저장 이후 결과 JSON 또는 manifest 저장이 실패할 때
- **THEN** 성공을 반환하지 않고 이전 raw·checkpoint와 이미 생성된 경로를 보존해야 한다(SHALL).

#### Scenario: Credentials and raw text stay out of metadata

- **WHEN** 단계별 또는 workflow metadata를 저장하거나 콘솔에 결과 위치를 출력할 때
- **THEN** API key·provider exception 원문·단계 답변 본문은 metadata나 자동 콘솔 로그에 포함하지 않아야 한다(SHALL).
- **AND** 답변 본문은 별도 raw 파일과 사용자가 열어 보는 collection JSON에서 확인할 수 있어야 한다(SHALL).

### Requirement: Structured null-spike review input

시스템은 `null_spike` `Incident`, 실제 제공된 하나 이상의 `Evidence`, 기존 `RemediationDraft`, `PromptIdentity`와 caller가 제공한 non-empty `project_revision`을 보존하는 call-scoped snapshot `AgenticReviewInput`을 받아야 한다(SHALL). Snapshot 생성 뒤 caller가 보유한 nested list 또는 mapping을 변경해도 prompt, validation과 provenance에 사용되는 input은 변하지 않아야 한다(SHALL).

Input은 다음 invariant를 모두 만족할 때만 provider review 대상으로 인정해야 한다(SHALL).

- **Incident and draft identity:** `incident.incident_type`와 `draft.incident_type`는 정확히 `null_spike`이고, incident와 draft의 `incident_id`, `asset_name`과 `partition`이 일치한다.
- **Evidence linkage:** 제공된 Evidence ID는 unique하고 `incident.evidence_refs` 및 `draft.evidence_refs`와 같은 set이어야 한다. 각 Evidence는 자신이 나타내는 asset과 partition identity를 보존해야 한다.
- **Canonical target:** 정확히 하나의 canonical target Evidence가 있어야 하며, 그 asset과 partition은 incident와 일치해야 한다. 이 Evidence는 `source=profile`, `payload.rule=null_spike`, non-empty string `column`, finite numeric `baseline_null_rate`, `current_null_rate`, `delta`와 `threshold`를 가져야 한다. Target column과 numeric facts는 이 Evidence에서만 유도한다. 명시적으로 참조된 bounded contextual Evidence는 다른 asset 또는 partition을 나타낼 수 있다.
- **Prompt metadata:** `PromptIdentity`는 `template_id=reliability-agentic-review.null-spike`, `version=v1|v2|v3`이어야 하고, Evidence payload는 canonical JSON으로 표현 가능해야 한다. 현재 개발 비교 단계의 version 생략 기본값은 `v1`이며, 향후 채택·단일 기본값 전환은 [review-ai-prompt-engineering](../review-ai-prompt-engineering/spec.md)의 lifecycle 계약을 따른다.

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

프롬프트 리소스, 한국어 지시문·설명문과 revision별 변경 추적은 [review-ai-prompt-engineering](../review-ai-prompt-engineering/spec.md) 계약을 따라야 한다(SHALL).

Rendered messages가 configured `max_prompt_bytes`를 넘으면 시스템은 provider call 전에 `input_rejected`를 반환하고 invocation evidence를 만들지 않아야 한다(MUST NOT).

#### Scenario: Canonical projection is deterministic and bounded

- **WHEN** 같은 valid `AgenticReviewInput`을 반복 render할 때
- **THEN** 같은 allowlisted `canonical_input`과 같은 prompt digest가 생성되어야 하며 allowlist 밖의 Incident, Evidence, Draft 또는 runtime field는 provider user data에 포함되지 않아야 한다(MUST NOT).

#### Scenario: Prompt-injection text remains data

- **WHEN** Evidence summary/payload 또는 draft text에 명령문 형태의 문자열이 있을 때
- **THEN** 문자열은 `canonical_input`의 data로만 serialize되어야 하며 system instruction 또는 execution command로 승격되어서는 안 된다(MUST NOT).

#### Scenario: Versioned output instructions preserve historical replay

- **WHEN** `v2` prompt를 render할 때
- **THEN** system instruction은 `evidence_used`, `findings`, `uncertainties`, `utility_contributions`와 nested `evidence_refs`의 배열 타입, 문자열·object element 구분, canonical facts 복사 및 `investigation_priority`만의 필수 `priority` 조건을 명시해야 한다(SHALL).
- **AND** 과거 prompt는 저장된 version과 canonical input을 기록된 `project_revision`의 renderer와 리소스에 제공해 재생할 수 있어야 하며(SHALL), 그 revision의 message digest와 일치해야 한다(SHALL).

#### Scenario: Oversized prompt is rejected before provider invocation

- **WHEN** canonical input을 포함한 rendered messages가 configured `max_prompt_bytes`를 넘을 때
- **THEN** 시스템은 `input_rejected` result를 반환하고 provider invocation 또는 invocation evidence 생성을 수행해서는 안 된다(MUST NOT).

### Requirement: Opt-in grounded review instructions

시스템은 `v3` prompt를 명시적으로 선택할 수 있어야 한다(SHALL). v3 instruction은 closed output의 field/type 및 conditional priority를 설명하면서 task-specific 내용 예시를 포함하지 않아야 한다(SHALL). Rate와 percentage-point 차이, delta threshold 및 baseline-zero에서 정의되지 않는 상대 변화율을 구별하도록 안내해야 한다(SHALL). Structured facts는 입력 값을 그대로 복사하고 설명에서만 읽기 쉬운 단위 표현을 사용하도록 안내해야 한다(SHALL).

Instruction은 제공된 evidence와 실제 draft를 대조하고 미확인 원인·검증 결과를 확정하지 않으며 존재하지 않는 draft action을 비판하지 않도록 안내해야 한다(SHALL). Utility는 단순 재서술을 넘어 확인 우선순위와 결과에 따라 달라지는 사람의 다음 판단에 연결하도록 안내해야 한다(SHALL). 이는 prompt 계약이며 임의 free-text를 거부하는 새 deterministic acceptance 규칙이 아니다.

현재 개발 비교 단계는 Python identity 기본 `v1`과 live harness 기본 `v2`를 사용한다. 채택 판단 이후에는 [review-ai-prompt-engineering](../review-ai-prompt-engineering/spec.md)의 lifecycle 계약에 따라 하나의 active 기본값으로 함께 전환해야 한다(SHALL). 과거 `v1`/`v2` 실행은 기록된 `project_revision`의 renderer와 리소스를 사용할 때 저장된 instruction과 digest를 재생할 수 있어야 한다(SHALL). 언어 변경으로 현재 revision의 digest가 달라져도 과거 invocation의 기록을 재작성해서는 안 된다(MUST NOT). v3 지원만으로 human utility나 candidate 채택을 주장해서는 안 된다(MUST NOT).

#### Scenario: Candidate version renders without content examples

- **WHEN** caller가 `v3`를 명시적으로 선택하고 기존 valid input을 render할 때
- **THEN** 동일 canonical projection과 advisory boundary를 사용하면서 위 수치·근거·draft 지침을 담은 별도 digest의 prompt를 생성해야 한다(SHALL).

#### Scenario: Historical versions retain replay identity

- **WHEN** 과거 canonical input과 `v1`, `v2` 또는 `v3` version을 기록된 `project_revision`의 renderer와 리소스로 다시 render할 때
- **THEN** 과거 invocation의 message digest와 같아야 하며(SHALL) 현재 active 기본값의 변경으로 저장된 version이나 과거 기록의 해석을 바꿔서는 안 된다(MUST NOT).

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

시스템은 Review AI utility를 `rubric_v1`로 식별되는 immutable human rubric으로 평가해야 한다(SHALL). Python API는 이 human-rated review value 평가를 `ReviewValueRubric`과 `ReviewValueAssessment`로 제공해야 한다(SHALL). Rubric은 `added_value`, `actionability`, `evidence_awareness`, `uncertainty_handling`, `prioritization`의 다섯 criterion을 모두 포함해야 하며(SHALL), 각 criterion의 human score는 0–2 범위이고 non-empty rationale을 가져야 한다(SHALL). 자동 LLM judge 또는 외부 평가 플랫폼은 quality evaluation authority로 사용해서는 안 된다(MUST NOT).

#### Scenario: Rubric scores all utility dimensions

- **WHEN** human evaluator가 representative output을 평가할 때
- **THEN** 다섯 criterion 각각에 bounded score와 non-empty rationale가 있어야 evaluation을 유효한 quality evidence로 취급할 수 있다(SHALL).

#### Scenario: Rubric fixtures distinguish utility from restatement and hedging

- **WHEN** positive, deterministic-fact restatement 및 actionable next step이 없는 hedging control을 rubric test fixture로 평가할 때
- **THEN** fixture score는 추가 가치와 행동 가능성의 차이를 구분해야 하고 control 결과는 runtime 또는 durable quality-basis contract로 취급되어서는 안 된다(MUST NOT).

### Requirement: Baseline and candidate utility comparison evidence

시스템은 동일한 retained representative case와 rubric identity에서 baseline 및 candidate output의 human evaluation을 비교하는 immutable `ReviewValueComparisonEvidence`를 생성할 수 있어야 한다(SHALL). Python comparison API는 `ReviewValueComparisonStatus`, `ReviewValueComparisonEvidence`, `compare_review_value()`와 `render_review_value_comparison_markdown()`을 통해 이를 제공해야 한다(SHALL). Comparison은 baseline/candidate invocation identity, case identity/version, rubric identity, change-under-test, criterion별 정확히 하나의 score delta와 human `accept`, `reject` 또는 `no_change` decision 및 rationale을 연결해야 한다(SHALL). Criterion delta aggregate는 recorded baseline/candidate total과 total delta에 일치해야 한다(SHALL).

Comparison은 baseline output role이 `baseline`, candidate output role이 `candidate`이고 둘이 동일 case/version/rubric/revision 및 deterministic facts에서 평가된 경우에만 valid로 표시해야 한다(SHALL). 비교 조건이나 attribution evidence가 맞지 않으면 candidate를 accept 또는 baseline promotion하지 않고 `blocked`/`inconclusive`로 기록해야 한다(MUST NOT).

#### Scenario: Same case and rubric are compared

- **WHEN** 명시적 baseline/candidate evaluation이 동일 case/version, `rubric_v1`, deterministic facts와 project revision을 사용해 생성될 때
- **THEN** criterion 및 total delta, invocation identity, change-under-test와 human decision/rationale을 복원할 수 있어야 한다(SHALL).

#### Scenario: Mismatched or incomplete comparison is blocked

- **WHEN** output role, case/version, rubric, criterion score, deterministic facts 또는 project revision이 비교 조건을 만족하지 않을 때
- **THEN** evidence는 invalid 또는 `blocked`/`inconclusive`로 남고 candidate acceptance나 baseline promotion을 허용해서는 안 된다(MUST NOT).

#### Scenario: Comparison records retain their serialized contract after API rename

- **WHEN** comparison evidence가 Review Value Python API로 serialize된 뒤 다시 읽힐 때
- **THEN** serialized field names, enum values, rubric identity, embedded outputs와 output digests는 기존 utility comparison contract와 동일하게 유지되어야 한다(SHALL).

### Requirement: Optional synthetic invocation projection

시스템은 기존 synthetic live harness에서 별도 opt-in으로만 Langfuse projection을 수행해야 한다(SHALL). 비활성 상태에서는 SDK import, 초기화와 외부 호출을 하지 않아야 한다(MUST). 기존 core result, local provenance와 exit 의미를 유지해야 한다(MUST).

#### Scenario: Disabled integration without SDK

- **WHEN** Langfuse opt-in이 없고 SDK가 설치되지 않았다
- **THEN** 기존 harness 동작이 유지되고 Langfuse를 import하거나 호출하지 않는다

#### Scenario: Verified accepted record

- **WHEN** harness provenance 검증을 통과한 accepted record의 canonical input이 현재 합성 사례와 일치한다
- **THEN** invocation, revision, prompt identity/digest, rubric과 exact output digest를 보존한 allowlist projection을 생성한다
- **AND** bounded facts, draft, evidence와 context gaps 및 accepted structured output을 사람에게 제공한다

#### Scenario: Media-like accepted output remains exact

- **WHEN** accepted output에 Langfuse SDK가 media로 인식하는 base64 data URI 문자열이 있다
- **THEN** child SDK의 media detection/upload를 끄고 structured output 문자열을 그대로 전달한다
- **AND** metadata의 output digest는 관찰되는 exact structured output을 식별한다

#### Scenario: Unsafe or missing evidence

- **WHEN** input rejection, provenance failure, provenance 검증 실패, 합성 입력 불일치 또는 65536 UTF-8 byte 초과 projection이 발생한다
- **THEN** 외부 전송을 생략하고 잘린 context/output을 채점 대상으로 표시하지 않는다

#### Scenario: Durable failed record

- **WHEN** 검증된 unavailable 또는 validation_failed record를 표시한다
- **THEN** identity와 typed status만 표시하고 input, partial output, raw failure text와 annotation target을 포함하지 않는다

#### Scenario: Export boundary failure

- **WHEN** init, projection, export, flush, shutdown 또는 configured timeout이 실패한다
- **THEN** sanitized integration status를 별도로 출력하고 기존 core result, local record와 exit 의미를 유지한다
- **AND** 외부 연동 대기는 기본 5초, 설정 범위 0초 초과 60초 이하로 제한한다

#### Scenario: Remote ingestion is unknown

- **WHEN** exporter가 오류 없이 반환했지만 원격 조회를 수행하지 않았다
- **THEN** submitted_unverified로 보고하고 delivery 또는 human proof 성공을 주장하지 않는다
- **AND** projection 시간과 실제 기록된 model latency를 구분한다

### Requirement: Integration-local human annotation mapping

수동 annotation은 invocation_id, exact output_digest와 rubric_v1에 결합되어야 한다(MUST). 각 criterion의 0/1/2 integer와 non-empty rationale가 정확히 한 번씩 있을 때만 complete로 판정해야 한다(SHALL). 이 판정은 human provenance, utility acceptance 또는 repository evaluation 생성 권한을 부여하지 않는다(MUST).

#### Scenario: Missing or invalid annotation

- **WHEN** 다섯 항목 중 누락, 중복, 범위 밖 값, 비정수, 빈 rationale 또는 target 불일치가 있다
- **THEN** incomplete로 판정하며 UI 완료 표시는 이를 덮어쓰지 않는다

#### Scenario: Snapshot does not match its accepted output

- **WHEN** snapshot output이 없거나 유효한 `AgenticReviewOutput`이 아니거나, model 정규화 뒤 canonical JSON 값과 타입이 다르거나, output digest가 재계산 값과 다르거나 rubric이 `rubric_v1`이 아니다
- **THEN** annotation은 incomplete로 판정한다

#### Scenario: Complete local annotation shape

- **WHEN** accepted output이 재검증되고 그 exact digest 및 `rubric_v1` target과 다섯 유효한 criterion/rationale가 제공된다
- **THEN** integration-local completeness만 확인하며 `ReviewValueAssessment`, candidate 승인 또는 recovery action을 만들지 않는다

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

이 Capability의 common wire profile은 다음 조건을 만족해야 한다(SHALL). Runtime은 assistant 대화 메시지를 보존하며 호출별 출력 모드를 명시할 수 있어야 한다(SHALL). 기존 structured 호출의 기본 JSON 모드는 유지해야 한다(SHALL).

| Request / behavior | Contract |
| --- | --- |
| Response | Non-streaming. Structured는 JSON object, staged text는 response_format 생략 |
| Sampling | `temperature=0` |
| Token limit | Domain `max_output_tokens`를 wire `max_tokens`로 매핑 |
| Tools and stream | `stream=false`, no-tools |
| Retry | 유한한 timeout과 `max_retries` 이하의 transport retry만 허용 |
| No-retry cases | SDK hidden retry, schema failure, guard failure와 client 4xx retry 금지 |

#### Scenario: Local and cloud-compatible configuration

- **WHEN** 같은 `AgenticReviewInput`에 Ollama의 OpenAI-compatible base URL 또는 OpenAI base URL과 각각의 model/credential을 설정할 때
- **THEN** 시스템은 동일한 review adapter boundary에서 common wire profile request를 만들고 provider-specific Reliability/domain code 변경 없이 선택한 경로의 response를 처리해야 한다(SHALL).

#### Scenario: Provider timeout or unavailability

- **WHEN** configured endpoint가 timeout, connection failure 또는 bounded retry 이후 unavailable 상태를 반환할 때
- **THEN** 시스템은 unavailable invocation result와 failure provenance를 반환하고 review output, approval, recovery 또는 mutation authority를 생성해서는 안 된다(MUST NOT).

#### Scenario: Provider returns schema-invalid content

- **WHEN** structured 경로의 provider가 HTTP-level success를 반환했지만 JSON 또는 `AgenticReviewOutput`으로 검증할 수 없는 content를 반환할 때
- **THEN** 시스템은 validation_failed result와 failure provenance를 반환하고 accepted advisory review 또는 외부 action을 반환해서는 안 된다(MUST NOT).

#### Scenario: Text invocation keeps history without JSON forcing

- **WHEN** caller가 assistant 이력과 text 출력 모드를 명시할 때
- **THEN** Runtime은 메시지 순서와 원문을 보존하고 SDK wire에 response_format을 보내지 않아야 한다(SHALL).
- **AND** 같은 adapter의 다음 기본 호출은 기존 JSON 모드를 사용해야 한다(SHALL).

### Requirement: Bounded response failure diagnostics

시스템은 기존 공개 `response_schema_invalid` failure code를 유지하면서 빈 본문(`response_content_empty`), JSON 파싱 실패(`json_syntax_invalid`), 출력 계약 실패(`schema_validation_failed`)를 sanitized invocation evidence의 optional `response_diagnostics`로 구분해야 한다(SHALL). Schema 진단은 최대 8개의 field/code만 보존하며 field path는 최대 4개의 allowlisted schema field, 고정 `item` 또는 `unknown` component로 한정해야 한다(SHALL). 오류 code는 `type_invalid`, `missing_field`, `extra_field`, `conditional_invalid`, `value_invalid` 중 하나여야 한다(SHALL). 입력값, 임의 extra field 이름, Pydantic message/context/URL 또는 raw response는 진단·logger·CLI에 기록해서는 안 된다(MUST NOT).

Runtime SDK는 완료 응답의 `finish_reason`, `content_state`와 UTF-8 `content_bytes`를 provider-neutral optional `response_metadata`로 전달해야 한다(SHALL). 완료 이유는 `stop`, `length`, `content_filter`, `tool_calls`, `function_call`과 고정 `unknown`으로 제한하며, choice가 없으면 `null`이다. 본문 상태는 `text`, `content_missing`, `choices_empty`로 제한한다. Review evidence는 이 metadata를 보존하며, 이전 record의 두 optional field가 없어도 기존 의미로 읽을 수 있어야 한다(SHALL).

진단은 출력 자동 보정, schema/guard retry 또는 acceptance 완화를 수행해서는 안 된다(MUST NOT). `finish_reason=length`만으로 새로운 거부 정책을 적용해서는 안 되며(MUST NOT), 기존 schema·guard·provenance 경계로 최종 status를 판정해야 한다(SHALL). Raw tracing이나 Langfuse projection field 확대를 요구하지 않는다.

#### Scenario: Schema type and conditional failures remain contained

- **WHEN** provider가 문자열 `uncertainties`, 우선순위 kind의 `priority` 누락 또는 다른 kind의 non-null `priority`를 반환할 때
- **THEN** 시스템은 재호출이나 자동 수정 없이 `validation_failed / response_schema_invalid`를 반환하고 raw 입력값 없이 해당 field와 오류 분류를 evidence에 보존해야 한다(SHALL).

#### Scenario: Empty and truncated completions are distinguishable

- **WHEN** SDK가 빈 `choices`, `content=null`, 빈 문자열 또는 잘린 JSON을 반환할 때
- **THEN** invocation evidence에서 본문 상태와 가능한 완료 이유를 확인할 수 있고 빈 본문과 JSON 실패를 구분할 수 있어야 한다(SHALL). Invalid output은 accepted 결과로 노출해서는 안 된다(MUST NOT).

#### Scenario: Valid output with length metadata still uses existing validation

- **WHEN** `finish_reason=length`지만 본문이 출력 계약과 deterministic guard를 만족하고 provenance가 저장될 때
- **THEN** 시스템은 accepted 결과를 반환하고 완료 metadata만 진단 근거로 보존해야 한다(SHALL).

#### Scenario: Diagnostic metadata cannot retain arbitrary response text

- **WHEN** provider 오류 입력값·extra field 이름·알 수 없는 완료 이유에 임의 문자열이 포함될 때
- **THEN** 진단은 고정 field/code와 `unknown`으로 제한되어야 하며(SHALL), 해당 문자열은 schema-invalid evidence, result, CLI 또는 logger에 나타나서는 안 된다(MUST NOT).

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
