# reliability-agentic-review Specification

## Purpose

`null_spike`의 불변 사건 snapshot과 결정론적 사실을 유지하면서 제한된 read-only 도구 조사·한국어 보고·caller가 별도로 승인받은 복구 요청의 위임 조합을 제공한다. Native Prompt·모델·도구·원문·실패를 같은 invocation 근거로 연결하고 API와 합성 Dataset 실험이 공통 실행을 사용한다. `completed`는 구조와 로컬 저장의 완료이지 사실성·검토 가치·승인이나 mutation 권한이 아니다. 과거 실행의 identity·파일·Git 기록은 보존한다.

## Requirements

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

동일 snapshot은 같은 canonical JSON bytes를 생성해야 한다(SHALL). Evidence·draft·이전 모델 답변·도구 결과는 untrusted data이며 system 지시·도구 허용 범위·권한을 변경해서는 안 된다(MUST NOT). 도구가 추가한 관측은 원입력의 과거 사실과 구별해야 한다(SHALL). 프롬프트의 언어·native lifecycle은 [review-ai-prompt-engineering](../review-ai-prompt-engineering/spec.md)을 따라야 한다(SHALL).

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

`completed`는 실제 모델의 최종 보고가 유효하고 필수 로컬 근거 게시가 조사 기한 안에 완료된 상태를 의미하며 사실성·검토 가치·사람 승인·실행 허가를 뜻해서는 안 된다(MUST NOT). Invalid JSON·잘못된 결과 구조·provider·시간·저장 실패를 성공형 요약으로 대체해서는 안 된다(MUST NOT). 실패는 이전 partial 기록을 유지하되 완성 보고를 합성해서는 안 된다(MUST NOT).

유효한 모델 보고가 없는 조사는 종료 사유를 반환하고 확보한 사실을 로컬 조사 기록에 보존해야 한다(SHALL).

#### Scenario: Completed result requires retained provenance

- **WHEN** 유효한 최종 모델 보고와 필수 원문·manifest가 기한 안에 저장될 때
- **THEN** `completed`와 회수 가능한 경로를 반환해야 한다(SHALL).

#### Scenario: Failure never exposes a complete output

- **WHEN** 파싱·구조·provider·예산·저장이 실패할 때
- **THEN** 실패 상태·code와 보존한 partial 근거를 반환하고 성공을 합성해서는 안 된다(MUST NOT).

### Requirement: Provider-compatible bounded invocation

Ollama와 OpenAI 등 호환 연결은 credentials-free URL·SecretStr credential·model·bounded 설정을 사용해야 한다(SHALL). 도메인별 provider business rule을 두거나 URL의 userinfo·query·fragment를 허용해서는 안 된다(MUST NOT).

OpenAI 호환 호출은 non-streaming·temperature 0·bounded output tokens와 허용된 tool definition만 사용해야 한다(SHALL). Assistant tool call과 matching tool result의 ID·순서·원문을 유지하고 tools와 충돌하는 JSON response forcing을 해서는 안 된다(MUST NOT). SDK hidden retry는 끄고 configured transport retry만 허용해야 한다(SHALL). Invalid output을 고치기 위한 생성 재시도를 자동 수행해서는 안 된다(MUST NOT).

호환 호출은 설정된 retry와 타임아웃·연결 오류·5xx 분류를 유지해야 한다(SHALL).

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

### Requirement: Native synthetic dataset experiments

최초 등록은 `python -m hmda_reliability.reliability_ai.evaluation.setup`, 반복 실행은 `python -m hmda_reliability.reliability_ai.evaluation.experiment`로 분리해야 한다(SHALL). 명시적 setup만 seed Prompt·합성 Dataset을 등록하고 반복 실험은 기존 Dataset을 조회해야 한다(SHALL). Experiment가 Dataset item·Prompt version·Score Config·Annotation Queue를 자동 생성·수정해서는 안 된다(MUST NOT).

SDK의 native Dataset task·직렬 실행·결과 표시를 사용하고 Dataset 이름·run 이름·timezone-aware version·model·prompt label·실제 revision과 적용 예산을 식별할 수 있어야 한다(SHALL). Oracle·controls·expected output·검토자 질문을 모델 입력에 넣어서는 안 된다(MUST NOT). 결과에는 전체 InvestigationResult를 보존하고 Dataset item ID의 multiset과 반환 결과의 완전성을 검증해야 한다(SHALL). 누락·중복·실패 항목이 있으면 CLI 성공을 반환해서는 안 된다(MUST NOT).

표준 `LANGFUSE_*`와 기존 artifact root를 사용해야 한다(SHALL). 호환 연결에서는 제공된 `OPENAI_BASE_URL`과 `OPENAI_API_KEY`를 사용하고 명시적 로컬 Ollama 선택에는 기존 로컬 기본값을 지원해야 한다(SHALL). 옛 전용 환경 설정을 재해석해서는 안 된다(MUST NOT). Native 관측 실패를 이유로 모델을 재실행해서는 안 된다(MUST NOT).

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

시스템은 각 provider·tool 호출 직전에 단조 시계 기준의 동일한 종료 시각과 호출 한도를 적용해야 한다(SHALL). Provider 호출 전에는 앱이 실제 전달할 전체 구성 이력과 도구 정의의 바이트 수 및 남은 모델 턴을 확인해야 한다(SHALL). 한 응답의 여러 도구 요청은 순서대로 개별 실행 직전에 검증하며 남은 요청이 한도를 넘기면 그때까지의 관찰값과 `budget_exhausted`를 반환해야 한다(SHALL). 같은 요청의 반복 순환은 기록하고 중단해야 한다(SHALL). 정상 종료를 위해 불필요한 도구 호출 횟수를 강제해서는 안 된다(MUST NOT).

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

#### Scenario: Exact tool quota permits a final report

- **WHEN** 턴의 도구 요청을 모두 처리한 시점에 도구 호출 잔여 횟수는 0이고 시간과 모델 턴 한도는 남았을 때
- **THEN** 추가 도구 없이 최종 보고를 요청할 수 있어야 한다(SHALL).

### Requirement: Investigation provenance and failure retention

각 invocation은 충돌하지 않는 identity, 실제 revision·input snapshot·선택 제공자와 설정·prompt name/version·실제 앱 입력 digest, turn별 응답·확인 가능한 usage·attempt·latency·도구 기록과 최종 상태를 연결해야 한다(SHALL). Record·manifest는 bounded private create-only atomic 파일로 보존하고 실패 시 기존 파일을 덮어쓰거나 삭제해서는 안 된다(MUST NOT). 깊은 JSON 또는 결과 직렬화 실패도 원문을 잃거나 성공으로 바뀌어서는 안 된다(MUST NOT).
응답 원문, 호출 자료와 도구 결과는 각각 다음 단계에서 사용하기 전에 저장해야 한다(SHALL). 최종 파일의 쓰기에 실패해도 부분 기록은 조사 ID로 회수할 수 있어야 한다(SHALL). 새 버전의 기록은 원문과 관찰값을 참조하여 최종 결과를 표현하며, 공개 `InvestigationResult`와 평가 결과에서는 기존 응답 본문과 도구 결과 필드를 복원해야 한다(SHALL). 과거 기록은 원래 형식과 실행 ID로 읽을 수 있어야 한다(SHALL).

#### Scenario: A later failure preserves earlier evidence

- **WHEN** 앞선 turn 저장 후 다음 호출·파싱·직렬화가 실패할 때
- **THEN** 회수 가능한 원문·도구 결과·digest·partial 경로와 명시적 실패를 유지해야 한다(SHALL).

#### Scenario: Persistence failure cannot become success

- **WHEN** 원문·도구 근거·최종 manifest의 필수 쓰기가 실패하거나 경로가 충돌할 때
- **THEN** 오류와 이미 생성한 경로를 반환하고 completed를 반환해서는 안 된다(MUST NOT).

#### Scenario: Referenced evidence restores public results

- **WHEN** 참조 방식으로 보존한 실행을 공개 API 결과나 Dataset 결과로 반환할 때
- **THEN** 보존한 turn·응답 본문·도구 결과와 근거 경로를 기존 결과 필드로 반환해야 한다(SHALL).

#### Scenario: Publish a readable JSON copy of the investigation result

- **WHEN** 사고 조사에서 최종 manifest를 게시할 때
- **THEN** 같은 조사 ID의 읽기용 JSON을 자동 생성해야 한다(SHALL). 파일에는 상태·실패 사유·사실·발견·가설·미확정 사항이 들어간다.
- **AND** 읽기용 사본 쓰기에 실패하면 조사 ID가 포함된 경고를 남기고, 이미 저장한 manifest에서 같은 조사 결과를 읽을 수 있어야 한다(SHALL).

### Requirement: Delegated task limits and recovery reporting

위임 실행은 Task의 허용 도구와 caller capability의 교집합, Task·caller 중 더 작은 tool/time 예산을 적용해야 한다(SHALL). Goal·task ID·requester/recipient와 명시된 snapshot references를 사건 입력과 함께 추적하고, snapshot reference가 입력과 충돌하면 실행 전에 거부해야 한다(SHALL). 허용 action이나 approval flag만으로 복구 권한을 만들 수 없어야 한다(SHALL).

ReportEnvelope은 인간 또는 supervisor 수신자, facts·hypotheses·제안·실행 영수증·근거·차단/미확정·다음 요청을 구별해야 한다(SHALL). `completed`, `awaiting_approval`, `blocked`, `failed`, `partial`을 실제 조사·승인·mutation·재검증 결과에 따라 반환해야 한다(SHALL). 영수증은 wrapper 보고이며 authoritative domain result·proposal/approval ID·mutation/reconciliation 정보를 보존해야 한다(SHALL). 도메인이 mutation 상태를 보고하지 않은 오류는 `not_reported`로 남기고 실행 전 상태였다고 추측해서는 안 된다(MUST NOT).
승인된 백필 요청에 백필 실행에 필요한 DB 연결이 제공되지 않으면 조사 전에 `blocked`를 반환해야 한다(SHALL). 복구의 실행 권한과 별도의 승인 요청 검증은 기존 복구 명세를 따라야 한다(SHALL).

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

#### Scenario: Missing approved backfill connection blocks before investigation

- **WHEN** `execute_delegated_task`에 승인된 백필 요청을 전달했지만 백필의 DB 연결을 제공하지 않았을 때
- **THEN** `blocked`와 연결 누락 사유를 반환해야 한다(SHALL).
- **AND** 모델·도구·복구를 호출해서는 안 된다(MUST NOT).

### Requirement: Deterministic investigation evaluation

Offline suite는 network 없이 입력·canonical facts·context·실제 도구 gateway·history·예산·파싱·직렬화·저장 실패·위임·승인 분리를 독립 oracle로 검증해야 한다(SHALL). 정상·거부·빈 응답·invalid/깊은 JSON·미완료·cycle·batch 초과·provider·부분 mutation·관측 실패를 포함하고 assertion을 약화해 실패를 숨겨서는 안 된다(MUST NOT).

실제 모델 품질은 명시적 native 합성 실험과 사람 rubric으로만 평가해야 한다(SHALL). Offline 통과·completed·SDK 반환을 한국어 준수·정확성·검토 가치·원격 적재·사람 승인으로 해석해서는 안 된다(MUST NOT). 비교는 실제 실행한 후보만 같은 Dataset version·사례·기준으로 수행하고 실패·미평가 항목을 보존해야 한다(SHALL).

#### Scenario: Offline tests preserve truth and authority

- **WHEN** fake provider와 실제 로컬 artifact로 정상·실패 경로를 반복 검증할 때
- **THEN** canonical facts·상태·근거를 확인하고 무승인 target mutation이 없어야 한다(SHALL).

#### Scenario: Live results retain actual execution conditions

- **WHEN** 선택한 제공자로 native experiment를 명시적으로 실행할 때
- **THEN** 실제 revision·Dataset version·prompt·선택한 제공자/model/context 설정·원문·도구·확인 가능한 usage·지연·실패와 별도의 사람 평가 상태를 기록해야 한다(SHALL).

### Requirement: Offline investigation replay

시스템은 새 재현 ID를 원본 조사 ID와 연결하고 기록된 Prompt 또는 실제 구성 입력, 응답·조회 결과, 상대 시각과 종료에 영향을 준 저장 결과를 공급하여 종료 판정을 재현해야 한다(SHALL). 누락되거나 손상된 필수 기록과 버전 차이는 재현 불가로 보고해야 한다(SHALL). 실제 Prompt·Dataset·제공자·도구·관측·복구 호출이나 원본 근거 변경을 발생시켜서는 안 된다(MUST NOT).

#### Scenario: A recorded failure remains a failure during replay

- **WHEN** 응답과 도구 결과가 이미 저장됐고 최종 저장에 실패한 조사를 재현할 때
- **THEN** 기록된 Prompt 또는 구성 입력과 저장 실패에 따라 같은 종료 상태와 사유를 새 재현 ID로 보고해야 한다(SHALL).
- **AND** 실제 외부 호출과 복구 실행의 횟수는 0이어야 한다(SHALL).

#### Scenario: Missing or incompatible replay evidence

- **WHEN** 필수 입력·관찰·시각·저장 결과가 누락 또는 손상됐거나 실행 버전이 호환되지 않을 때
- **THEN** 재현 불가 사유를 보고하고 원본 조사의 상태 또는 기록을 변경해서는 안 된다(MUST NOT).

### Requirement: Investigation provider selection

시스템은 조사 단위로 모델 제공자와 설정을 고정하고 선택한 제공자의 요청·응답·실패를 공통 계약으로 전달해야 한다(SHALL). 공개 API는 주입한 `provider=`, `RuntimeAISettings`에 명시한 호환 연결, 로컬 Codex 순으로 선택해야 한다(SHALL). 평가 CLI는 명시적 제공자, 명시적 `OPENAI_BASE_URL`, 로컬 Codex 순으로 선택해야 한다(SHALL). `OPENAI_API_KEY`만으로 호환 연결을 선택해서는 안 되며 서로 충돌하는 새 명시적 설정은 호출 전에 거절해야 한다(SHALL). 선택된 제공자에서 모델 기본값과 인증 정보를 가져오고 해당 제공자의 장애를 자동 fallback으로 감춰서는 안 된다(MUST NOT).

모델 전송 재시도는 선택한 어댑터에서 허용하고 기록한 시도에 한정해야 한다(SHALL).

#### Scenario: Explicit provider configuration takes precedence

- **WHEN** API에서 `provider=`와 호환 설정을 함께 전달하거나 CLI가 명시적 제공자와 `OPENAI_BASE_URL`을 함께 받았을 때
- **THEN** 주입한 어댑터 또는 명시한 제공자를 선택하고 선택과 호환되지 않는 새 명시적 설정을 호출 전에 거절해야 한다(SHALL).

#### Scenario: Unconfigured local execution selects Codex

- **WHEN** API에 주입과 호환 설정이 모두 없거나 CLI에 제공자와 `OPENAI_BASE_URL`이 모두 없을 때
- **THEN** 로컬 Codex를 선택해야 한다(SHALL).
- **AND** `OPENAI_API_KEY`만 설정되어 있어도 같은 선택을 사용해야 한다(SHALL).

### Requirement: Bounded Codex subscription invocation

Codex는 관리형 ChatGPT 구독 OAuth 로그인과 허용된 도구 범위에 맞는 실행 격리를 확인한 경우에만 조사 자료를 전달해야 한다(SHALL). 모델이 지정한 경로·명령·권한 승격과 상속된 도구가 조사 범위 밖에서 동작해서는 안 된다(MUST NOT). 시도별 실제 앱 입력과 호스트 조회 결과를 해당 제안과 순서대로 연결하고, 조사·논리 턴·시도·제공자 요청·스레드·턴의 식별자를 대조해 유효한 종료 응답만 받아야 한다(SHALL). 앱 입력에 적용한 한도와 digest를 제공자가 내부에서 추가한 문맥의 증거로 사용해서는 안 된다(MUST NOT).

Codex의 이전 요청이 수락되지 않았음을 확인한 경우에만 같은 조사 예산 안에서 재시도할 수 있어야 한다(SHALL). 이전 시도가 수락됐거나 수락 여부가 불명확하면 같은 논리 턴을 재시도해서는 안 된다(MUST NOT). 기한이 소진되면 가능한 중단 요청의 결과와 실제 턴 종료를 구분해 기록해야 한다(SHALL).

#### Scenario: Codex requires verified account and isolation

- **WHEN** Codex의 ChatGPT 구독 로그인이나 읽기 전용 조사에 맞는 실행 격리를 확인할 수 없을 때
- **THEN** 원인을 반환하고 모델·도구 실행, 조사 근거 전송과 대체 제공자 호출을 시작해서는 안 된다(MUST NOT).

#### Scenario: Ambiguous Codex acceptance prevents retry

- **WHEN** Codex 요청을 보낸 뒤 수락을 증명하는 기록 없이 연결이 끊겼을 때
- **THEN** 수락 여부가 불명확한 실패를 기록하고 모델 재호출과 후속 도구 실행 없이 종료해야 한다(SHALL).

#### Scenario: Codex responses match the active attempt

- **WHEN** 다른 요청·스레드·턴의 종료 이벤트 또는 같은 종료 이벤트를 반복해서 받았을 때
- **THEN** 현재 시도의 유효한 종료 이벤트와 응답만 처리하고 도구를 중복 실행해서는 안 된다(MUST NOT).

### Requirement: Synthetic experiment authorization and observation linkage

실험 시작 전에 Dataset의 모든 항목이 합성 입력으로 명시적으로 허용됐는지 검사해야 한다(SHALL). 어떤 제공자를 선택했는지 기록하고 각 Dataset 항목을 해당 조사·턴·관측 식별자와 연결해야 한다(SHALL).

#### Scenario: Dataset preflight rejects unapproved items

- **WHEN** 조회한 Dataset에 `metadata.synthetic`이 `true`가 아닌 항목이 하나라도 있을 때
- **THEN** 실험 시작 전에 합성 입력 허용 오류를 보고하고 CLI 종료 코드 `2`를 반환해야 한다(SHALL).
- **AND** 어떤 항목의 조사나 모델 호출도 시작해서는 안 된다(MUST NOT).

#### Scenario: Observations are matched to the actual experiment item

- **WHEN** 완료한 Dataset 항목의 원격 관측을 확인할 때
- **THEN** 같은 리비전·Dataset 항목·조사·턴의 관측을 다시 조회한 경우에만 확인된 관측으로 기록해야 한다(SHALL).
