---
type: openspec-spec-driven-tdd-spec
category: spec
title: reliability-agentic-review
description: 합성 검토를 native Langfuse 실험·사람 평가로 연결하고 무결성과 외부 실패 경계를 정의합니다.
---

## MODIFIED Requirements

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

## ADDED Requirements

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
