# reliability-agentic-review Specification

## Purpose

`null_spike`의 결정론적 사실과 제공된 근거를 고정한 채 LLM의 한국어 검토를 단계별로 수집한다. 모델 답변은 원문으로 보존하고, 입력 식별자·수치·단계 답변을 코드로 JSON에 결합한다. `completed`는 수집과 저장의 완료이며 사실성, 검토 가치 또는 사람의 승인을 뜻하지 않는다.

현재 API와 CLI는 Langfuse native 프롬프트·합성 Dataset 실험과 이 단계 실행을 제공한다. 과거 JSON 응답용 실행·프롬프트·파서·검증기·기록 reader·외부 projection은 제공하지 않는다. 과거 실행의 파일과 Git 기록은 삭제하거나 현재 결과로 재작성하지 않는다.

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

일반 `review_null_spike` API·직접 service·실험 CLI는 같은 현재 실행을 사용해야 한다(SHALL). 근거 검토·초안 비판·종합을 고정 순서로 실행하고 모델에는 JSON 대신 한국어 텍스트를 요청해야 한다(SHALL). 각 호출은 원래 canonical input과 완료된 assistant 답변을 유지하고 누적 메시지 전체의 byte cap과 digest를 적용해야 한다(SHALL). 자료가 단계·system 지시를 선택해서는 안 된다(MUST NOT).

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

현재 package는 shared input·bounded context·세 단계 실행·현재 raw 저장·Runtime adapter를 제공해야 한다(SHALL). 일반 API와 실험 CLI는 Langfuse에서 읽은 현재 한국어 프롬프트를 사용하고 실행 모드·과거 v1/v2/v3·이전 환경 설정·호환 alias·로컬 프롬프트 fallback을 제공해서는 안 된다(MUST NOT). Langfuse SDK는 고정된 기본 의존성이며 import만으로 원격 연결이나 모델 호출을 시작해서는 안 된다(MUST NOT).

실제 합성 검토의 CLI는 `python -m hmda_reliability.review_ai.evaluation.experiment` 하나로 제공해야 한다(SHALL). 기존 live module·script·worker·별도 native SDK façade·사람 점수 조회 모듈과 호환 wrapper를 남겨서는 안 된다(MUST NOT). 과거 artifact·Inbox·Git 기록을 삭제하거나 현재 결과로 재작성해서는 안 된다(MUST NOT).

#### Scenario: Current API has one execution contract

- **WHEN** 일반 공개 API 또는 실험 CLI를 호출할 때
- **THEN** 같은 remote prompt 경로와 세 단계 실행을 사용하고 과거 실행 모드를 선택할 수 없어야 한다(SHALL).

#### Scenario: Imports stay offline

- **WHEN** package를 import하거나 기본 offline suite를 실행할 때
- **THEN** 원격 prompt·Dataset 조회나 모델 호출을 요구해서는 안 된다(MUST NOT).

### Requirement: Typed review result boundary

결과는 `StagedReviewResult`로 표현하고 다음 status를 구분해야 한다(SHALL).

| Status | Meaning |
| --- | --- |
| `completed` | 세 답변과 코드 조립 output 및 provenance의 저장 완료 |
| `input_rejected` | input·context 또는 누적 prompt 한도 위반으로 해당 호출 전에 종료 |
| `validation_failed` | 응답 크기·빈 본문·알려진 미완료 종료로 텍스트 수집 실패 |
| `unavailable` | remote prompt 조회·전송 실패 또는 단계·전체 예산 소진 |
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

시스템은 유한한 양수의 연결·읽기 대기 제한과 별도 단계·전체 실행 예산을 설정할 수 있어야 한다(SHALL). 공통 timeout은 생략된 세부 전송 설정의 기본값이며 명시된 연결·읽기 설정이 우선해야 한다(SHALL). 실험 시작값과 native Prompt config·명시적 설정 객체의 소유 경계를 문서화해야 한다(SHALL).

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

파일은 bounded·private·atomic·create-only로 저장하고 기존 원문이나 workflow identity를 덮어써서는 안 된다(MUST NOT). 원문 저장 실패는 `provenance_failed / stage_response_write_failed`로 종료해야 한다(SHALL). 이후 저장이 실패해도 이미 회수 가능한 response 경로를 유지해야 한다(SHALL). 원문은 stage metadata·진단·자동 콘솔 로그·logger에 넣어서는 안 된다(MUST NOT). Native 합성 평가의 실제 compiled prompt·사례·단계 텍스트·collection만 명시적인 원격 input/output에 보낼 수 있다. Metadata에는 본문을 복제하거나 credential·개인 절대 경로·provider 예외·전체 설정 object를 전송해서는 안 된다(MUST NOT).

#### Scenario: Invalid stage text remains inspectable

- **WHEN** 빈 본문 또는 알려진 미완료 응답이 반환될 때
- **THEN** 판정 전에 파일을 저장하고 stage의 `response_path`에서 원래 bytes를 읽을 수 있어야 한다(SHALL).

#### Scenario: Retained raw precedes remote output

- **WHEN** Runtime이 bounded 본문을 반환할 때
- **THEN** 원격 output 갱신 전에 로컬 원문을 저장하고 전송 장애가 이를 삭제하거나 모델 재호출을 일으켜서는 안 된다(MUST NOT).

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

사람의 `added_value`, `actionability`, `evidence_awareness`, `uncertainty_handling`, `prioritization` 평가와 명시적 채택 의견은 Langfuse native Score Config·annotation·Annotation Queue·비교 UI에서 관리해야 한다(SHALL). 로컬 ReviewValue 평가·합계·비교 저장 모델·Markdown 평가 renderer·점수 조회와 별도 완비 판정기를 제공해서는 안 된다(MUST NOT).

사람이 다섯 기준의 0·1·2 의미와 실제 출력에 근거해 판단하도록 안내해야 한다(SHALL). SDK/API·자동 evaluator 점수·Queue 완료를 사람의 독립 평가나 채택 의견으로 취급해서는 안 된다(MUST NOT). 서버에서 확인하지 않은 사람·평가·원격 상태를 합성해 완료로 기록해서는 안 된다(MUST NOT).

#### Scenario: Human evaluation uses the native UI

- **WHEN** 사람이 실제 experiment output을 평가할 때
- **THEN** UI의 Config·annotation·Queue를 사용하고 프로젝트 CLI가 점수·작성자·comment를 다시 읽어 별도 완료 판정을 만들지 않아야 한다(SHALL).

### Requirement: Baseline and candidate utility comparison evidence

Baseline/candidate는 Langfuse native experiment 비교 화면에서 동일 Dataset version·사례·평가 기준과 의도한 변경 변수를 확인해 대조해야 한다(SHALL). 실제 prompt name/version·model·project revision·workflow·실제 메시지와 output digest를 보존해야 한다(SHALL). 코드 변경이 비교 변수이면 서로 다른 실제 revision을 허용하고 같은 값으로 보이도록 출처를 재작성해서는 안 된다(MUST NOT).

별도 비교 저장 모델·점수 delta·합계·호환 loader·자동 채택 판정기를 제공해서는 안 된다(MUST NOT). 실패·누락·미평가 사례를 숨기거나 점수·Queue 완료로 GitHub 승인·병합·recovery 권한을 생성해서는 안 된다(MUST NOT).

#### Scenario: Native comparison retains real execution conditions

- **WHEN** 사람이 같은 Dataset의 두 experiment run을 비교할 때
- **THEN** 양쪽 실제 revision·prompt version·model과 실패 사례를 확인할 수 있어야 하고 도구가 채택 판단을 대신 생성해서는 안 된다(MUST NOT).

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

실제 모델 생성은 명시적인 native experiment 실행으로 확인하고 offline 통과나 completed만으로 현재 revision의 한국어 준수·정확성·검토 가치를 주장해서는 안 된다(MUST NOT).

#### Scenario: Offline staged collection evaluation

- **WHEN** fake 응답으로 정상·빈 본문·미완료·크기·시간·저장 실패를 반복 검증할 때
- **THEN** 같은 입력은 같은 facts·상태·failure를 만들고 원본과 target state를 변경하지 않아야 한다(SHALL).

#### Scenario: Free-text variation does not change canonical facts

- **WHEN** 모델 문구만 바뀔 때
- **THEN** 코드는 같은 input identity와 facts를 취합하고 바뀐 원문만 그대로 보존해야 한다(SHALL).

#### Scenario: Prompt injection is data, not instruction

- **WHEN** input 또는 이전 답변에 prompt-injection-like 문장이 있을 때
- **THEN** 단계 선택·system 지시·실행 권한을 바꾸지 않고 untrusted data로 유지해야 한다(SHALL).

#### Scenario: Ollama experiment proof

- **WHEN** 명시적으로 실행한 native experiment에 합성 사례와 접근 가능한 endpoint를 제공할 때
- **THEN** 현재 세 단계 결과 또는 typed failure와 revision·설정·입력·digest·원문·attempt·latency를 보존해야 한다(SHALL).

### Requirement: Native synthetic dataset experiments

최초 등록은 `python -m hmda_reliability.review_ai.evaluation.setup`, 반복 실행은 `python -m hmda_reliability.review_ai.evaluation.experiment`로 분리해야 한다(SHALL). 명시적인 setup 실행만 seed Prompt와 합성 Dataset을 등록하고 experiment는 기존 Dataset만 조회해야 한다(SHALL). 반복 실험에서 Dataset item·Score Config·Annotation Queue를 자동 생성·수정해서는 안 된다(MUST NOT).

실험은 Dataset 이름·run 이름·선택적 UTC Dataset version·기본 `production` prompt label을 받고 SDK `dataset.run_experiment(task=...)`와 native 결과 표시를 사용해야 한다(SHALL). Task는 사례의 허용 입력만 같은 세 단계 함수에 전달하며 `expected_output`·oracle·controls·검토자 질문을 모델 입력이나 history에 넣어서는 안 된다(MUST NOT). 실제 project revision을 사용하고 반복 run은 SDK가 구분해야 한다(SHALL).

초기 실험은 사례를 직렬 처리하고 Runtime retry·byte/token cap·단계/전체 예산·원문·checkpoint·기계적 JSON 취합을 유지해야 한다(SHALL). 관측·SDK 실패를 이유로 모델을 다시 실행해서는 안 된다(MUST NOT). 기존 `HMDA_AGENTIC_REVIEW_*`·`HMDA_LANGFUSE_*` 설정을 읽지 않고 native `LANGFUSE_*`와 표준 `OPENAI_BASE_URL`·`OPENAI_API_KEY`, Prompt config 및 기존 artifact root를 사용해야 한다(SHALL).

#### Scenario: Setup is separate from repeated experiments

- **WHEN** 이미 등록한 Dataset으로 experiment를 실행할 때
- **THEN** native task와 결과 표시를 사용하고 원격 bootstrap·점수 조회를 수행하지 않아야 한다(SHALL).

#### Scenario: Dataset expectations remain reviewer data

- **WHEN** 합성 item을 검토할 때
- **THEN** oracle·controls·expected output을 provider에 주입하지 않고 원래 사례만 검토해야 한다(SHALL).

### Requirement: Verified model IO observation linkage

Native generation은 실제 단계 모델 호출 구간을 감싸고 적용한 native prompt 객체·model과 실제 메시지 input, 로컬 저장 이후의 반환 output, native usage를 연결해야 한다(SHALL). 실행 뒤 빈 generation을 재생성하거나 원격 전송만을 위해 모든 manifest·checkpoint·원문을 다시 읽는 계층을 두어서는 안 된다(MUST NOT). 단계 provenance에는 적용한 prompt name/version과 메시지 digest를 보존해야 한다(SHALL).

허용된 합성 실행에서는 system·canonical input·완료 history를 포함한 실제 compiled prompt를 input으로 전송할 수 있다. Credential·provider 예외·개인 경로·전체 설정을 자동 캡처하거나 본문을 metadata에 복제해서는 안 된다(MUST NOT). 본문 없는 실패에서 답변을 만들거나 실패 stage를 성공으로 표시해서는 안 된다(MUST NOT).

#### Scenario: Generations observe real call duration and prompt

- **WHEN** 단계 provider 호출이 실행될 때
- **THEN** 실제 호출 구간에 native prompt·model을 연결하고 반환 usage와 저장된 원문을 해당 generation에서 확인할 수 있어야 한다(SHALL).

#### Scenario: Missing responses stay failures

- **WHEN** Runtime이 본문 없이 실패할 때
- **THEN** 성공 output을 합성하지 않고 실제 failure 상태와 보존된 경로만 남겨야 한다(SHALL).

### Requirement: Independent external evaluation IO

원격 Prompt를 시작 시 읽지 못하면 모델 호출 전에 `unavailable / prompt_unavailable`을 반환하고 로컬 seed로 fallback해서는 안 된다(MUST NOT). 이미 모델이 실행된 뒤의 관측 전송 실패는 core status·원문·manifest와 분리하고 모델 재호출이나 보존된 결과 변경을 일으켜서는 안 된다(MUST NOT).

SDK의 native timeout·retry·cache·flush lifecycle을 사용하고 별도 child process·watchdog·외부 I/O 강제 deadline을 제공하지 않아야 한다(SHALL). HTTP timeout·core 실행 예산이 SDK flush와 프로세스 종료의 wall-clock 상한을 보장한다고 표현해서는 안 된다(MUST NOT).

SDK 제출·flush 반환, 원격 조회·UI 확인, 사람이 작성한 평가는 구분해야 한다(SHALL). 실제 원격 객체나 사람 평가를 확인하지 않았다면 그 성공을 주장해서는 안 된다(MUST NOT).

#### Scenario: Prompt startup failure prevents model execution

- **WHEN** 필요한 remote prompt를 읽지 못할 때
- **THEN** 정제된 prompt failure로 종료하고 모델이나 로컬 fallback을 실행하지 않아야 한다(SHALL).

#### Scenario: Observation failure preserves local results

- **WHEN** 모델 실행 후 native 관측이 실패할 때
- **THEN** 로컬 결과를 보존하고 모델을 재호출하지 않아야 한다(SHALL).
