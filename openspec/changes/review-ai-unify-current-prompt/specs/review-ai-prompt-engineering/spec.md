---
type: openspec-spec-driven-tdd-spec
category: spec
title: review-ai-prompt-engineering
description: 현재 한국어 단계 실행만 제공하고 과거 버전·출력·기록 호환 지원을 제거합니다.
---

## RENAMED Requirements

- FROM: `### Requirement: Inspectable versioned prompt resources`
- TO: `### Requirement: Inspectable modular prompt resources`

## MODIFIED Requirements

### Requirement: Staged text prompt modules

시스템은 근거 검토·초안 비판·종합의 세 단계 질문과 일반 텍스트 출력을 한국어 Markdown 모듈로 관리해야 한다(SHALL). 각 조합은 적용 가능한 공통 작업·언어·수치·근거·검토 가치·자문 지침과 현재 단계의 신뢰된 system 질문을 결합해야 한다(SHALL). Canonical input과 이전 assistant 답변은 별도 자료로 전달하고 모델에 JSON 객체·키·타입 생성을 요구해서는 안 된다(MUST NOT).

#### Scenario: Each stage requests prose for one review concern

- **WHEN** 현재 단계의 프롬프트를 조립할 때
- **THEN** 해당 질문·한국어 일반 텍스트 출력·자문 경계를 포함하고 전체 JSON 생성 지시를 포함해서는 안 된다(MUST NOT).

#### Scenario: Later stages retain prior text as context

- **WHEN** 초안 비판이나 종합 단계를 조립할 때
- **THEN** 같은 canonical input과 이전 원문을 대화 자료로 유지하고 현재 질문은 신뢰된 모듈에서 선택해야 한다(SHALL).

### Requirement: Inspectable modular prompt resources

한국어 지시문은 작업·출력·검토 지침·자문 정책·단계 질문의 UTF-8 Markdown 모듈로 관리하고 최초 등록 자료로 배포해야 한다(SHALL). 각 모듈을 Langfuse text prompt로 등록하고 세 chat prompt는 native composition reference·history message placeholder를 사용해야 한다(SHALL). Langfuse Prompt Management가 실행 정본이며 일반 실행은 repository 모듈을 직접 조립하거나 별도 include·cache·version registry를 제공해서는 안 된다(MUST NOT).

사례 데이터가 prompt 이름·조합·system 지시문을 선택해서는 안 된다(MUST NOT). 실제 native compile 결과 전체에 byte cap과 digest를 적용해야 한다(SHALL). 과거 v1/v2/v3 완성 snapshot·renderer·호환 리소스를 package에 남겨서는 안 된다(MUST NOT).

#### Scenario: Native composition shares common instructions

- **WHEN** 최초 등록한 세 단계 chat prompt를 조회할 때
- **THEN** 같은 의미의 공통 지시문은 native text prompt reference로 공유하고 단계 질문과 history 위치를 확인할 수 있어야 한다(SHALL).

#### Scenario: Packaged modules are setup material

- **WHEN** 배포 wheel에서 명시적으로 setup을 실행할 때
- **THEN** 한국어 Markdown 자료를 읽어 native Prompt를 등록할 수 있어야 하고 일반 검토가 이를 fallback으로 사용해서는 안 된다(MUST NOT).

### Requirement: Prompt lifecycle and active default

일반 Python API·직접 service·실험 CLI는 같은 native prompt 경로를 사용해야 한다(SHALL). 기본 label은 `production`이며 workflow 시작 시 세 chat prompt를 모두 읽고 같은 workflow에서는 해당 객체와 실제 name/version을 고정해야 한다(SHALL). 실행 도중 label 이동으로 후속 단계를 재조회해서는 안 된다(MUST NOT). 원격 prompt를 읽지 못하면 모델 호출 전에 `prompt_unavailable`로 끝내고 로컬 fallback을 제공해서는 안 된다(MUST NOT).

SDK의 native version·label은 변경 식별에 사용한다. 과거 v1/v2/v3 실행 모드·compatibility alias·옛 환경 설정 해석을 제공해서는 안 된다(MUST NOT). Prompt 변경이 모델 품질 개선을 입증하지 않으며 과거 실행의 revision·digest·결과를 다시 써서는 안 된다(MUST NOT).

#### Scenario: One workflow pins the loaded prompts

- **WHEN** 실행 도중 서버의 production label이 이동할 때
- **THEN** 이미 시작한 workflow는 처음 읽은 세 prompt 객체를 계속 사용하고 실제 version을 기록해야 한다(SHALL).

#### Scenario: Unavailable prompts have no local fallback

- **WHEN** 시작에 필요한 prompt 조회가 실패할 때
- **THEN** typed failure를 반환하고 모델 호출이나 repository 프롬프트 실행을 시작해서는 안 된다(MUST NOT).

### Requirement: Korean instructions and narrative output

현재 모든 역할·작업·제약·설명 지시문의 자연어는 한국어여야 하며 단계별 답변도 한국어로 요청해야 한다(SHALL). 자체 생성한 `review_context.gaps[].description`과 빈 근거 요약의 대체 문구도 한국어로 작성해야 한다(SHALL). 입력 식별자·근거 ID·원본 수치·선언된 API 및 schema 식별자는 원표기를 보존하고 원본 자료를 번역 목적으로 재작성해서는 안 된다(MUST NOT).

#### Scenario: Every stage requests Korean prose

- **WHEN** 세 단계 중 하나를 조립할 때
- **THEN** system은 한국어 검토와 원표기의 입력 식별자·수치 보존을 명시해야 한다(SHALL).

#### Scenario: Korean output preserves the collection contract

- **WHEN** 모델이 한국어 일반 텍스트를 반환할 때
- **THEN** 코드는 원문을 유지하고 input identity·facts와 고정 단계 ID로 collection을 만들어야 한다(SHALL).

#### Scenario: Generated context gaps use Korean descriptions

- **WHEN** 누락·제외된 근거 또는 미확정 원인의 gap을 생성할 때
- **THEN** 설명은 한국어로 작성하고 kind·topic과 원본 Evidence는 보존해야 한다(SHALL).

#### Scenario: Missing evidence summary uses a Korean fallback

- **WHEN** Evidence summary가 비어 있거나 공백뿐일 때
- **THEN** bounded context에 한국어 대체 문구를 사용하고 원본 Evidence를 바꾸지 않아야 한다(SHALL).

### Requirement: Revision-bound prompt change evidence

각 실행은 실제 native prompt name/version과 전체 compiled message digest·project revision을 함께 보존해야 한다(SHALL). 같은 로드된 prompt 객체·canonical input·완료 원문으로 compile한 메시지는 결정적이어야 한다(SHALL). Repository revision만으로 실행 프롬프트가 같다고 가정해서는 안 된다(MUST NOT).

과거 실행의 자료를 현재 prompt version으로 소급 변경하거나 과거 local renderer를 호환 실행 경로로 제공해서는 안 된다(MUST NOT).

#### Scenario: Native versions identify prompt changes

- **WHEN** 같은 코드 revision에서 remote prompt를 수정해 실행할 때
- **THEN** 실제 prompt version과 compiled digest로 변경을 식별하고 과거 기록을 보존해야 한다(SHALL).

#### Scenario: Fixed native compilation is repeatable

- **WHEN** 같은 native prompt 객체·canonical input·history를 반복 compile할 때
- **THEN** 같은 메시지 bytes와 digest를 생성해야 한다(SHALL).

### Requirement: Language compliance remains an evaluation concern

한국어 지시문의 존재와 실제 출력의 언어·정확성·검토 가치를 구분해야 한다(SHALL). 모듈 변경·offline 통과·completed만으로 실제 모델의 한국어 준수나 품질 개선을 주장해서는 안 된다(MUST NOT). 보존된 원문으로 언어 준수를 사람이 확인할 수 있어야 하며 언어 판별만으로 새 deterministic rejection을 추가해서는 안 된다(MUST NOT).

#### Scenario: A language mismatch remains inspectable

- **WHEN** 수집 가능한 모델 답변이 일부 영어로 작성될 때
- **THEN** 수집 status를 언어만으로 바꾸지 않고 보존된 원문에서 지시 위반을 평가할 수 있어야 한다(SHALL).

## ADDED Requirements

### Requirement: Evidence-grounded prose instructions

지시문은 rate·percentage-point 차이·delta threshold와 baseline-zero에서 정의되지 않는 상대 변화율을 구별하도록 안내해야 한다(SHALL). 코드는 structured facts를 입력에서 그대로 가져오며 모델은 설명에서만 읽기 쉬운 단위를 사용하도록 안내해야 한다(SHALL).

제공된 Evidence와 실제 draft를 대조하고 미확인 원인·검증 결과를 확정하거나 존재하지 않는 draft action을 비판하지 않도록 안내해야 한다(SHALL). 검토 가치는 단순 재서술을 넘어 확인 우선순위와 결과에 따라 달라지는 사람의 다음 판단에 연결해야 한다(SHALL). 이런 지시문을 임의 자연어를 거부하는 deterministic classifier로 바꾸어서는 안 된다(MUST NOT).

#### Scenario: Numeric units remain distinct

- **WHEN** baseline 0.01·current 0.21·delta 0.20인 사례를 검토할 때
- **THEN** 1%에서 21%로 20 percentage points 증가한 것과 baseline 대비 2000% 증가를 구별하도록 안내해야 한다(SHALL).
- **AND** baseline이 0이면 상대 변화율을 계산할 수 없음을 안내해야 한다(SHALL).

#### Scenario: Evidence gaps lead to bounded next decisions

- **WHEN** 원인이나 검증 결과가 제공되지 않았을 때
- **THEN** gap과 불확실성을 밝히고 실제 근거·draft에 연결된 다음 확인을 제안하도록 안내해야 한다(SHALL).
