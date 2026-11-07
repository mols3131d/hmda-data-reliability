---
type: openspec-spec-driven-tdd-spec
category: spec
title: Bounded Reliability Investigation
description: "불변 사건 근거에 묶인 도구 조사, 위임 제한, 실패 보존과 native 평가로 고정 단계 검토를 전환한다."
---

## MODIFIED Requirements

### Requirement: Structured null-spike review input

시스템은 `null_spike` Incident, 실제 제공된 하나 이상의 Evidence, RemediationDraft와 caller가 제공한 non-empty `project_revision`을 깊게 복사한 call-scoped `AgenticReviewInput`으로 받아야 한다(SHALL). Caller가 원본 nested list 또는 mapping을 변경해도 실행 snapshot은 변하지 않아야 한다(SHALL). Input은 prompt 이름·버전 또는 실행 권한을 선택해서는 안 된다(MUST NOT).

Incident와 draft는 `null_spike`이며 incident ID·asset·partition이 같아야 한다(SHALL). Evidence ID는 unique하고 incident·draft의 reference set과 같아야 한다(SHALL). 정확히 하나의 canonical profile Evidence는 incident와 같은 asset·partition, `rule=null_spike`, non-empty column과 finite numeric baseline/current null rate·delta·threshold를 가져야 한다(SHALL). Canonical 수치·대상은 이 Evidence에서만 유도하고 payload는 canonical JSON으로 표현 가능해야 한다(SHALL). 명시적으로 참조된 contextual Evidence는 자체 asset·partition identity를 유지할 수 있어야 한다(SHALL).

#### Scenario: Valid evidence-bound input

- **WHEN** identity·complete Evidence set·unique canonical target·project revision이 유효할 때
- **THEN** 시스템은 불변 snapshot으로 bounded investigation을 실행할 수 있어야 한다(SHALL).

#### Scenario: Mismatched input is rejected before invocation

- **WHEN** incident/draft identity 또는 Evidence reference set이 다를 때
- **THEN** 입력 생성에서 거부하고 provider·tool·recovery를 호출해서는 안 된다(MUST NOT).
- **AND** Dataset task는 이 거부를 `input_rejected`로 보고해야 한다(SHALL).

#### Scenario: Referenced contextual evidence retains its own identity

- **WHEN** 다른 asset 또는 partition의 명시적 contextual Evidence가 함께 제공될 때
- **THEN** canonical target은 incident에 일치하고 contextual Evidence는 자체 identity를 유지해야 한다(SHALL).

#### Scenario: Invalid canonical target evidence

- **WHEN** canonical target이 없거나 둘 이상이거나 column·required numeric fact가 없거나 비유한 값일 때
- **THEN** 모델·도구 호출 전에 입력을 거부해야 한다(SHALL).

#### Scenario: Unsupported incident type

- **WHEN** `null_spike` 이외의 incident type이 제공될 때
- **THEN** provider·approval·recovery 없이 입력을 거부해야 한다(SHALL).

### Requirement: Canonical provider input projection

시스템은 bounded canonical projection을 초기 provider 자료와 invocation provenance의 같은 source로 사용해야 한다(SHALL). Incident의 ID·type·asset·partition·status·severity, 선택한 Evidence의 bounded summary·allowlisted facts·provenance, draft의 identity·근거 참조·영향 asset·권고·검증·승인 필요 여부와 결정론적 facts·bounded context만 전달해야 한다(SHALL). Credential·DB connection·원시 row·범용 파일 경로·allowlist 밖 payload를 자동 포함해서는 안 된다(MUST NOT).

동일 snapshot은 같은 canonical JSON bytes를 생성해야 한다(SHALL). Evidence·draft·이전 모델 답변·도구 결과는 untrusted data이며 system 지시·도구 허용 범위·권한을 변경해서는 안 된다(MUST NOT). 도구가 추가한 관측은 원입력의 과거 사실과 구별해야 한다(SHALL). 프롬프트의 언어·native lifecycle은 `review-ai-prompt-engineering`을 따라야 한다(SHALL).

#### Scenario: Canonical projection is deterministic and bounded

- **WHEN** 같은 snapshot을 반복 render할 때
- **THEN** 같은 bounded projection·digest를 만들고 allowlist 밖 필드를 전달해서는 안 된다(MUST NOT).

#### Scenario: Prompt-injection text remains data

- **WHEN** 사례 자료 또는 도구 결과에 명령문이 있을 때
- **THEN** 자료로만 serialize하고 system 지시·tool argument schema·권한으로 승격해서는 안 된다(MUST NOT).

#### Scenario: Oversized prompt is rejected before provider invocation

- **WHEN** 초기 또는 누적 메시지가 configured `max_prompt_bytes`를 넘을 때
- **THEN** 해당 provider 호출을 시작하지 않고 `error / prompt_too_large`와 이미 보존한 기록을 반환해야 한다(SHALL).

### Requirement: Bounded review context

시스템은 유효한 input에서 incident 판단에 관련된 Evidence를 stable priority와 identity로 선택·투영하는 immutable `BoundedReviewContext`를 제공해야 한다(SHALL). Canonical target을 포함해 identity·source·asset·partition·observation time·bounded facts·provenance를 보존하고 raw log·전체 row·database 또는 allowlist 밖 payload를 포함해서는 안 된다(MUST NOT). 제공되지 않은 source는 `missing_evidence`, 확정되지 않은 원인·맥락은 `unconfirmed_context`로 구분해야 한다(SHALL).

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
- **THEN** remote prompt·provider·tool 호출 전에 `error / context_too_large`와 로컬 실패 manifest를 반환하고 성공 보고를 합성해서는 안 된다(MUST NOT).

#### Scenario: Prompt-visible evidence references match the bounded allowlist

- **WHEN** bounded context에서 canonical input을 만들 때
- **THEN** draft의 인용 가능한 Evidence reference는 선택된 context Evidence ID로 제한해야 한다(SHALL).

### Requirement: Current review surface

공개 실행은 `hmda_reliability.reliability_ai`의 `investigate_incident`와 `execute_delegated_task`, 합성 실행은 `python -m hmda_reliability.reliability_ai.evaluation.experiment`로 제공해야 한다(SHALL). 일반 API와 CLI는 같은 bounded investigation과 native prompt 경로를 사용해야 한다(SHALL). 과거 `review_ai` package·고정 3단계 실행·옛 설정 alias·로컬 prompt fallback을 호환 경로로 남겨서는 안 된다(MUST NOT). 기존 `AgenticReviewInput`의 데이터 계약은 유지해야 한다(SHALL).

Langfuse SDK는 고정된 기본 의존성이며 import만으로 원격 연결이나 모델 호출을 시작해서는 안 된다(MUST NOT). 과거 파일·Inbox·Git 이력의 실행 identity와 bytes를 삭제하거나 새 형식으로 소급 재작성해서는 안 된다(MUST NOT).

#### Scenario: Current API has one execution contract

- **WHEN** 공개 조사 API 또는 실험 CLI를 호출할 때
- **THEN** 같은 native prompt·도구·예산 계약을 사용하고 과거 실행 모드를 선택할 수 없어야 한다(SHALL).

#### Scenario: Imports stay offline

- **WHEN** package를 import하거나 기본 offline suite를 실행할 때
- **THEN** 원격 Prompt·Dataset 또는 실제 모델을 요구해서는 안 된다(MUST NOT).

### Requirement: Typed review result boundary

조사는 `InvestigationResult`의 `completed`, `budget_exhausted`, `tool_cycle_detected`, `error`와 원인을 구별하는 failure code를 반환해야 한다(SHALL). 결과는 input에서 고정한 사건 identity·결정론적 facts와 모델의 findings·hypotheses·uncertainties, 실제 도구 기록·turn·원문 경로·manifest를 구분해야 한다(SHALL). 모델의 다른 수치를 canonical facts로 채택해서는 안 된다(MUST NOT).

`completed`는 유효한 최종 구조와 필수 로컬 근거의 저장 완료만 의미하며 사실성·검토 가치·사람 승인·실행 허가를 뜻해서는 안 된다(MUST NOT). Invalid JSON·잘못된 결과 구조·provider·시간·저장 실패를 성공형 요약으로 대체해서는 안 된다(MUST NOT). 실패는 이전 partial 기록을 유지하되 완성 보고를 합성해서는 안 된다(MUST NOT).

#### Scenario: Completed result requires retained provenance

- **WHEN** 유효한 최종 결과와 필수 원문·manifest가 저장될 때
- **THEN** `completed`와 회수 가능한 경로를 반환해야 한다(SHALL).

#### Scenario: Failure never exposes a complete output

- **WHEN** 파싱·구조·provider·예산·저장이 실패할 때
- **THEN** 실패 상태·code와 보존한 partial 근거를 반환하고 성공을 합성해서는 안 된다(MUST NOT).

### Requirement: Provider-compatible bounded invocation

시스템은 `runtime_ai`의 공통 OpenAI-compatible adapter로 Ollama 또는 OpenAI를 호출해야 한다(SHALL). Provider 차이는 credentials-free URL·SecretStr credential·model·bounded 설정으로 나타내고 도메인별 provider business rule을 두어서는 안 된다(MUST NOT). URL의 userinfo·query·fragment를 허용해서는 안 된다(MUST NOT).

호출은 non-streaming·temperature 0·bounded output tokens와 허용된 tool definition만 사용해야 한다(SHALL). Assistant tool call과 matching tool result의 ID·순서·원문을 유지하고 tools와 충돌하는 JSON response forcing을 해서는 안 된다(MUST NOT). SDK hidden retry는 끄고 configured transport retry만 허용해야 한다(SHALL). Invalid output을 고치기 위한 생성 재시도를 자동 수행해서는 안 된다(MUST NOT).

#### Scenario: Local and cloud-compatible configuration

- **WHEN** 같은 사례에 다른 OpenAI-compatible endpoint를 설정할 때
- **THEN** 같은 domain 실행·Runtime adapter를 사용해야 한다(SHALL).

#### Scenario: Provider timeout or unavailability

- **WHEN** timeout·connection failure·bounded retry 소진이 발생할 때
- **THEN** 구분 가능한 failure code와 실제 attempt·latency를 보존해야 한다(SHALL).

#### Scenario: Text invocation keeps history without JSON forcing

- **WHEN** 모델 호출과 도구 결과가 누적될 때
- **THEN** matching history를 보존하고 `response_format`을 강제해서는 안 된다(MUST NOT).

### Requirement: Local provider response retention

각 bounded provider 응답은 파싱·완료·예산 판정 전에 caller의 artifact root 아래 create-only private atomic 파일로 저장해야 한다(SHALL). 공백·개행·빈 본문을 포함한 UTF-8 bytes를 변경해서는 안 된다(MUST NOT). Tool-call-only 응답도 raw content와 구조화된 call 자료를 함께 추적해야 한다(SHALL). Invocation identity는 반복 실행 간 충돌하지 않아야 한다(SHALL).

원문 저장 실패는 명시적인 오류로 종료하고 이후 저장 실패에도 이미 회수 가능한 경로를 유지해야 한다(SHALL). 원문을 자동 콘솔 로그·metadata에 복제해서는 안 된다(MUST NOT). 허가된 합성 실험의 명시적 input/output 외에 credential·provider 예외·개인 절대 경로·전체 설정을 원격 전송해서는 안 된다(MUST NOT).

#### Scenario: Invalid stage text remains inspectable

- **WHEN** 빈 본문·invalid JSON·알려진 미완료 응답이 반환될 때
- **THEN** 거부 전에 raw bytes를 보존하고 해당 turn의 경로에서 읽을 수 있어야 한다(SHALL).

#### Scenario: Retained raw precedes remote output

- **WHEN** Runtime이 bounded 응답을 반환할 때
- **THEN** 원격 output 갱신 전에 로컬 원문을 저장하고 관측 장애가 이를 삭제하거나 재호출을 유발해서는 안 된다(MUST NOT).

#### Scenario: Unavailable calls have no response file

- **WHEN** preflight 거부 또는 본문 없는 전송 실패가 발생할 때
- **THEN** 존재하지 않는 원문 경로를 성공 근거로 반환해서는 안 된다(MUST NOT).

### Requirement: Native synthetic dataset experiments

최초 등록은 `python -m hmda_reliability.reliability_ai.evaluation.setup`, 반복 실행은 `python -m hmda_reliability.reliability_ai.evaluation.experiment`로 분리해야 한다(SHALL). 명시적 setup만 seed Prompt·합성 Dataset을 등록하고 반복 실험은 기존 Dataset을 조회해야 한다(SHALL). Experiment가 Dataset item·Prompt version·Score Config·Annotation Queue를 자동 생성·수정해서는 안 된다(MUST NOT).

SDK의 native Dataset task·직렬 실행·결과 표시를 사용하고 Dataset 이름·run 이름·timezone-aware version·model·prompt label·실제 revision과 적용 예산을 식별할 수 있어야 한다(SHALL). Oracle·controls·expected output·검토자 질문을 모델 입력에 넣어서는 안 된다(MUST NOT). 결과에는 전체 InvestigationResult를 보존하고 Dataset item ID의 multiset과 반환 결과의 완전성을 검증해야 한다(SHALL). 누락·중복·실패 항목이 있으면 CLI 성공을 반환해서는 안 된다(MUST NOT).

표준 `LANGFUSE_*`, `OPENAI_BASE_URL`, `OPENAI_API_KEY`와 기존 artifact root를 사용하고 옛 전용 환경 설정을 재해석해서는 안 된다(MUST NOT). Native 관측 실패를 이유로 모델을 재실행해서는 안 된다(MUST NOT).

#### Scenario: Setup is separate from repeated experiments

- **WHEN** 등록된 Dataset으로 반복 실험할 때
- **THEN** native task만 실행하고 원격 bootstrap·점수 조회를 수행해서는 안 된다(MUST NOT).

#### Scenario: Dataset expectations remain reviewer data

- **WHEN** 합성 item을 조사할 때
- **THEN** item의 허용 input만 모델 자료로 사용해야 한다(SHALL).

#### Scenario: Omitted task exceptions cannot produce success

- **WHEN** SDK가 task exception 항목을 결과에서 제외하거나 항목을 중복 반환할 때
- **THEN** CLI는 불완전성을 보고하고 nonzero로 끝나야 한다(SHALL).

### Requirement: Verified model IO observation linkage

Native generation은 실제 모델 호출 구간마다 적용 prompt 객체·실제 version·model·메시지·반환 usage와 로컬 보존 이후의 output을 연결해야 한다(SHALL). Tool observation은 같은 조사 아래 generation과 sibling으로 실제 실행 입력·결과·상태를 보존해야 한다(SHALL). 전체 loop를 하나의 generation으로 감추거나 실행 뒤 빈 observation을 재생성해서는 안 된다(MUST NOT).

허가된 합성 실행만 실제 compiled system·history·tool IO를 명시적 원격 input/output에 보낼 수 있어야 한다(SHALL). Credential·개인 경로·provider 예외를 자동 캡처하거나 본문을 metadata에 복제해서는 안 된다(MUST NOT).

#### Scenario: Generations observe real call duration and prompt

- **WHEN** provider 또는 도구를 실제 호출할 때
- **THEN** 각 실행 구간과 prompt·model·usage·matching tool result를 trace에서 구별할 수 있어야 한다(SHALL).

#### Scenario: Missing responses stay failures

- **WHEN** 응답 본문 없이 호출이 실패할 때
- **THEN** 성공 output을 합성하지 않고 실제 failure와 보존한 경로만 남겨야 한다(SHALL).

### Requirement: Independent external evaluation IO

시작에 필요한 remote prompt 조회 실패는 모델 호출 전 `error / prompt_unavailable`로 끝내고 local seed로 fallback해서는 안 된다(MUST NOT). 모델 실행 이후의 관측 전송 실패는 core status·원문·manifest와 분리하고 재호출·결과 변경을 유발해서는 안 된다(MUST NOT).

SDK native timeout·retry·cache·flush lifecycle을 사용하고 별도 subprocess watchdog 또는 외부 I/O 강제 deadline을 제공해서는 안 된다(MUST NOT). Core 예산이 SDK flush나 process 종료의 wall-clock 상한을 보장한다고 표현해서는 안 된다(MUST NOT). SDK 제출·flush 반환·실제 원격 조회·사람 평가는 구분해야 한다(SHALL).

#### Scenario: Prompt startup failure prevents model execution

- **WHEN** remote prompt를 읽지 못할 때
- **THEN** 모델·local fallback 없이 정제된 prompt failure로 종료해야 한다(SHALL).

#### Scenario: Observation failure preserves local results

- **WHEN** 모델 실행 후 관측 전송이 실패할 때
- **THEN** 로컬 결과를 보존하고 모델을 재호출해서는 안 된다(MUST NOT).

### Requirement: Advisory and read-only boundary

Investigation은 입력 truth·Evidence·draft·Approval·RecoveryProposal·대상 data/database를 변경해서는 안 된다(MUST NOT). Filesystem 쓰기는 로컬 실행 근거의 private create-only 저장과 기존 artifact reader lock primitive로 제한해야 한다(SHALL). 모델 답변·ActionProposal·Task의 approval flag·상위 모델 위임은 실행 권한을 만들 수 없어야 한다(SHALL).

위임 실행은 caller가 별도로 제공한 authoritative approved request를 기존 deterministic executor에 전달하는 경우에만 복구를 시도할 수 있어야 한다(SHALL). 이 경우에도 Task allowlist·동일 사건 binding·exact proposal Approval·stale 검사·재검증·멱등성·실패 reconciliation을 우회해서는 안 된다(MUST NOT). AI가 만든 제안을 authoritative request로 자동 변환해서는 안 된다(MUST NOT).

#### Scenario: Completed review does not mutate reliability state

- **WHEN** investigation이 completed될 때
- **THEN** 사건 truth·draft·대상 data와 recovery/approval 상태가 바뀌지 않아야 한다(SHALL).

#### Scenario: Action-like advisory remains non-executable

- **WHEN** 모델 답변 또는 ActionProposal이 실행을 권고할 때
- **THEN** 승인·RecoveryProposal·mutation request를 생성하거나 executor를 자동 호출해서는 안 된다(MUST NOT).

#### Scenario: Rejected or unavailable review remains contained

- **WHEN** 입력·provider·파싱·예산·저장이 실패할 때
- **THEN** 결정론적 결과와 target data를 보존하고 위임된 mutation을 시작해서는 안 된다(MUST NOT).

## ADDED Requirements

### Requirement: Bounded incident tools

시스템은 typed schema·추가 인자 금지·capability allowlist로 제한한 read-only 도구만 노출해야 한다(SHALL). 기본 registry는 사건 snapshot의 Evidence 조회와 canonical target profile 비교를 제공하고, dbt 영향 도구는 trusted caller가 artifact pair를 지정한 경우에만 제공해야 한다(SHALL). 미연결 도구를 광고하거나 빈 성공 관측을 합성해서는 안 된다(MUST NOT). Model이 SQL·파일 경로·다른 column 또는 incident asset으로 조회 범위를 확장해서는 안 된다(MUST NOT).

Profile 비교는 baseline/current/delta와 incident snapshot의 Evidence ID·source·관측 시각·가용 snapshot reference를 보존해야 한다(SHALL). Dbt 조회는 기존 deterministic 분석 결과와 동일 읽기 경계에서 식별한 artifact pair projection ID·관측 시각을 보존하고 current artifact 관측임을 표시해야 한다(SHALL). 이를 과거 사건 Evidence로 소급 대체해서는 안 된다(MUST NOT). 실제 분석에서 증명하지 않은 no-impact·미관측 성공을 단정해서는 안 된다(MUST NOT).

#### Scenario: Bound profile comparison returns observed facts

- **WHEN** baseline 0.01·current 0.21인 사건의 target column을 조회할 때
- **THEN** 0.01·0.21·delta 0.20과 snapshot 출처를 반환하고 다른 column은 거부해야 한다(SHALL).

#### Scenario: Configured dbt projection is distinct from incident evidence

- **WHEN** trusted artifact pair로 사건 asset의 영향을 조회할 때
- **THEN** 실제 downstream 결과와 current projection identity를 반환하고 모델이 path 또는 asset 범위를 바꾸지 못해야 한다(SHALL).

#### Scenario: Unavailable or invalid capabilities remain failures

- **WHEN** handler가 없거나 인자가 invalid하거나 artifact를 읽을 수 없을 때
- **THEN** 미연결 capability는 노출하지 않고 잘못된 호출은 오류로 기록해야 한다(SHALL).

### Requirement: Bounded investigation budgets

시스템은 각 provider·tool 호출 직전에 monotonic 잔여 시간과 누적 prompt bytes·tool call 상한을 확인해야 한다(SHALL). 한 응답에 여러 tool call이 있어도 개별 dispatch마다 한도를 지켜야 한다(SHALL). 같은 요청의 반복 순환은 기록하고 중단해야 한다(SHALL). 정상 종료를 위해 불필요한 도구 호출 횟수를 강제해서는 안 된다(MUST NOT).

유한한 양수의 connect/read timeout과 전체 실행 예산을 설정하고 생략한 세부 timeout만 공통 기본값을 사용해야 한다(SHALL). Retry·backoff·후속 호출은 잔여 예산 안에서만 시작하고 전송 대기를 잔여 시간 이하로 줄여야 한다(SHALL). 늦은 bounded 응답은 보존하되 완료로 채택해서는 안 된다(MUST NOT). 진행 중인 동기 provider·handler의 강제 취소나 원격 추론 중단을 보장해서는 안 된다(MUST NOT).

#### Scenario: Batched calls cannot exceed the budget

- **WHEN** 모델이 잔여 한도보다 많은 도구를 한 번에 요청할 때
- **THEN** 허용 수를 넘는 handler는 실행하지 않고 예산 소진을 반환해야 한다(SHALL).

#### Scenario: Late responses and expired workflows stop follow-up

- **WHEN** 응답 반환 또는 저장 사이에 전체 시간이 소진될 때
- **THEN** 회수한 원문은 유지하되 추가 provider·tool 호출과 completed 채택을 중단해야 한다(SHALL).

#### Scenario: Explicit phase settings and retries remain bounded

- **WHEN** 세부 timeout과 retry를 설정할 때
- **THEN** 세부 설정이 우선하며 잔여 예산 밖 시도·backoff 없이 timeout과 connection failure를 구분해야 한다(SHALL).

#### Scenario: Repeated exploration terminates

- **WHEN** 동일한 도구와 인자를 반복 요청할 때
- **THEN** 무한 탐색 없이 `tool_cycle_detected`와 이전 기록을 반환해야 한다(SHALL).

### Requirement: Investigation provenance and failure retention

각 invocation은 충돌하지 않는 identity, 실제 revision·input snapshot·설정·prompt name/version·메시지 digest, turn별 응답·usage·attempt·latency·도구 기록과 최종 상태를 연결해야 한다(SHALL). Record·manifest는 bounded private create-only atomic 파일로 보존하고 실패 시 기존 파일을 덮어쓰거나 삭제해서는 안 된다(MUST NOT). 깊은 JSON 또는 결과 직렬화 실패도 원문을 잃거나 성공으로 바뀌어서는 안 된다(MUST NOT).

#### Scenario: A later failure preserves earlier evidence

- **WHEN** 앞선 turn 저장 후 다음 호출·파싱·직렬화가 실패할 때
- **THEN** 회수 가능한 원문·도구 결과·digest·partial 경로와 명시적 실패를 유지해야 한다(SHALL).

#### Scenario: Persistence failure cannot become success

- **WHEN** 원문·결과·manifest 쓰기가 실패하거나 경로가 충돌할 때
- **THEN** 오류와 이미 생성한 경로를 반환하고 completed를 반환해서는 안 된다(MUST NOT).

### Requirement: Delegated task limits and recovery reporting

위임 실행은 Task의 허용 도구와 caller capability의 교집합, Task·caller 중 더 작은 tool/time 예산을 적용해야 한다(SHALL). Goal·task ID·requester/recipient와 명시된 snapshot references를 사건 입력과 함께 추적하고, snapshot reference가 입력과 충돌하면 실행 전에 거부해야 한다(SHALL). 허용 action이나 approval flag만으로 복구 권한을 만들 수 없어야 한다(SHALL).

ReportEnvelope은 인간 또는 supervisor 수신자, facts·hypotheses·제안·실행 영수증·근거·차단/미확정·다음 요청을 구별해야 한다(SHALL). `completed`, `awaiting_approval`, `blocked`, `failed`, `partial`을 실제 조사·승인·mutation·재검증 결과에 따라 반환해야 한다(SHALL). 영수증은 wrapper 보고이며 authoritative domain result·proposal/approval ID·mutation/reconciliation 정보를 보존해야 한다(SHALL). 도메인이 mutation 상태를 보고하지 않은 오류는 `not_reported`로 남기고 실행 전 상태였다고 추측해서는 안 된다(MUST NOT).

#### Scenario: Task limits cannot be widened by the model

- **WHEN** Task가 일부 도구만 허용하고 더 작은 예산을 줄 때
- **THEN** 실제 호출은 그 제한을 넘지 않고 모델·상위 위임이 이를 확대하지 못해야 한다(SHALL).

#### Scenario: Failed investigation prevents recovery

- **WHEN** 조사가 completed가 아닐 때
- **THEN** 보고는 실패 원인을 보존하고 approved request가 있어도 mutation을 시작해서는 안 된다(MUST NOT).

#### Scenario: Recovery request belongs to the investigated incident

- **WHEN** approved request의 incident·target·partition이 조사 입력과 다르거나 복구 요청 둘이 동시에 제공될 때
- **THEN** mutation 전에 거부하고 임의로 한 요청을 선택해서는 안 된다(MUST NOT).

#### Scenario: Partial and unknown execution states remain visible

- **WHEN** mutation 후 검증·freshness·reconciliation이 실패하거나 상태 불명 오류가 발생할 때
- **THEN** domain result와 실제 또는 미보고 상태를 보존하고 성공으로 축약해서는 안 된다(MUST NOT).

### Requirement: Deterministic investigation evaluation

Offline suite는 network 없이 입력·canonical facts·context·실제 도구 gateway·history·예산·파싱·직렬화·저장 실패·위임·승인 분리를 독립 oracle로 검증해야 한다(SHALL). 정상·거부·빈 응답·invalid/깊은 JSON·미완료·cycle·batch 초과·provider·부분 mutation·관측 실패를 포함하고 assertion을 약화해 실패를 숨겨서는 안 된다(MUST NOT).

실제 모델 품질은 명시적 native 합성 실험과 사람 rubric으로만 평가해야 한다(SHALL). Offline 통과·completed·SDK 반환을 한국어 준수·정확성·검토 가치·원격 적재·사람 승인으로 해석해서는 안 된다(MUST NOT). 비교는 실제 실행한 후보만 같은 Dataset version·사례·기준으로 수행하고 실패·미평가 항목을 보존해야 한다(SHALL).

#### Scenario: Offline tests preserve truth and authority

- **WHEN** fake provider와 실제 로컬 artifact로 정상·실패 경로를 반복 검증할 때
- **THEN** canonical facts·상태·근거를 확인하고 무승인 target mutation이 없어야 한다(SHALL).

#### Scenario: Live results retain actual execution conditions

- **WHEN** Ollama native experiment를 명시적으로 실행할 때
- **THEN** 실제 revision·Dataset version·prompt·model/context 설정·원문·도구·usage·지연·실패와 별도의 사람 평가 상태를 기록해야 한다(SHALL).

## REMOVED Requirements

### Requirement: Staged prose review collection

- **Reason:** 고정된 세 prose 응답은 동적 도구 조사의 실행·결과 계약이 아니다.
- **Migration:** `Bounded incident tools`, `Typed review result boundary`와 `Bounded investigation budgets`로 대체한다. 과거 collection 파일은 그대로 보존한다.

### Requirement: Staged execution time budgets

- **Reason:** 고정 stage 대신 provider·tool dispatch마다 예산을 적용한다.
- **Migration:** `Bounded investigation budgets`로 timeout·retry·late response와 동기 호출 한계를 유지한다.

### Requirement: Staged review provenance and failure retention

- **Reason:** 실행 단위가 stage에서 invocation·turn·tool로 바뀐다.
- **Migration:** `Investigation provenance and failure retention`과 `Local provider response retention`으로 identity·private atomic 저장·실패 경로를 유지한다.

### Requirement: Deterministic and adversarial evaluation

- **Reason:** 고정 prose collection과 no-JSON acceptance를 조사 결과 구조 검증으로 전환한다.
- **Migration:** `Deterministic investigation evaluation`로 independent oracle·실패·injection·live/human 구분을 유지한다.
