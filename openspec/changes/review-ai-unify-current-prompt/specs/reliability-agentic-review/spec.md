---
type: openspec-spec-driven-tdd-spec
category: spec
title: reliability-agentic-review
description: 현재 한국어 단계 실행만 제공하고 과거 버전·출력·기록 호환 지원을 제거합니다.
---

## MODIFIED Requirements

### Requirement: Structured null-spike review input

시스템은 `null_spike` `Incident`, 실제 제공된 하나 이상의 `Evidence`, `RemediationDraft`와 caller가 제공한 non-empty `project_revision`을 보존하는 call-scoped snapshot `AgenticReviewInput`을 받아야 한다(SHALL). Snapshot 생성 뒤 caller가 보유한 nested list 또는 mapping을 변경해도 prompt와 provenance에 사용되는 input은 변하지 않아야 한다(SHALL). Input은 prompt version이나 `PromptIdentity`를 받거나 보존해서는 안 된다(MUST NOT).

Input은 다음 invariant를 모두 만족할 때만 provider review 대상으로 인정해야 한다(SHALL).

- **Incident and draft identity:** incident와 draft의 type은 정확히 `null_spike`이고 `incident_id`, `asset_name`과 `partition`이 일치한다.
- **Evidence linkage:** 제공된 Evidence ID는 unique하고 incident와 draft의 `evidence_refs`와 같은 set이어야 한다. 각 Evidence는 자체 asset과 partition identity를 보존한다.
- **Canonical target:** 정확히 하나의 canonical target Evidence가 incident와 같은 asset·partition을 나타내야 한다. 이 Evidence는 `source=profile`, `payload.rule=null_spike`, non-empty string `column`, finite numeric `baseline_null_rate`, `current_null_rate`, `delta`와 `threshold`를 가져야 한다. Target column과 numeric facts는 이 Evidence에서만 유도한다.
- **Canonical data:** Evidence payload는 canonical JSON으로 표현 가능해야 한다. 명시적으로 참조된 bounded contextual Evidence는 다른 asset 또는 partition을 나타낼 수 있다.

이 review entry point는 다른 incident type을 지원해서는 안 된다(MUST NOT).

#### Scenario: Valid evidence-bound input

- **WHEN** 위 identity 관계, complete Evidence set, unique canonical target과 project revision을 만족하는 입력이 제공될 때
- **THEN** 시스템은 immutable input을 만들고 현재 단계 실행을 진행할 수 있어야 한다(SHALL).

#### Scenario: Mismatched input is rejected before invocation

- **WHEN** Evidence reference set 또는 incident/draft identity가 다르거나 canonical target의 asset·partition이 다를 때
- **THEN** provider 호출과 workflow reservation 전에 `input_rejected`를 반환해야 한다(SHALL).

#### Scenario: Referenced contextual evidence retains its own identity

- **WHEN** canonical target과 함께 명시적으로 참조된 다른 asset의 contextual Evidence가 제공될 때
- **THEN** canonical target은 incident identity와 일치하고 contextual Evidence는 자체 identity를 보존해야 한다(SHALL).

#### Scenario: Invalid canonical target evidence

- **WHEN** canonical target이 없거나 둘 이상이거나 rule·column·required numeric fact가 없거나 비유한 값일 때
- **THEN** provider 호출 전에 `input_rejected`를 반환해야 한다(SHALL).

#### Scenario: Unsupported incident type

- **WHEN** 다른 incident type이 입력될 때
- **THEN** provider 호출, approval 또는 recovery 없이 `input_rejected`를 반환해야 한다(SHALL).

### Requirement: Canonical provider input projection

시스템은 `AgenticReviewInput`에서 결정론적으로 생성한 bounded `canonical_input`을 provider 자료와 workflow provenance의 동일한 source로 사용해야 한다(SHALL). 허용하는 필드는 다음과 같으며 그 밖의 runtime field를 포함해서는 안 된다(MUST NOT).

| Source | Allowed fields |
| --- | --- |
| Incident | `incident_id`, `incident_type`, `asset_name`, `partition`, `status`, `severity` |
| Selected Evidence | `evidence_id`, `source`, bounded `summary`, allowlisted `facts`, `provenance` |
| Evidence provenance | `evidence_id`, `source`, `asset_name`, `partition`, `observed_at` |
| RemediationDraft | `incident_id`, `incident_type`, `asset_name`, `partition`, `rca_summary`, bounded `evidence_refs`, `affected_assets`, `recommended_actions`, `dbt_test_suggestions`, `backfill_actions`, `validation_actions`, `requires_approval` |
| Review facts and context | `deterministic_facts`, `review_context` |

동일 snapshot은 같은 canonical JSON bytes를 생성해야 한다(SHALL). System 지시문과 사례 자료를 분리하고 Evidence·draft·이전 모델 답변을 untrusted data로 다뤄야 한다(SHALL). 프롬프트 모듈과 한국어 지시문은 [review-ai-prompt-engineering](../review-ai-prompt-engineering/spec.md) 계약을 따른다.

#### Scenario: Canonical projection is deterministic and bounded

- **WHEN** 같은 유효 input을 반복 render할 때
- **THEN** 같은 bounded projection과 digest를 만들고 allowlist 밖 필드를 provider에 전달해서는 안 된다(MUST NOT).

#### Scenario: Prompt-injection text remains data

- **WHEN** Evidence 또는 draft에 명령문이 포함될 때
- **THEN** 자료로만 serialize하고 system 지시나 실행 명령으로 승격해서는 안 된다(MUST NOT).

#### Scenario: Oversized prompt is rejected before provider invocation

- **WHEN** 현재 메시지 전체가 configured `max_prompt_bytes`를 넘을 때
- **THEN** 해당 provider 호출 전에 `input_rejected`를 반환해야 한다(SHALL).
- **AND** 첫 호출 전 거부라면 workflow를 만들지 않고 이후 단계의 거부라면 이전 checkpoint를 보존해야 한다(SHALL).

### Requirement: Bounded review context

시스템은 유효한 input에서 incident 판단에 직접 관련된 Evidence만 stable priority와 identity로 선택·투영하는 immutable `BoundedReviewContext`를 제공해야 한다(SHALL). 선택한 Evidence의 identity·source·asset·partition·observation time·bounded facts·provenance를 보존하고 raw log·전체 row·database 또는 allowlist 밖의 unbounded payload를 포함해서는 안 된다(MUST NOT).

제공되지 않은 context source는 `missing_evidence`, 제공된 Evidence로 확정할 수 없는 원인과 semantic context는 `unconfirmed_context`로 구분해야 한다(SHALL).

#### Scenario: Context selects bounded evidence and preserves provenance

- **WHEN** canonical Evidence와 관련 metadata·lineage·validation Evidence가 제공될 때
- **THEN** limit 안에서 canonical target을 포함한 stable selection과 각 Evidence의 provenance를 보존해야 한다(SHALL).

#### Scenario: Missing and unconfirmed context remain distinct

- **WHEN** 일부 source가 없고 원인도 확정되지 않았을 때
- **THEN** source 누락과 미확정 내용을 서로 다른 gap으로 기록해야 한다(SHALL).

#### Scenario: Context projection is bounded and replayable

- **WHEN** 같은 input으로 context를 반복 생성할 때
- **THEN** 같은 projection·digest를 만들고 크기와 Evidence 수 한도를 지켜야 한다(SHALL).

#### Scenario: Oversized context is rejected before invocation

- **WHEN** context가 설정 한도를 넘을 때
- **THEN** provider 호출과 workflow reservation 전에 `input_rejected / context_too_large`를 반환해야 한다(SHALL).

#### Scenario: Prompt-visible evidence references match the bounded allowlist

- **WHEN** bounded context에서 canonical input을 만들 때
- **THEN** draft의 인용 가능한 Evidence reference는 선택된 context Evidence ID로 제한해야 한다(SHALL).

### Requirement: Staged prose review collection

일반 `review_null_spike` API·직접 service·live CLI는 같은 현재 실행을 사용해야 한다(SHALL). 근거 검토·초안 비판·종합을 고정 순서로 실행하고 모델에는 JSON 대신 한국어 텍스트를 요청해야 한다(SHALL). 각 호출은 원래 canonical input과 완료된 assistant 답변을 유지하고 누적 메시지 전체의 byte cap과 digest를 적용해야 한다(SHALL). 자료가 단계·system 지시를 선택해서는 안 된다(MUST NOT).

코드는 원입력 식별자·대상·수치와 단계 ID·순서·반환 텍스트를 결합한 `StagedReviewOutput` JSON을 생성해야 한다(SHALL). 모델 텍스트의 공백·개행을 보존하고, prose에서 분류·근거 참조·권고 enum을 추측해 생성해서는 안 된다(MUST NOT). `workflow_version=staged-v1`은 collection schema의 출처이며 선택 가능한 prompt version이 아니다.

#### Scenario: Three text answers are mechanically collected

- **WHEN** 세 단계가 비어 있지 않은 정상 텍스트를 반환할 때
- **THEN** 코드는 고정 순서 원문과 원입력 facts를 JSON으로 저장하고 `completed`와 저장 경로를 반환해야 한다(SHALL).
- **AND** provider에 JSON `response_format`을 강제해서는 안 된다(MUST NOT).

#### Scenario: Later turns retain the same case and prior answers

- **WHEN** 두 번째 또는 세 번째 단계를 호출할 때
- **THEN** 같은 canonical input과 완료 단계 원문을 유지하고 누적 메시지 한도를 호출 전에 확인해야 한다(SHALL).

#### Scenario: A failed or incomplete answer stops the workflow

- **WHEN** unavailable·oversized·empty 응답 또는 알려진 length·filter·tool 종료가 발생할 때
- **THEN** 반환된 bounded 원문을 판정 전에 보존하고 실패 단계와 완료된 단계를 기록하며 후속 호출을 중단해야 한다(SHALL).
- **AND** 완성된 output이나 `completed`를 반환해서는 안 된다(MUST NOT).

### Requirement: Typed review result boundary

결과는 `StagedReviewResult`로 표현하고 다음 status를 구분해야 한다(SHALL).

| Status | Meaning |
| --- | --- |
| `completed` | 세 답변과 코드 조립 output 및 provenance의 저장 완료 |
| `input_rejected` | input·context 또는 누적 prompt 한도 위반으로 해당 호출 전에 종료 |
| `validation_failed` | 응답 크기·빈 본문·알려진 미완료 종료로 텍스트 수집 실패 |
| `unavailable` | 전송 실패 또는 단계·전체 예산 소진 |
| `provenance_failed` | reservation·원문·checkpoint·output·manifest 저장 실패 |

완료되지 않은 결과는 완성된 output을 반환해서는 안 된다(MUST NOT). 이미 생성된 진단 경로와 이전 stage 기록은 가능한 범위에서 유지해야 한다(SHALL). 자연어의 JSON 문법·필드·enum·주장 검증으로 status를 판정해서는 안 되며(MUST NOT), `completed`를 품질 채택이나 approval로 해석해서는 안 된다(MUST NOT).

#### Scenario: Completed result requires retained provenance

- **WHEN** 모든 단계와 output·manifest 저장이 성공할 때
- **THEN** `completed`, output과 경로를 반환해야 한다(SHALL).

#### Scenario: Failure never exposes a complete output

- **WHEN** 단계 실행 또는 저장이 실패할 때
- **THEN** typed failure와 보존된 stage·경로를 반환하고 완성 output을 반환해서는 안 된다(MUST NOT).

### Requirement: Provider-compatible bounded invocation

시스템은 같은 Runtime adapter로 Ollama와 OpenAI의 OpenAI-compatible `chat.completions` endpoint를 호출할 수 있어야 한다(SHALL). Provider 차이는 credentials-free `base_url`, `SecretStr` API credential·model·bounded configuration으로 표현하고 Reliability domain이 provider별 business rule을 소유해서는 안 된다(MUST NOT). URL은 userinfo·query·fragment를 포함해서는 안 된다(MUST NOT).

Review 호출은 assistant 이력을 유지하는 non-streaming text mode·`temperature=0`·bounded `max_tokens`·no tools를 사용하고 `response_format`을 생략해야 한다(SHALL). Runtime adapter의 범용 JSON 출력 기능은 이 Capability의 모델 JSON 파서나 검증기를 의미하지 않는다. SDK hidden retry를 끄고 configured transport retry만 허용해야 한다(SHALL). 응답 내용에 따른 생성 재시도나 자동 수정을 해서는 안 된다(MUST NOT).

#### Scenario: Local and cloud-compatible configuration

- **WHEN** 같은 사례에 Ollama 또는 OpenAI의 endpoint·model·credential을 설정할 때
- **THEN** 같은 domain 실행과 common Runtime adapter를 사용해야 한다(SHALL).

#### Scenario: Provider timeout or unavailability

- **WHEN** timeout·connection failure 또는 bounded retry 소진이 발생할 때
- **THEN** typed unavailable과 실패 provenance를 반환해야 한다(SHALL).

#### Scenario: Text invocation keeps history without JSON forcing

- **WHEN** 단계 답변과 assistant 이력을 Runtime에 제공할 때
- **THEN** 메시지 순서·원문을 보존하고 `response_format`을 보내지 않아야 한다(SHALL).

### Requirement: Staged execution time budgets

시스템은 유한한 양수의 연결·읽기 대기 제한과 별도 단계·전체 실행 예산을 설정할 수 있어야 한다(SHALL). 공통 timeout은 생략된 세부 전송 설정의 기본값이며 명시된 연결·읽기 설정이 우선해야 한다(SHALL). Live 시작값과 환경 변수의 우선순위를 문서화해야 한다(SHALL).

Monotonic 시간으로 남은 예산을 확인하고 그 범위를 넘는 후속 단계·retry·backoff를 시작해서는 안 된다(MUST NOT). 각 전송 대기는 남은 예산 이하로 줄여야 한다(SHALL). 늦게 반환된 응답을 완료 답변으로 채택해서는 안 되며(MUST NOT), bounded 원문은 예산 실패 판정 전에 보존해야 한다(SHALL). 진행 중 동기 호출의 강제 취소나 원격 추론 중단을 보장해서는 안 된다(MUST NOT).

전송 timeout·연결 오류·단계 예산·전체 예산을 구분하고 실제 시도 수·경과 시간·적용 설정·원문·checkpoint를 남겨야 한다(SHALL). 현재 manifest에는 실행 설정과 경과 시간을 명시적으로 기록해야 하며 시간 설정이 canonical input이나 prompt 내용을 바꾸어서는 안 된다(MUST NOT).

#### Scenario: Explicit phase settings override common timeout

- **WHEN** 공통 timeout과 연결·읽기 설정이 함께 제공될 때
- **THEN** 명시된 세부 설정이 우선하고 생략된 값만 공통 timeout을 사용해야 한다(SHALL).
- **AND** 음수·0·비유한 예산은 호출 전에 거부해야 한다(SHALL).

#### Scenario: Retries stop at the remaining budget

- **WHEN** retry 또는 backoff를 위한 시간이 남지 않았을 때
- **THEN** 추가 시도 없이 실제 횟수와 예산 소진을 반환해야 한다(SHALL).

#### Scenario: Late text remains available for diagnosis

- **WHEN** 단계 또는 전체 예산을 넘긴 뒤 bounded 응답이 반환될 때
- **THEN** 원문과 실패 checkpoint를 보존하고 후속 호출과 completed 채택을 중단해야 한다(SHALL).

#### Scenario: Workflow expires between stages

- **WHEN** 완료 단계 저장 뒤 전체 예산이 소진될 때
- **THEN** 다음 단계 호출 수를 0으로 기록하고 이전 기록을 유지해야 한다(SHALL).

#### Scenario: Transport timeout differs from a connection failure

- **WHEN** SDK가 timeout 예외를 반환할 때
- **THEN** 연결 오류와 다른 `provider_timeout` 코드로 기록해야 한다(SHALL).

### Requirement: Local provider response retention

Runtime이 반환한 bounded 응답은 수집 실패 여부를 판정하기 전에 `HMDA_RELIABILITY_ARTIFACTS_DIR/agentic-review/responses/<workflow_id>-<stage_id>.txt`에 저장해야 한다(SHALL). UTF-8 bytes가 정확히 같아야 하며 개행 추가·공백 제거·JSON 재직렬화를 해서는 안 된다(MUST NOT). 빈 본문도 0-byte 파일로 남겨야 한다(SHALL).

파일은 bounded·private·atomic·create-only로 저장하고 기존 원문이나 workflow identity를 덮어써서는 안 된다(MUST NOT). 원문 저장 실패는 `provenance_failed / stage_response_write_failed`로 종료해야 한다(SHALL). 이후 저장이 실패해도 이미 회수 가능한 response 경로를 유지해야 한다(SHALL). 원문은 stage metadata·진단·자동 콘솔 로그·logger·외부 projection에 넣어서는 안 된다(MUST NOT).

#### Scenario: Invalid stage text remains inspectable

- **WHEN** 빈 본문 또는 알려진 미완료 응답이 반환될 때
- **THEN** 판정 전에 파일을 저장하고 stage의 `response_path`에서 원래 bytes를 읽을 수 있어야 한다(SHALL).

#### Scenario: Capture is bounded and create-only

- **WHEN** 본문이 UTF-8 byte cap을 넘거나 identity 충돌 또는 쓰기 실패가 발생할 때
- **THEN** 기존 파일을 보존하고 정제된 failure를 반환해야 한다(SHALL).

#### Scenario: Later persistence fails after response capture

- **WHEN** 원문 저장 뒤 stage record·output·manifest 저장이 실패할 때
- **THEN** 이미 저장된 원문과 이전 checkpoint 경로를 가능한 범위에서 제공해야 한다(SHALL).

#### Scenario: Unavailable calls have no response file

- **WHEN** preflight가 거부되거나 Runtime이 본문 없이 실패할 때
- **THEN** 해당 단계의 `response_path`는 null이어야 한다(SHALL).

### Requirement: Staged review provenance and failure retention

시스템은 workflow·stage identity, project revision·적용 설정·canonical input, 요청·응답 digest·상태·usage·attempt·latency·예산·원문 경로와 코드 조립 output digest를 연결해야 한다(SHALL). Metadata에 API key·raw prompt·provider exception·답변 본문을 넣어서는 안 된다(MUST NOT). 원문과 코드 조립 JSON의 출처를 구별해야 한다(SHALL).

Workflow directory를 provider 호출 전에 독점 reservation하고 stage record·output·manifest를 bounded create-only atomic private 파일로 저장해야 한다(SHALL). 현재 workflow 또는 raw 경로 충돌을 호출 전에 거부하고 저장 실패는 `provenance_failed`로 정규화해야 한다(SHALL). 실패 시 이전 파일을 덮어쓰거나 삭제해서는 안 된다(MUST NOT). 호출 수는 세 단계와 per-call retry 한도로 제한해야 한다(SHALL).

#### Scenario: A later failure preserves earlier evidence

- **WHEN** 첫 단계 저장 뒤 두 번째 단계가 실패할 때
- **THEN** 이전 원문·digest·checkpoint와 반환된 두 번째 원문·failure를 보존하고 세 번째 호출을 생략해야 한다(SHALL).

#### Scenario: Collection or manifest persistence fails

- **WHEN** 원문 저장 뒤 output 또는 manifest 쓰기가 실패할 때
- **THEN** 성공을 반환하지 않고 이전 기록과 생성된 경로를 보존해야 한다(SHALL).

#### Scenario: Credentials and raw text stay out of metadata

- **WHEN** metadata를 저장하거나 콘솔에 위치를 출력할 때
- **THEN** credential·provider exception·답변 본문을 포함하지 않아야 한다(SHALL).
- **AND** 사용자가 연 raw 파일과 collection JSON에서 답변을 확인할 수 있어야 한다(SHALL).

### Requirement: Versioned human utility evaluation

시스템은 `StagedReviewOutput`의 검토 가치를 immutable `rubric_v1`과 `ReviewValueAssessment`로 평가해야 한다(SHALL). `added_value`, `actionability`, `evidence_awareness`, `uncertainty_handling`, `prioritization`의 다섯 criterion마다 0–2 human score와 non-empty rationale이 있어야 한다(SHALL). 자동 LLM judge나 외부 평가 플랫폼이 품질 평가 권한을 대신해서는 안 된다(MUST NOT). `workflow_id`·case·revision과 원문을 포함한 output digest로 대상 결과를 식별해야 한다(SHALL).

#### Scenario: Rubric scores all utility dimensions

- **WHEN** 사람이 현재 세 단계 output을 평가할 때
- **THEN** 다섯 점수와 근거 및 정확한 평가 대상을 기록해야 한다(SHALL).

#### Scenario: Rubric fixtures distinguish utility from restatement and hedging

- **WHEN** positive·단순 재서술·실행 가능한 다음 판단이 없는 hedging control을 비교할 때
- **THEN** 추가 가치와 행동 가능성의 차이를 구분하고 fixture 점수를 실제 human 품질 증거로 취급해서는 안 된다(MUST NOT).

### Requirement: Baseline and candidate utility comparison evidence

시스템은 같은 retained case/version·rubric·project revision·deterministic facts에서 평가한 baseline/candidate `StagedReviewOutput`을 immutable `ReviewValueComparisonEvidence`로 비교할 수 있어야 한다(SHALL). 각 `workflow_id`, output digest, change-under-test, 다섯 criterion delta, total과 human `accept`·`reject`·`no_change` 및 rationale을 연결해야 한다(SHALL). Digest는 canonical JSON의 단계 순서·원문 공백·개행까지 식별하고 manifest의 output digest와 같은 결과를 가리켜야 한다(SHALL).

비교 조건과 attribution이 맞지 않으면 `blocked` 또는 `inconclusive`로 기록하고 candidate를 accept하거나 baseline으로 승격해서는 안 된다(MUST NOT). 동일한 immutable `workflow_id`가 서로 다른 output digest를 가리키면 `workflow_output_conflict`로 차단해야 하며(SHALL), 같은 workflow와 같은 digest의 비교는 human `no_change` 판단을 기록할 수 있다. 과거 invocation 기반 serialized shape를 읽거나 현재 workflow 결과로 자동 변환하는 호환 loader를 제공해서는 안 된다(MUST NOT).

#### Scenario: Same case and rubric are compared

- **WHEN** 양쪽 평가가 같은 case/version·rubric·facts·revision을 만족할 때
- **THEN** workflow identity·원문 digest·score delta·human decision을 복원할 수 있어야 한다(SHALL).

#### Scenario: Mismatched or incomplete comparison is blocked

- **WHEN** role·case·rubric·score·facts·revision이 맞지 않을 때
- **THEN** invalid 또는 blocked/inconclusive로 남고 acceptance를 허용해서는 안 된다(MUST NOT).

#### Scenario: Current comparison retains exact staged text

- **WHEN** 현재 comparison을 serialize한 뒤 다시 읽을 때
- **THEN** workflow identity·rubric·단계 원문·순서·output digest를 그대로 보존해야 한다(SHALL).

### Requirement: Advisory and read-only boundary

Review의 filesystem mutation은 로컬 workflow·stage·원문·collection 파일의 create-only write로 한정해야 한다(SHALL). 모든 status에서 Incident truth·Evidence·draft·RecoveryProposal·Approval·recovery state·data/database를 변경해서는 안 된다(MUST NOT). 모델 답변을 실행 명령이나 approval·recovery 권한으로 승격해서는 안 된다(MUST NOT).

#### Scenario: Completed review does not mutate reliability state

- **WHEN** 검토가 completed되고 기록이 저장될 때
- **THEN** 근거·draft·target data와 recovery/approval state는 호출 전과 같아야 한다(SHALL).

#### Scenario: Action-like advisory remains non-executable

- **WHEN** 모델 답변이 approval 또는 실행 명령처럼 읽힐 때
- **THEN** typed Approval·RecoveryProposal·mutation request를 만들거나 executor를 호출해서는 안 된다(MUST NOT).

#### Scenario: Rejected or unavailable review remains contained

- **WHEN** input·provider·응답 수집 또는 provenance가 실패할 때
- **THEN** typed failure와 로컬 근거로 격리하고 deterministic 결과와 target data를 보존해야 한다(SHALL).

### Requirement: Deterministic and adversarial evaluation

Offline suite는 provider network 없이 input snapshot·canonical projection·context bounds·단계 순서와 history·코드 조립 facts·typed failure·예산·원문·provenance·권한 분리를 반복 검증해야 한다(SHALL). JSON 응답 파싱이나 자연어 의미를 현재 acceptance oracle로 사용해서는 안 된다(MUST NOT). 수치 설명과 검토 가치의 oracle은 기존 모델 답변을 정답으로 취급하지 않고 독립적인 사례 기대값과 human rubric으로 다뤄야 한다(SHALL).

실제 모델 생성은 별도 opt-in live 경로로 확인하고 offline 통과나 completed만으로 현재 revision의 한국어 준수·정확성·검토 가치를 주장해서는 안 된다(MUST NOT).

#### Scenario: Offline staged collection evaluation

- **WHEN** fake 응답으로 정상·빈 본문·미완료·크기·시간·저장 실패를 반복 검증할 때
- **THEN** 같은 입력은 같은 facts·상태·failure를 만들고 원본과 target state를 변경하지 않아야 한다(SHALL).

#### Scenario: Free-text variation does not change canonical facts

- **WHEN** 모델 문구만 바뀔 때
- **THEN** 코드는 같은 input identity와 facts를 취합하고 바뀐 원문만 그대로 보존해야 한다(SHALL).

#### Scenario: Prompt injection is data, not instruction

- **WHEN** input 또는 이전 답변에 prompt-injection-like 문장이 있을 때
- **THEN** 단계 선택·system 지시·실행 권한을 바꾸지 않고 untrusted data로 유지해야 한다(SHALL).

#### Scenario: Ollama live proof

- **WHEN** 명시적으로 활성화한 live 경로에 합성 사례와 접근 가능한 endpoint를 제공할 때
- **THEN** 현재 세 단계 결과 또는 typed failure와 revision·설정·입력·digest·원문·attempt·latency를 보존해야 한다(SHALL).

## ADDED Requirements

### Requirement: Current review surface

현재 package와 배포 wheel은 버전별 JSON 검토 service·prompt snapshot·renderer·출력 계약·파서·validator·invocation reader 및 그 결과 전용 Langfuse projection을 제공해서는 안 된다(MUST NOT). 일반 API와 CLI에는 mode·prompt version 선택, 호환 alias, 이전 설정을 해석하는 guard 또는 자동 fallback을 두어서는 안 된다(MUST NOT). Shared input·bounded context·현재 raw 저장·runtime adapter는 유지해야 한다(SHALL).

CLI는 현재 실행에 필요한 활성화·provider·byte/token limit·시간 예산·artifact 설정만 읽어야 한다(SHALL). `HMDA_AGENTIC_REVIEW_MODE`, `HMDA_AGENTIC_REVIEW_PROMPT_VERSION`, `HMDA_AGENTIC_REVIEW_LEGACY_PROMPT_VERSION`과 과거 projection 선택을 읽어서는 안 된다(MUST NOT).

#### Scenario: Current API has one execution contract

- **WHEN** 일반 공개 API 또는 live CLI를 호출할 때
- **THEN** prompt version 인자 없이 현재 세 단계 실행만 제공해야 한다(SHALL).

#### Scenario: Distribution excludes retired implementations

- **WHEN** package를 설치하거나 공개 API를 import할 때
- **THEN** 삭제된 version snapshot·실행·출력·reader·projection을 import하거나 실행할 수 없어야 한다(SHALL).

#### Scenario: Historical artifacts remain external evidence

- **WHEN** 현재 실행만 남기기 위해 source와 배포 리소스를 정리할 때
- **THEN** 기존 로컬 artifact와 역사 문서를 삭제하거나 현재 기록으로 다시 쓰지 않아야 한다(SHALL).
- **AND** 과거 record를 읽는 호환 API를 현재 package에 남겨서는 안 된다(MUST NOT).

## REMOVED Requirements

### Requirement: Opt-in grounded review instructions

**Reason:** 현재 한국어 단계별 텍스트 실행으로 통일하며 과거 JSON 응답·버전·검증·기록·projection 지원을 삭제한다.

**Migration:** 현재 API와 StagedReviewOutput·workflow provenance를 사용한다. 과거 파일은 보존하되 현재 package에서 호환 실행·reader를 제공하지 않는다.

### Requirement: Structured advisory review output

**Reason:** 현재 한국어 단계별 텍스트 실행으로 통일하며 과거 JSON 응답·버전·검증·기록·projection 지원을 삭제한다.

**Migration:** 현재 API와 StagedReviewOutput·workflow provenance를 사용한다. 과거 파일은 보존하되 현재 package에서 호환 실행·reader를 제공하지 않는다.

### Requirement: Versioned validation provenance compatibility

**Reason:** 현재 한국어 단계별 텍스트 실행으로 통일하며 과거 JSON 응답·버전·검증·기록·projection 지원을 삭제한다.

**Migration:** 현재 API와 StagedReviewOutput·workflow provenance를 사용한다. 과거 파일은 보존하되 현재 package에서 호환 실행·reader를 제공하지 않는다.

### Requirement: Optional synthetic invocation projection

**Reason:** 현재 한국어 단계별 텍스트 실행으로 통일하며 과거 JSON 응답·버전·검증·기록·projection 지원을 삭제한다.

**Migration:** 현재 API와 StagedReviewOutput·workflow provenance를 사용한다. 과거 파일은 보존하되 현재 package에서 호환 실행·reader를 제공하지 않는다.

### Requirement: Integration-local human annotation mapping

**Reason:** 현재 한국어 단계별 텍스트 실행으로 통일하며 과거 JSON 응답·버전·검증·기록·projection 지원을 삭제한다.

**Migration:** 현재 API와 StagedReviewOutput·workflow provenance를 사용한다. 과거 파일은 보존하되 현재 package에서 호환 실행·reader를 제공하지 않는다.

### Requirement: Deterministic review validation

**Reason:** 현재 한국어 단계별 텍스트 실행으로 통일하며 과거 JSON 응답·버전·검증·기록·projection 지원을 삭제한다.

**Migration:** 현재 API와 StagedReviewOutput·workflow provenance를 사용한다. 과거 파일은 보존하되 현재 package에서 호환 실행·reader를 제공하지 않는다.

### Requirement: Bounded response failure diagnostics

**Reason:** 현재 한국어 단계별 텍스트 실행으로 통일하며 과거 JSON 응답·버전·검증·기록·projection 지원을 삭제한다.

**Migration:** 현재 API와 StagedReviewOutput·workflow provenance를 사용한다. 과거 파일은 보존하되 현재 package에서 호환 실행·reader를 제공하지 않는다.

### Requirement: Durable invocation evidence

**Reason:** 현재 한국어 단계별 텍스트 실행으로 통일하며 과거 JSON 응답·버전·검증·기록·projection 지원을 삭제한다.

**Migration:** 현재 API와 StagedReviewOutput·workflow provenance를 사용한다. 과거 파일은 보존하되 현재 package에서 호환 실행·reader를 제공하지 않는다.
