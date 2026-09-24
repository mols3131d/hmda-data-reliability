# reliability-agentic-review Specification Delta

## MODIFIED Requirements

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

#### Scenario: Invalid canonical target evidence

- **WHEN** canonical target Evidence가 없거나 둘 이상이거나 rule, column 또는 required numeric fact가 없거나 non-finite일 때
- **THEN** 시스템은 `input_rejected` result를 반환하고 provider invocation을 수행해서는 안 된다(MUST NOT).

#### Scenario: Unsupported incident type

- **WHEN** `volume_drop`, `schema_drift` 또는 `freshness_delay` Incident를 이 Capability의 review entry point에 제공할 때
- **THEN** 시스템은 명시적인 `input_rejected` result를 반환하고 provider invocation, approval 또는 recovery를 수행해서는 안 된다(MUST NOT).

#### Scenario: Referenced contextual evidence retains its own identity

- **GIVEN** incident identity와 일치하는 canonical target Evidence 및 incident/draft가 명시적으로 참조한 다른 asset의 contextual Evidence가 주어질 때
- **WHEN** review input을 생성할 때
- **THEN** canonical target의 asset과 partition은 incident와 일치해야 하고 contextual Evidence는 자체 identity를 보존한 채 input 및 bounded context에 포함될 수 있어야 한다.

## ADDED Requirements

### Requirement: Bounded review context

시스템은 유효한 `AgenticReviewInput`에서 incident 판단에 직접 관련된 Evidence만 결정론적으로 선택·투영하는 immutable `BoundedReviewContext`를 제공해야 한다(SHALL). Context는 각 선택 Evidence의 `evidence_id`, source, asset, partition, observation time, bounded facts와 provenance를 보존해야 하며 raw log, 전체 row, 전체 database 또는 allowlist 밖의 unbounded payload를 포함해서는 안 된다(MUST NOT).

Context selection은 stable priority와 evidence identity로 반복 실행해도 같은 순서와 projection을 생성해야 한다(SHALL). 요청된 context source가 제공되지 않으면 `missing_evidence` gap으로, 제공된 Evidence만으로 확인할 수 없는 root cause 또는 semantic context는 `unconfirmed_context` gap으로 구분해야 한다(SHALL).

#### Scenario: Context selects bounded evidence and records provenance

- **GIVEN** 하나의 canonical null-spike Evidence와 partition metadata, related-table 또는 validation Evidence가 포함된 review input이 주어질 때
- **WHEN** bounded context를 생성할 때
- **THEN** canonical target을 포함해 bounded limit 안의 관련 Evidence가 stable order로 선택되고 각 항목에 source, identity, observed time과 provenance가 남아야 한다.

#### Scenario: Missing and unconfirmed context remain distinct

- **GIVEN** context source 일부가 제공되지 않고 root cause가 Evidence에서 확정되지 않는 review input이 주어질 때
- **WHEN** bounded context를 생성할 때
- **THEN** 누락된 source는 `missing_evidence`, Evidence만으로 판단할 수 없는 내용은 `unconfirmed_context`로 각각 기록해야 하며 서로 합쳐서는 안 된다.

#### Scenario: Context projection is bounded and replayable

- **WHEN** 같은 review input으로 bounded context를 반복 생성할 때
- **THEN** 같은 canonical JSON projection과 digest가 생성되어야 하며 payload 크기와 선택 Evidence 수가 configured bound를 초과하지 않아야 한다.

#### Scenario: Oversized context is rejected before invocation

- **WHEN** bounded context의 canonical serialized size가 configured context limit을 초과할 때
- **THEN** 시스템은 `input_rejected`와 `context_too_large` failure code를 반환하고 provider invocation 또는 invocation evidence 생성을 수행해서는 안 된다(MUST NOT).

#### Scenario: Prompt-visible evidence references match the bounded allowlist

- **WHEN** bounded context에서 canonical prompt input을 생성할 때
- **THEN** draft의 citable `evidence_refs`는 선택된 bounded context Evidence ID와 일치해야 하며 provider-visible reference가 deterministic validator의 Evidence allowlist 밖에 있어서는 안 된다(MUST NOT).

### Requirement: Structured agentic utility contribution

시스템은 advisory review output에서 deterministic facts와 `RemediationDraft`를 단순 재진술하지 않고 사람의 다음 판단에 기여하는 구조화된 utility contribution을 표현할 수 있어야 한다(SHALL). Contribution 종류는 최소 `evidence_gap`, `investigation_priority`, `remediation_critique`, `material_uncertainty`를 지원해야 하며 각 contribution은 bounded 설명, optional Evidence reference와 필요한 경우 priority를 가져야 한다.

Utility contribution은 approval, `RecoveryProposal`, recovery, shell, SQL, file, database 또는 data mutation authority를 생성해서는 안 된다(MUST NOT). 기존 structured-fact validator는 contribution의 Evidence reference와 input identity를 deterministic하게 검증해야 하며 자연어 utility 의미를 safety oracle로 사용해서는 안 된다.

#### Scenario: Utility contribution adds a decision aid

- **WHEN** provider output이 제공된 Evidence의 gap 또는 불확실성을 식별하고 조사 priority나 draft critique를 함께 반환할 때
- **THEN** 해당 contribution을 구조화된 advisory output으로 parse하고 관련 Evidence reference를 보존할 수 있어야 한다.

#### Scenario: Utility output remains advisory

- **WHEN** utility contribution이 recovery 또는 backfill을 추천하거나 비판할 때
- **THEN** output은 advisory content로만 남고 approval, recovery 또는 target mutation을 직접 수행하거나 권한을 부여해서는 안 된다.

### Requirement: Versioned human utility evaluation

시스템은 Review AI utility를 `rubric_v1`로 식별되는 immutable human rubric으로 평가해야 하며(SHALL), rubric은 `added_value`, `actionability`, `evidence_awareness`, `uncertainty_handling`, `prioritization`의 다섯 criterion을 모두 포함해야 한다(SHALL). 각 criterion은 bounded human score와 non-empty rationale를 가져야 하며 자동 LLM judge 또는 외부 평가 플랫폼에 의존해서는 안 된다(MUST NOT).

사람이 평가한 점수가 유효하려면 다섯 criterion 각각에 bounded score와 non-empty rationale가 있어야 한다(SHALL). Rubric identity가 baseline과 candidate에서 다르면 comparison을 성공으로 보고해서는 안 된다(MUST NOT). Positive, deterministic-fact restatement, non-actionable hedging 사례를 이용해 rubric 판별력을 테스트해야 하지만, control 결과를 runtime 또는 durable quality-basis contract로 보존할 필요는 없다.

#### Scenario: Rubric scores all utility dimensions

- **WHEN** human evaluator가 representative output을 평가할 때
- **THEN** 다섯 criterion 각각에 score와 rationale이 없으면 evaluation을 유효한 quality evidence로 저장할 수 없어야 한다.

#### Scenario: Rubric fixtures distinguish added value from restatement and hedging

- **WHEN** `rubric_v1` positive/negative controls를 검증할 때
- **THEN** positive 사례는 다섯 criterion에서 적절한 human score를 받을 수 있고, 단순 재진술 및 실행 가능한 행동 없는 hedging 사례는 `added_value`, `actionability` 또는 `prioritization`에서 낮은 점수로 구분되어야 한다.

#### Scenario: Over-defensive hedging fixture is not treated as useful by proxy

- **GIVEN** deterministic facts가 존재함에도 실행 가능한 후속 검증 행동 없이 전수 조사나 포괄적 불확실성만을 주장하는 면책형 negative control output이 주어질 때
- **WHEN** `rubric_v1` 기준으로 평가를 수행할 때
- **THEN** 해당 fixture는 `actionability` 또는 `prioritization` 중 하나 이상에서 낮은 human score로 평가되며, 다른 criterion 점수나 구조화된 contribution의 존재만으로 utility pass가 되지 않아야 한다(MUST NOT).

### Requirement: Baseline and candidate utility comparison evidence

시스템은 동일한 retained representative case와 동일한 rubric identity에서 baseline과 candidate output의 human evaluations를 비교하는 immutable `UtilityComparisonEvidence`를 생성할 수 있어야 한다(SHALL). Comparison은 baseline/candidate invocation identity, case identity/version, rubric identity, change-under-test, rubric criterion마다 정확히 하나씩 있는 score delta와 human `accept`, `reject` 또는 `no_change` decision 및 rationale을 연결해야 한다(SHALL). 각 criterion score의 aggregate는 recorded baseline/candidate total 및 total delta와 일치해야 한다(SHALL).

Comparison은 baseline evaluation의 `output_kind`가 `baseline`, candidate evaluation의 `output_kind`가 `candidate`이고 둘이 동일 case/version/rubric/revision 및 deterministic facts(`incident_id`, `target_column`, `deterministic_facts`)에서 평가된 경우에만 valid로 표시해야 한다(SHALL). Applicable candidate에 비교 가능한 evaluation 또는 attribution evidence가 없거나 동일 case 속성이 불일치하면 accept 또는 baseline promotion 대신 `blocked`/`inconclusive`를 기록해야 한다(MUST NOT).

#### Scenario: Same case and rubric are compared

- **WHEN** 명시적으로 baseline과 candidate로 식별된 evaluation이 같은 case/version 및 `rubric_v1`, 동일 deterministic facts 및 project revision에서 human 평가되고 comparison이 생성될 때
- **THEN** criterion별 delta와 total delta, invocation identity, change-under-test와 human decision/rationale을 사람이 검토 가능한 evidence로 복원할 수 있어야 한다.

#### Scenario: Mismatched or incomplete comparison is blocked

- **WHEN** baseline/candidate role, case/version, rubric, criterion score, 또는 deterministic facts/project revision이 비교 조건을 만족하지 않을 때
- **THEN** evidence는 invalid 또는 `blocked`/`inconclusive`로 남고 candidate accept와 baseline promotion을 허용해서는 안 된다.
