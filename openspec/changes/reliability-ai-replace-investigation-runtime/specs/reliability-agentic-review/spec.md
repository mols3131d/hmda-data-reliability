---
type: openspec-spec-driven-tdd-spec
category: spec
title: reliability-agentic-review
description: 사고 조사 제공자 선택, 제한된 실행과 오프라인 재현의 관찰 가능한 계약을 변경합니다.
---

## ADDED Requirements

### Requirement: Offline investigation replay

시스템은 새 재현 ID를 원본 조사 ID와 연결하고 기록된 Prompt 또는 실제 구성 입력, 응답·조회 결과, 상대 시각과 종료에 영향을 준 저장 결과를 공급하여 종료 판정을 재현해야 한다(SHALL). 누락되거나 손상된 필수 기록과 버전 차이는 재현 불가로 보고해야 한다(SHALL). 실제 Prompt·Dataset·제공자·도구·관측·복구 호출이나 원본 근거 변경을 발생시켜서는 안 된다(MUST NOT).

#### Scenario: A recorded failure remains a failure during replay

- **WHEN** 응답과 도구 결과가 이미 저장됐고 최종 저장에 실패한 조사를 재현할 때
- **THEN** 기록된 Prompt 또는 구성 입력과 저장 실패에 따라 같은 종료 상태와 사유를 새 재현 ID로 보고해야 한다(SHALL).
- **AND** 실제 외부 호출과 복구 실행의 횟수는 0이어야 한다(SHALL).

#### Scenario: Missing or incompatible replay evidence

- **WHEN** 필수 입력·관찰·시각·저장 결과가 누락 또는 손상됐거나 실행 버전이 호환되지 않을 때
- **THEN** 재현 불가 사유를 보고하고 원본 조사의 상태 또는 기록을 변경해서는 안 된다(MUST NOT).

## MODIFIED Requirements

### Requirement: Typed review result boundary

조사는 `InvestigationResult`의 `completed`, `budget_exhausted`, `tool_cycle_detected`, `error`와 원인을 구별하는 failure code를 반환해야 한다(SHALL). 결과는 input에서 고정한 사건 identity·결정론적 facts와 모델의 findings·hypotheses·uncertainties, 실제 도구 기록·turn·원문 경로·manifest를 구분해야 한다(SHALL). 모델의 다른 수치를 canonical facts로 채택해서는 안 된다(MUST NOT).

`completed`는 실제 모델의 최종 보고가 유효하고 필수 로컬 근거 게시가 조사 기한 안에 완료된 상태를 의미하며 사실성·검토 가치·사람 승인·실행 허가를 뜻해서는 안 된다(MUST NOT). Invalid JSON·잘못된 결과 구조·provider·시간·저장 실패를 성공형 요약으로 대체해서는 안 된다(MUST NOT). 실패는 이전 partial 기록을 유지하되 완성 보고를 합성해서는 안 된다(MUST NOT).

#### Scenario: Completed result requires retained provenance

- **WHEN** 유효한 최종 모델 보고와 필수 원문·manifest가 기한 안에 저장될 때
- **THEN** `completed`와 회수 가능한 경로를 반환해야 한다(SHALL).

#### Scenario: Failure never exposes a complete output

- **WHEN** 파싱·구조·provider·예산·저장이 실패할 때
- **THEN** 실패 상태·code와 보존한 partial 근거를 반환하고 성공을 합성해서는 안 된다(MUST NOT).

#### Scenario: Rule-only facts cannot complete an incident investigation

- **WHEN** 모든 결정론적 facts를 확보했지만 실제 모델의 유효한 최종 보고가 없을 때
- **THEN** facts와 종료 사유를 보고하고 `completed`를 반환해서는 안 된다(MUST NOT).

### Requirement: Provider-compatible bounded invocation

시스템은 조사 단위로 모델 제공자와 설정을 고정하고 선택한 제공자의 요청·응답·실패를 공통 계약으로 전달해야 한다(SHALL). 공개 API는 주입한 `provider=`, `RuntimeAISettings`에 명시한 호환 연결, 로컬 Codex 순으로 선택해야 한다(SHALL). 평가 CLI는 명시적 제공자, 명시적 `OPENAI_BASE_URL`, 로컬 Codex 순으로 선택해야 한다(SHALL). `OPENAI_API_KEY`만으로 호환 연결을 선택해서는 안 되며 서로 충돌하는 새 명시적 설정은 호출 전에 거절해야 한다(SHALL). 선택된 제공자에서 모델 기본값과 인증 정보를 가져오고 해당 제공자의 장애를 자동 fallback으로 감춰서는 안 된다(MUST NOT).

Ollama와 OpenAI 등 호환 연결은 credentials-free URL·SecretStr credential·model·bounded 설정을 사용해야 한다(SHALL). 도메인별 provider business rule을 두거나 URL의 userinfo·query·fragment를 허용해서는 안 된다(MUST NOT).

OpenAI 호환 호출은 non-streaming·temperature 0·bounded output tokens와 허용된 tool definition만 사용해야 한다(SHALL). Assistant tool call과 matching tool result의 ID·순서·원문을 유지하고 tools와 충돌하는 JSON response forcing을 해서는 안 된다(MUST NOT). SDK hidden retry는 끄고 configured transport retry만 허용해야 한다(SHALL). Invalid output을 고치기 위한 생성 재시도를 자동 수행해서는 안 된다(MUST NOT).
Codex는 관리형 ChatGPT 구독 OAuth 로그인과 허용된 도구 범위에 맞는 실행 격리를 확인한 경우에만 조사 자료를 전달해야 한다(SHALL). 모델이 지정한 경로·명령·권한 승격과 상속된 도구가 조사 범위 밖에서 동작해서는 안 된다(MUST NOT). 시도별 실제 앱 입력과 호스트 조회 결과를 해당 제안과 순서대로 연결하고, 조사·논리 턴·시도·제공자 요청·스레드·턴의 식별자를 대조해 유효한 종료 응답만 받아야 한다(SHALL). 앱 입력에 적용한 한도와 digest를 제공자가 내부에서 추가한 문맥의 증거로 사용해서는 안 된다(MUST NOT).

호환 호출은 설정된 retry와 타임아웃·연결 오류·5xx 분류를 유지해야 한다(SHALL). Codex의 이전 요청이 수락되지 않았음을 확인한 경우에만 같은 조사 예산 안에서 재시도할 수 있어야 한다(SHALL). 이전 시도가 수락됐거나 수락 여부가 불명확하면 같은 논리 턴을 재시도해서는 안 된다(MUST NOT). 기한이 소진되면 가능한 중단 요청의 결과와 실제 턴 종료를 구분해 기록해야 한다(SHALL). 모델 전송 재시도는 선택한 어댑터에서 허용하고 기록한 시도에 한정해야 한다(SHALL).

#### Scenario: Local and cloud-compatible configuration

- **WHEN** 같은 사례에 다른 OpenAI-compatible endpoint를 설정할 때
- **THEN** 같은 domain 실행·Runtime adapter를 사용해야 한다(SHALL).

#### Scenario: Provider timeout or unavailability

- **WHEN** timeout·connection failure·bounded retry 소진이 발생할 때
- **THEN** 구분 가능한 failure code와 실제 attempt·latency를 보존해야 한다(SHALL).

#### Scenario: Text invocation keeps history without JSON forcing

- **WHEN** 모델 호출과 도구 결과가 누적될 때
- **THEN** matching history를 보존하고 `response_format`을 강제해서는 안 된다(MUST NOT).

#### Scenario: Explicit provider configuration takes precedence

- **WHEN** API에서 `provider=`와 호환 설정을 함께 전달하거나 CLI가 명시적 제공자와 `OPENAI_BASE_URL`을 함께 받았을 때
- **THEN** 주입한 어댑터 또는 명시한 제공자를 선택하고 선택과 호환되지 않는 새 명시적 설정을 호출 전에 거절해야 한다(SHALL).

#### Scenario: Unconfigured local execution selects Codex

- **WHEN** API에 주입과 호환 설정이 모두 없거나 CLI에 제공자와 `OPENAI_BASE_URL`이 모두 없을 때
- **THEN** 로컬 Codex를 선택해야 한다(SHALL).
- **AND** `OPENAI_API_KEY`만 설정되어 있어도 같은 선택을 사용해야 한다(SHALL).

#### Scenario: Codex requires verified account and isolation

- **WHEN** Codex의 ChatGPT 구독 로그인이나 읽기 전용 조사에 맞는 실행 격리를 확인할 수 없을 때
- **THEN** 원인을 반환하고 모델·도구 실행, 조사 근거 전송과 대체 제공자 호출을 시작해서는 안 된다(MUST NOT).

#### Scenario: Ambiguous Codex acceptance prevents retry

- **WHEN** Codex 요청을 보낸 뒤 수락을 증명하는 기록 없이 연결이 끊겼을 때
- **THEN** 수락 여부가 불명확한 실패를 기록하고 모델 재호출과 후속 도구 실행 없이 종료해야 한다(SHALL).

#### Scenario: Codex responses match the active attempt

- **WHEN** 다른 요청·스레드·턴의 종료 이벤트 또는 같은 종료 이벤트를 반복해서 받았을 때
- **THEN** 현재 시도의 유효한 종료 이벤트와 응답만 처리하고 도구를 중복 실행해서는 안 된다(MUST NOT).

### Requirement: Native synthetic dataset experiments

최초 등록은 `python -m hmda_reliability.reliability_ai.evaluation.setup`, 반복 실행은 `python -m hmda_reliability.reliability_ai.evaluation.experiment`로 분리해야 한다(SHALL). 명시적 setup만 seed Prompt·합성 Dataset을 등록하고 반복 실험은 기존 Dataset을 조회해야 한다(SHALL). Experiment가 Dataset item·Prompt version·Score Config·Annotation Queue를 자동 생성·수정해서는 안 된다(MUST NOT).

SDK의 native Dataset task·직렬 실행·결과 표시를 사용하고 Dataset 이름·run 이름·timezone-aware version·model·prompt label·실제 revision과 적용 예산을 식별할 수 있어야 한다(SHALL). Oracle·controls·expected output·검토자 질문을 모델 입력에 넣어서는 안 된다(MUST NOT). 결과에는 전체 InvestigationResult를 보존하고 Dataset item ID의 multiset과 반환 결과의 완전성을 검증해야 한다(SHALL). 누락·중복·실패 항목이 있으면 CLI 성공을 반환해서는 안 된다(MUST NOT).

실험 시작 전에 Dataset의 모든 항목이 합성 입력으로 명시적으로 허용됐는지 검사해야 한다(SHALL). 표준 `LANGFUSE_*`와 기존 artifact root를 사용해야 한다(SHALL). 호환 연결에서는 제공된 `OPENAI_BASE_URL`과 `OPENAI_API_KEY`를 사용하고 명시적 로컬 Ollama 선택에는 기존 로컬 기본값을 지원해야 한다(SHALL). 어떤 제공자를 선택했는지 기록하고 각 Dataset 항목을 해당 조사·턴·관측 식별자와 연결해야 한다(SHALL). 옛 전용 환경 설정을 재해석해서는 안 된다(MUST NOT). Native 관측 실패를 이유로 모델을 재실행해서는 안 된다(MUST NOT).

#### Scenario: Setup is separate from repeated experiments

- **WHEN** 등록된 Dataset으로 반복 실험할 때
- **THEN** native task만 실행하고 원격 bootstrap·점수 조회를 수행해서는 안 된다(MUST NOT).

#### Scenario: Dataset expectations remain reviewer data

- **WHEN** 합성 item을 조사할 때
- **THEN** item의 허용 input만 모델 자료로 사용해야 한다(SHALL).

#### Scenario: Dataset preflight rejects unapproved items

- **WHEN** 조회한 Dataset에 `metadata.synthetic`이 `true`가 아닌 항목이 하나라도 있을 때
- **THEN** 실험 시작 전에 합성 입력 허용 오류를 보고하고 CLI 종료 코드 `2`를 반환해야 한다(SHALL).
- **AND** 어떤 항목의 조사나 모델 호출도 시작해서는 안 된다(MUST NOT).

#### Scenario: Omitted task exceptions cannot produce success

- **WHEN** SDK가 task exception 항목을 결과에서 제외하거나 항목을 중복 반환할 때
- **THEN** CLI는 불완전성을 보고하고 nonzero로 끝나야 한다(SHALL).

#### Scenario: Observations are matched to the actual experiment item

- **WHEN** 완료한 Dataset 항목의 원격 관측을 확인할 때
- **THEN** 같은 리비전·Dataset 항목·조사·턴의 관측을 다시 조회한 경우에만 확인된 관측으로 기록해야 한다(SHALL).

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

- **WHEN** 원문·결과·manifest 쓰기가 실패하거나 경로가 충돌할 때
- **THEN** 오류와 이미 생성한 경로를 반환하고 completed를 반환해서는 안 된다(MUST NOT).

#### Scenario: Referenced evidence restores public results

- **WHEN** 참조 방식으로 보존한 실행을 공개 API 결과나 Dataset 결과로 반환할 때
- **THEN** 보존한 turn·응답 본문·도구 결과와 근거 경로를 기존 결과 필드로 반환해야 한다(SHALL).

#### Scenario: Publish a readable JSON copy of the investigation result

- **WHEN** 사고 조사에서 최종 manifest를 게시할 때
- **THEN** 같은 조사 ID의 읽기용 JSON을 자동 생성해야 한다(SHALL). 파일에는 상태·실패 사유·사실·발견·가설·미확정 사항이 들어간다.
- **AND** 읽기용 사본 쓰기에 실패하면 조사 ID로 경고하고, 이미 저장한 manifest에서 조사 결과를 읽을 수 있어야 한다(SHALL).

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
