# reliability-agentic-review Specification Delta

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

### Requirement: Versioned human rubric and control discrimination

시스템은 Review AI utility를 `rubric_v1`로 식별되는 immutable human rubric으로 평가해야 하며(SHALL), rubric은 `added_value`, `actionability`, `evidence_awareness`, `uncertainty_handling`, `prioritization`의 다섯 criterion을 모두 포함해야 한다(SHALL). 각 criterion은 bounded human score와 non-empty rationale를 가져야 하며 자동 LLM judge 또는 외부 평가 플랫폼에 의존해서는 안 된다(MUST NOT).

Quality basis는 compliant positive control이 `PASS`, deterministic facts 또는 draft를 재진술하는 bounded negative control뿐만 아니라 구체적 조사 행동 없이 책임을 회피하는 과도한 면책형(non-committal/hedging) negative control이 `FAIL`이 되도록 판별력을 검증해야 한다(SHALL). Control validation이 실패하거나 rubric identity가 mismatch이면 실제 baseline/candidate 비교를 성공으로 보고해서는 안 된다(MUST NOT).

Durable quality basis는 controls의 공통 `case_id`, `case_version`, `project_revision`과 `rubric_v1` identity를 보존해야 하며(SHALL), basis digest는 rubric, case identity, project revision, validity summary와 control validation evidence를 함께 바인딩해야 한다(SHALL). Positive control은 구조화된 utility contribution을 포함하고, restatement-negative control은 structured finding과 utility contribution을 포함하지 않아야 한다(SHALL). Baseline/candidate comparison 및 proof bundle은 valid quality basis와 동일한 case/version 및 rubric을 사용해야 하며(MUST), identity 또는 rubric이 불일치하거나 digest가 저장된 내용과 맞지 않으면 fail closed 해야 한다(SHALL). Invalid quality basis를 참조하는 comparison은 `blocked`여야 하며, 어떠한 comparison 상태에서도 invalid basis를 durable proof bundle로 저장할 수 없어야 한다(MUST NOT).

#### Scenario: Rubric scores all utility dimensions

- **WHEN** human evaluator가 representative output을 평가할 때
- **THEN** 다섯 criterion 각각에 score와 rationale이 없으면 evaluation을 유효한 quality evidence로 저장할 수 없어야 한다.

#### Scenario: Controls prove non-vacuous discrimination

- **WHEN** `rubric_v1` positive/negative controls를 검증할 때
- **THEN** positive control은 `PASS`, negative control(단순 재진술 및 과도한 면책형 회피)은 `FAIL`로 판정되고 결과가 durable quality-basis evidence에 남아야 한다.

#### Scenario: Over-defensive hedging control is rejected as FAIL

- **GIVEN** deterministic facts가 존재함에도 실행 가능한 후속 검증 행동 없이 전수 조사나 포괄적 불확실성만을 주장하는 면책형 negative control output이 주어질 때
- **WHEN** `rubric_v1` 기준으로 평가를 수행할 때
- **THEN** `actionability` 또는 `prioritization` 중 적어도 하나에서 0점을 받아 최종 `FAIL`로 판정되어야 하며, 나머지 criterion의 점수만으로 hedging control을 유효하게 만들어서는 안 된다(MUST NOT).

#### Scenario: Quality basis identity is durable and bound to its controls

- **WHEN** 동일 case/version/revision의 세 required controls로 valid quality basis를 생성하고 저장 후 재로드할 때
- **THEN** basis는 case identity와 세 control outcome을 보존하고 digest가 rubric, case identity, project revision, validity summary 및 control evidence를 바인딩해야 하며, 재로드 시 세 role의 정확한 개수, role별 outcome, control validity와 공통 case/version/revision을 다시 검증해야 한다(SHALL). 다른 case를 참조하는 comparison 또는 proof bundle은 valid할 수 없어야 한다(MUST NOT).

#### Scenario: Quality basis rubric mismatch is blocked

- **WHEN** baseline/candidate가 `rubric_v1`로 평가됐지만 quality basis의 rubric identity가 다를 때
- **THEN** comparison은 `blocked`로 기록되고 human decision을 보존하거나 candidate를 accept해서는 안 된다(MUST NOT).

### Requirement: Baseline and candidate utility comparison evidence

시스템은 동일한 retained representative case와 동일한 rubric identity에서 baseline과 candidate output의 human evaluations를 비교하는 immutable `UtilityComparisonEvidence`를 생성할 수 있어야 한다(SHALL). Comparison은 baseline/candidate invocation identity, case identity/version, rubric identity, change-under-test, rubric criterion마다 정확히 하나씩 있는 score delta와 human `accept`, `reject` 또는 `no_change` decision 및 rationale을 연결해야 한다(SHALL). 각 criterion score의 aggregate는 recorded baseline/candidate total 및 total delta와 일치해야 한다(SHALL).

Comparison은 quality-basis control validation이 통과하고 baseline과 candidate가 동일 case/rubric 및 동일 deterministic facts(`incident_id`, `target_column`, `deterministic_facts`), 동일 `quality_basis.project_revision`으로 평가된 경우에만 valid로 표시해야 한다(SHALL). Applicable candidate에 비교 가능한 evaluation 또는 attribution evidence가 없거나 동일 case 속성이 불일치하면 accept 또는 baseline promotion 대신 `blocked`/`inconclusive`를 기록해야 한다(MUST NOT).

#### Scenario: Same case and rubric are compared

- **WHEN** baseline과 candidate가 같은 case/version 및 `rubric_v1`, 동일 deterministic facts 및 project revision에서 human 평가되고 comparison이 생성될 때
- **THEN** criterion별 delta와 total delta, invocation identity, change-under-test와 human decision/rationale을 사람이 검토 가능한 evidence로 복원할 수 있어야 한다.

#### Scenario: Mismatched or incomplete comparison is blocked

- **WHEN** case/version, rubric, control validation, criterion score, 또는 deterministic facts/project revision이 비교 조건을 만족하지 않을 때
- **THEN** evidence는 invalid 또는 `blocked`/`inconclusive`로 남고 candidate accept와 baseline promotion을 허용해서는 안 된다.
