# reliability-agentic-review Specification

## Purpose

`null_spike`의 결정론적 사실과 제공된 근거를 고정한 채 LLM의 한국어 검토를 단계별로 수집한다. 모델 답변은 원문으로 보존하고, 입력 식별자·수치·단계 답변을 코드로 JSON에 결합한다. `completed`는 수집과 저장의 완료이며 사실성, 검토 가치 또는 사람의 승인을 뜻하지 않는다.

현재 API와 CLI는 이 단계 실행과 명시적으로 활성화하는 native 합성 평가를 제공한다. 과거 JSON 응답용 실행·프롬프트·파서·검증기·기록 reader·외부 projection은 제공하지 않는다. 과거 실행의 파일과 Git 기록은 삭제하거나 현재 결과로 재작성하지 않는다.

## Requirements

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

### Requirement: Current review surface

현재 package와 배포 wheel은 버전별 JSON 검토 service·prompt snapshot·renderer·출력 계약·파서·validator·invocation reader 및 그 결과 전용 Langfuse projection을 제공해서는 안 된다(MUST NOT). 일반 API와 CLI에는 mode·prompt version 선택, 호환 alias, 이전 설정을 해석하는 guard 또는 자동 fallback을 두어서는 안 된다(MUST NOT). Shared input·bounded context·현재 raw 저장·runtime adapter는 유지해야 한다(SHALL).

기존 live CLI는 현재 실행 설정을 유지하고 native 평가 경계에서만 명시적 opt-in과 SDK·Dataset·experiment·외부 대기 설정을 읽어야 한다(SHALL). 비활성 실행과 일반 import는 optional SDK나 원격 연결을 요구해서는 안 된다(MUST NOT). `HMDA_AGENTIC_REVIEW_MODE`, `HMDA_AGENTIC_REVIEW_PROMPT_VERSION`, `HMDA_AGENTIC_REVIEW_LEGACY_PROMPT_VERSION`과 과거 projection 선택을 읽어서는 안 된다(MUST NOT).

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

파일은 bounded·private·atomic·create-only로 저장하고 기존 원문이나 workflow identity를 덮어써서는 안 된다(MUST NOT). 원문 저장 실패는 `provenance_failed / stage_response_write_failed`로 종료해야 한다(SHALL). 이후 저장이 실패해도 이미 회수 가능한 response 경로를 유지해야 한다(SHALL). 원문은 stage metadata·진단·자동 콘솔 로그·logger에 넣어서는 안 된다(MUST NOT). 명시적으로 활성화한 native 합성 평가에서 검증된 사례·단계 텍스트·collection의 허용 필드만 원격 input/output에 보낼 수 있다. Metadata에는 본문을 복제해서는 안 되며(MUST NOT), credential·개인 절대 경로·provider 예외·전체 설정 object는 전송해서는 안 된다(MUST NOT).

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

시스템은 현재 `StagedReviewOutput`의 사람 평가와 결과 표시에 Langfuse native Score Config·annotation·Annotation Queue를 사용해야 한다(SHALL). `rubric_v1`의 `added_value`, `actionability`, `evidence_awareness`, `uncertainty_handling`, `prioritization`의 의미와 사람의 명시적 판단은 유지하고 로컬 ReviewValue 평가·합계·비교 저장 모델이나 Markdown 평가 보고서를 중복 제공해서는 안 된다(MUST NOT).

각 기준은 0·1·2에 대응하는 고정 categorical 선택지와 Config ID·설정 snapshot으로 식별하고, 읽어 온 값은 정확한 범주와 일치해야 한다(SHALL). 점수만 입력하거나 Queue 완료 표시만으로 사람 평가가 완비됐다고 판단해서는 안 된다(MUST NOT). 프로젝트의 얇은 검사는 같은 검토자·case/version·rubric·workflow/output에 다섯 기준이 각각 정확히 한 번 있고, 공백이 아닌 comment/rationale과 확인 가능한 사람 annotation source·작성자·시각이 연결됐는지 확인해야 한다(SHALL). 누락·중복·충돌·소수·boolean·알 수 없는 범주·잘못된 Config나 대상 연결은 미완료로 남겨야 한다(SHALL).

평가 대상은 검증한 실제 workflow·원문을 포함한 output digest와 연결해야 한다(SHALL). SDK/API 또는 자동 evaluator 점수를 사람의 독립 평가로 취급하거나 점수로 사람의 채택 결정을 생성해서는 안 된다(MUST NOT). 서버에서 확인할 수 없는 작성자·원격 상태·사람 평가를 합성 값으로 채워 완료 처리해서는 안 된다(MUST NOT).

#### Scenario: Rubric scores all utility dimensions

- **WHEN** 사람이 현재 output에 native 점수와 comment를 입력할 때
- **THEN** 다섯 고정 Config·정확한 범주·non-empty 사유·검토자와 exact 대상 연결이 모두 확인된 경우에만 평가 완비로 표시해야 한다(SHALL).

#### Scenario: Rubric fixtures distinguish utility from restatement and hedging

- **WHEN** positive·재서술·hedging의 합성 control과 점수 fixture로 계약을 검사할 때
- **THEN** 독립 oracle과 control의 구별력은 유지하고 이를 실제 모델 결과나 사람의 평가로 기록해서는 안 된다(MUST NOT).

### Requirement: Baseline and candidate utility comparison evidence

시스템은 Langfuse native experiment 비교 화면과 사람 annotation을 이용해 baseline/candidate를 대조해야 한다(SHALL). 동일 retained case/version·사례 payload digest·rubric/Config snapshot과 의도한 변경 변수 및 양쪽 실제 실행 조건을 연결해야 한다(SHALL). 코드 revision이 의도한 변경 변수이면 서로 다른 실제 SHA를 허용하고, 같은 revision 조건을 맞추려고 SHA·ID·canonical input 또는 digest를 재작성해서는 안 된다(MUST NOT).

각 실행은 실제 canonical input 본문 그대로의 digest, 실제 project revision, workflow·trace·observation·experiment identity와 output digest를 보존해야 한다(SHALL). 사례 payload digest는 실행 출처를 제외한 고정 사례 자료의 동일성을 나타내며 실제 canonical input digest와 구분해야 한다(SHALL). 서로 다른 실제 canonical digest를 같은 값으로 강요하거나 기존 입력에 없는 provenance 필드를 있다고 가정해서는 안 된다(MUST NOT).

프로젝트에는 사례·평가 기준·workflow/output 연결 무결성과 사람 annotation의 완비 검사만 남겨야 한다(SHALL). 로컬 `ReviewValueComparisonEvidence`·criterion delta·합계·별도 비교 Markdown이나 그 호환 loader를 제공해서는 안 된다(MUST NOT). 같은 workflow가 다른 output digest를 가리키면 `workflow_output_conflict`로 차단하고, 사례나 rubric 또는 의도하지 않은 비교 조건이 다르면 직접 개선 비교를 보류해야 한다(SHALL).

채택 의견은 candidate에 연결된 별도 native categorical `accept`·`reject`·`no_change`와 사람의 사유로 기록하고 양쪽 run·output digest를 식별해야 한다(SHALL). 점수 평균·합계·Queue 완료를 채택 의견으로 자동 변환하거나 GitHub 승인·병합·recovery 권한으로 사용해서는 안 된다(MUST NOT). 실패·누락·미평가 사례도 비교 분모에서 제외하지 않아야 한다(SHALL).

#### Scenario: Same case and rubric are compared

- **WHEN** 같은 사례·rubric에서 명시한 변경 변수에 따라 두 실행을 비교할 때
- **THEN** 실제 두 revision·run·workflow·digest와 사람 의견을 그대로 식별하고 의도한 코드 변경의 revision 차이를 허용해야 한다(SHALL).

#### Scenario: Mismatched or incomplete comparison is blocked

- **WHEN** 사례 payload·rubric·원문 digest·workflow 연결이 다르거나 사람 annotation과 의견이 완비되지 않았을 때
- **THEN** 연결 충돌 또는 평가 미완료로 남기고 candidate 채택이나 baseline 승격의 증거로 사용해서는 안 된다(MUST NOT).

#### Scenario: Current comparison retains exact staged text

- **WHEN** 검토자가 native compare 화면에서 양쪽 결과를 읽을 때
- **THEN** 각 실제 input·단계 원문·output digest를 로컬 provenance와 연결하고 별도 로컬 평가 serialization을 요구하지 않아야 한다(SHALL).

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

### Requirement: Evaluation-owned live validation entrypoint

실제 provider로 합성 사례를 검증하는 CLI는 `python -m hmda_reliability.review_ai.evaluation.live`로 제공해야 한다(SHALL). 기존 `scripts/run_agentic_review_live.py`와 그 호환 wrapper를 제공해서는 안 된다(MUST NOT). 검증은 실제 데이터 적재 없이 현재 한국어 세 단계·코드 JSON 취합을 사용하고 명시적 live opt-in·설정 검증·시간 예산·원문 보존·provenance 검사와 기존 종료 의미를 유지해야 한다(SHALL).

진행 표시는 표준 오류에만 기록하고 표준 출력의 최종 JSON shape와 의미를 변경해서는 안 된다(MUST NOT). 모듈 import 또는 비활성 실행만으로 provider를 호출해서는 안 된다(MUST NOT). 실행 완료와 진행 표시는 실제 출력의 정확성·한국어 준수·사람의 rubric 평가를 대신해서는 안 된다(MUST NOT).

자동 revision은 실제 import한 모듈이 속한 source checkout의 HEAD와 clean tracked tree를 검증해야 하며 caller의 다른 working directory를 그 source로 기록해서는 안 된다(MUST NOT). 배포 설치처럼 해당 checkout을 입증할 수 없으면 auto를 거부하고 명시적 revision을 요구해야 한다(SHALL).

#### Scenario: Module execution preserves the live result

- **WHEN** 사용자가 live opt-in과 유효 설정으로 새 모듈을 실행할 때
- **THEN** 현재 합성 사례의 세 단계 실행·저장·provenance 검증을 수행하고 기존 최종 JSON과 종료 의미를 유지해야 한다(SHALL).
- **AND** 기존 script 또는 wrapper를 실행 경로로 남겨서는 안 된다(MUST NOT).

#### Scenario: Import and disabled execution do not call a provider

- **WHEN** 모듈을 import하거나 live opt-in 없이 실행할 때
- **THEN** provider 호출과 heartbeat 실행을 시작해서는 안 된다(MUST NOT).

#### Scenario: Automatic revision identifies the loaded source checkout

- **WHEN** source checkout의 모듈을 다른 working directory에서 auto revision으로 실행할 때
- **THEN** 실제 모듈 소유 checkout의 HEAD·clean tree만 사용하고 다른 repository의 revision을 기록해서는 안 된다(MUST NOT).

#### Scenario: Installed code requires explicit revision provenance

- **WHEN** source checkout을 입증할 수 없는 배포 모듈에서 auto revision을 요청할 때
- **THEN** provider 호출 전에 정제된 설정 오류로 종료하고 명시적 revision을 요구해야 한다(SHALL).

### Requirement: Safe live stage progress

Live 검증은 표준 오류에 현재 단계의 한국어 이름·시작·완료 또는 실패·단계 경과 시간을 표시해야 한다(SHALL). 완료·실패 표시는 원문과 checkpoint 저장을 포함한 실제 단계 결과에 맞춰야 하며 provider 반환만으로 단계 완료를 표시해서는 안 된다(MUST NOT).

동기 provider 호출의 로컬 대기 중에는 기본 5초 간격으로 해당 단계와 로컬 경과 시간을 표시해야 한다(SHALL). 이 대기에는 logical call 내부의 bounded retry·backoff가 포함된다. 대기 표시는 provider 내부 진행률·생성 토큰 수·성공 예상이나 원격 추론 완료를 뜻한다고 표현해서는 안 된다(MUST NOT). Provider 호출 전 준비·후속 저장 및 실행 종료 후에는 provider 대기 heartbeat를 표시해서는 안 된다(MUST NOT).

진행 자료는 고정 단계·사건·상태와 로컬 경과 시간으로 한정해야 한다(SHALL). 원문·prompt·API key·사용자 설정값·개인 절대 경로·예외 문구를 진행 로그에 포함해서는 안 된다(MUST NOT). 일반 API는 관찰자를 명시하지 않으면 콘솔 출력과 heartbeat를 생성해서는 안 되며(MUST NOT), 관찰자 실패가 실행 결과·원문·provenance 보존을 변경해서는 안 된다(MUST NOT).

Provider 정상 반환·typed failure·예상하지 못한 예외·중단의 모든 종료 경로에서 대기 timer와 진행 자원을 정리하고 종료 후 로그가 계속 나와서는 안 된다(MUST NOT).

#### Scenario: Stage progress follows retained results

- **WHEN** 정상 단계가 시작되고 원문과 checkpoint 저장을 마칠 때
- **THEN** 한국어 단계 시작과 경과 시간을 포함한 완료를 순서대로 표시해야 한다(SHALL).
- **AND** provider 응답 이후 저장이 실패하면 완료 대신 실패를 표시해야 한다(SHALL).

#### Scenario: Heartbeats cover only synchronous provider waiting

- **WHEN** provider logical call이 기본 간격을 넘겨 계속 대기 중일 때
- **THEN** 5초마다 로컬 대기 시간을 표시하고 provider 호출 종료 시 heartbeat를 중단해야 한다(SHALL).
- **AND** 출력에 provider 내부 진행률이나 완료 예측을 포함해서는 안 된다(MUST NOT).

#### Scenario: Failed stage stops subsequent progress

- **WHEN** provider·응답 수집·시간 예산 또는 checkpoint 저장으로 단계가 실패할 때
- **THEN** 해당 단계 실패와 경과 시간을 표시하고 호출하지 않은 후속 단계의 시작·완료를 표시해서는 안 된다(MUST NOT).

#### Scenario: Unexpected exits release progress resources

- **WHEN** provider 대기 중 예외 또는 중단으로 제어가 빠져나갈 때
- **THEN** timer를 중지·정리하고 원문·예외 문구를 진행 로그에 추가하거나 종료 뒤 heartbeat를 출력해서는 안 된다(MUST NOT).

#### Scenario: Progress cannot leak input or alter evidence

- **WHEN** 원문·설정·오류에 민감한 문자열이 있거나 관찰자 자체가 실패할 때
- **THEN** 진행 로그는 고정 자료와 시간만 표시하고 관찰 실패로 provider 결과나 저장 근거를 바꾸어서는 안 된다(MUST NOT).

#### Scenario: Ordinary API calls stay silent

- **WHEN** 일반 검토 API를 관찰자 없이 실행할 때
- **THEN** 기존 결과와 저장 경계를 유지하고 단계 로그와 heartbeat 자원을 만들지 않아야 한다(SHALL).

### Requirement: Native synthetic dataset experiments

Native 평가 진입점은 `python -m hmda_reliability.review_ai.evaluation.experiment`로 제공하고 `HMDA_LANGFUSE_ENABLED=true`와 `HMDA_AGENTIC_REVIEW_LIVE=true`를 모두 명시한 경우에만 실행해야 한다(SHALL). 기존 live 모듈의 단일 합성 실행은 유지해야 한다(SHALL). SDK에는 `LANGFUSE_BASE_URL`·`LANGFUSE_PUBLIC_KEY`·`LANGFUSE_SECRET_KEY`를 제공하고 설정값을 콘솔이나 관측 metadata에 복제해서는 안 된다(MUST NOT).

명시적으로 활성화한 native 평가는 version과 item identity를 고정한 세 합성 사례의 Dataset을 SDK experiment task로 실행해야 한다(SHALL). Task는 허용된 사례 자료만 기존 세 단계 검토 함수에 전달하고 corpus의 revision 표식 대신 실제 실행 SHA를 provenance로 사용해야 한다(SHALL). `expected_output`·oracle·controls·사람 평가 질문을 모델 입력이나 대화 history에 넣어서는 안 된다(MUST NOT).

최초 실행은 사례를 직렬 처리하고 세 단계 순서·한국어 모듈·Runtime retry·byte/token limit·단계/전체 예산·원문 보존·checkpoint·코드 JSON 취합을 유지해야 한다(SHALL). SDK task나 전송 실패 때문에 모델 호출을 중복 재시도해서는 안 된다(MUST NOT). Dataset item upsert로 사례 변경을 숨기거나 같은 item의 반복을 같은 experiment 결과로 덮어써서는 안 된다(MUST NOT). 반복마다 별도 run identity와 모든 시도·실패 기록을 남겨야 한다(SHALL).

#### Scenario: A dataset task uses the existing review workflow

- **WHEN** 고정된 합성 Dataset item을 SDK task로 실행할 때
- **THEN** 기존 세 단계와 로컬 기록을 사용하고 oracle·기대값·controls는 provider에 전달하지 않아야 한다(SHALL).

#### Scenario: Changed items or repeated attempts remain identifiable

- **WHEN** 사례 payload가 바뀌거나 같은 사례를 반복 실행할 때
- **THEN** 고정 version·payload digest와 별도 run identity로 구분하고 이전 결과나 실패를 덮어써서는 안 된다(MUST NOT).

#### Scenario: Disabled evaluation stays offline

- **WHEN** native 평가 opt-in이 없거나 기본 suite를 실행할 때
- **THEN** optional SDK import·초기화·원격 호출·실제 모델 호출을 요구해서는 안 된다(MUST NOT).

### Requirement: Verified model IO observation linkage

Native 평가는 검증한 로컬 manifest·checkpoint·원문·collection에서 사례 trace와 세 단계 observation을 연결해야 한다(SHALL). 실제 canonical input·사례 payload·workflow/output digest 및 project revision의 일치 여부를 검사한 뒤 허용된 합성 본문만 명시적 input/output으로 전달해야 한다(SHALL). 단계 input은 bounded canonical input과 완료된 이전 assistant 답변으로 한정하고 system prompt 본문은 보내지 않으며 prompt digest만 연결해야 한다(SHALL). Metadata에는 식별자·digest·고정 status·검증된 설정만 두고 prompt·답변·credential·개인 경로·예외 원문을 포함해서는 안 된다(MUST NOT).

SDK의 자동 캡처에 전체 함수 인자나 설정 object를 넘겨서는 안 된다(MUST NOT). 본문 없는 progress callback을 raw 전송 채널로 확대하거나 다른 provider 경로를 만들어서는 안 된다(MUST NOT). 본문이 없는 실패에 답변을 만들거나 실패 stage를 성공 observation으로 표시해서는 안 된다(MUST NOT). 이미 반환·저장된 실패 단계의 bounded 텍스트는 실패 상태를 유지한 input/output으로만 보여야 한다(SHALL).

#### Scenario: Native observations match retained outputs

- **WHEN** 로컬 검토 결과를 원격 관측에 연결할 때
- **THEN** 실제 workflow·원문·digest를 대조하고 사례와 세 단계의 실제 상태·본문을 일치시켜야 한다(SHALL).

#### Scenario: A missing body cannot become a successful answer

- **WHEN** provider가 본문 없이 실패하거나 stage가 미완료로 끝날 때
- **THEN** 보존된 단계·typed failure만 표시하고 답변 또는 성공을 합성해서는 안 된다(MUST NOT).

#### Scenario: IO allowlists exclude private metadata

- **WHEN** SDK 관측이나 로그를 구성할 때
- **THEN** 허용된 합성 본문을 input/output으로만 전달하고 metadata·자동 캡처·오류 출력에서 credential·예외·개인 경로·전체 설정을 제외해야 한다(SHALL).

### Requirement: Independent bounded external evaluation IO

Native SDK·인증·Dataset 등록/조회·전송·flush 실패는 로컬 검토 status·원문·manifest·exit 의미와 분리해야 한다(SHALL). 추가 외부 I/O에는 `HMDA_LANGFUSE_IO_TIMEOUT_SECONDS`로 기본 30초·허용 범위 1–300초의 대기 한도를 적용해야 한다(SHALL). 이 한도는 SDK 시작·task 사이·최종 전송 구간에 적용하고 실제 검토 함수 실행 중에는 기존 단계/전체 예산과 전송 timeout을 사용해야 한다(SHALL). 원격 실패 복구를 이유로 모델을 다시 실행하거나 기존 workflow를 변경해서는 안 된다(MUST NOT).

SDK 제출·flush 반환, 실제 원격 조회·UI 연결 확인, 사람이 작성한 평가 완비를 서로 다른 증거로 기록해야 한다(SHALL). 원격 객체가 실제로 확인되지 않으면 제출 이상의 성공을 주장해서는 안 되며(MUST NOT), 실제 사람 annotation이 없으면 품질 미검증으로 남겨야 한다(SHALL). SDK 예외는 안전한 분류만 표시하고 원문을 노출해서는 안 된다(MUST NOT).

#### Scenario: External failure preserves a local result

- **WHEN** core 결과 보존 뒤 외부 인증·네트워크·flush 또는 대기 한도가 실패할 때
- **THEN** core status와 파일을 보존하고 별도 외부 상태를 반환하며 모델을 재호출해서는 안 된다(MUST NOT).

#### Scenario: Submission is distinct from verified remote evaluation

- **WHEN** SDK가 오류 없이 반환했지만 실제 원격 조회나 사람 평가를 확인하지 않았을 때
- **THEN** 제출 상태만 기록하고 원격 적재·UI·사람 품질 검증을 완료로 표시해서는 안 된다(MUST NOT).
