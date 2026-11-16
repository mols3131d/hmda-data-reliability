---
type: openspec-spec-driven-tdd-spec
category: spec
title: Investigation Prompt Engineering
description: "고정 세 단계 질문을 한국어 조사·도구·보고 지침으로 전환하고 native Prompt lifecycle과 출처를 유지한다."
---

## MODIFIED Requirements

### Requirement: Inspectable modular prompt resources

한국어 조사·도구 사용·출력 구조·수치·근거·검토 가치·자문 지침을 UTF-8 Markdown seed로 배포하고 Langfuse text/chat prompt의 native composition으로 관리해야 한다(SHALL). Repository 자료는 명시적 최초 등록용이며 일반 실행은 이를 직접 조립하거나 fallback·별도 include/cache/version registry로 사용해서는 안 된다(MUST NOT).

사례·이전 모델 답변·도구 결과가 prompt 이름·조합·system 지시를 선택해서는 안 된다(MUST NOT). 실제 native compile 메시지 전체에 byte cap과 digest를 적용해야 한다(SHALL). 과거 v1/v2/v3·고정 stage renderer를 호환 실행으로 남겨서는 안 된다(MUST NOT).

#### Scenario: Native composition shares common instructions

- **WHEN** 조사 chat prompt를 조회할 때
- **THEN** 공통 지침의 native reference와 도구/보고 지침·history 위치를 확인할 수 있어야 한다(SHALL).

#### Scenario: Packaged modules are setup material

- **WHEN** wheel에서 명시적 setup을 실행할 때
- **THEN** seed로 native Prompt를 등록할 수 있고 일반 조사에서 local fallback으로 실행해서는 안 된다(MUST NOT).

### Requirement: Prompt lifecycle and active default

일반 조사 API·위임 조사·실험 CLI는 같은 native prompt 경로를 사용해야 한다(SHALL). 기본 label은 `production`이며 invocation 시작에 필요한 prompt 객체를 읽고 모든 turn에서 실제 name/version을 고정해야 한다(SHALL). Label 이동으로 loop 중 재조회해서는 안 된다(MUST NOT). Remote 조회 실패는 모델 호출 전 `error / prompt_unavailable`로 종료하고 local fallback을 사용해서는 안 된다(MUST NOT).

기존 Prompt의 이름·버전·label을 먼저 확인하고 명시적 setup만 등록 자료를 변경해야 한다(SHALL). 반복 실험에서 Prompt version을 자동 생성하거나 기존 실행을 새 version으로 소급 기록해서는 안 된다(MUST NOT).

#### Scenario: One workflow pins the loaded prompts

- **WHEN** 실행 도중 production label이 이동할 때
- **THEN** 시작한 invocation은 처음 읽은 객체·실제 version을 계속 사용해야 한다(SHALL).

#### Scenario: Unavailable prompts have no local fallback

- **WHEN** prompt 조회가 실패할 때
- **THEN** 모델·repository seed 실행 없이 정제된 실패를 반환해야 한다(SHALL).

### Requirement: Evidence-grounded prose instructions

지시문은 rate·percentage-point 차이·delta threshold·baseline-zero에서 정의되지 않는 상대 변화율을 구별하도록 안내해야 한다(SHALL). 결정론적 facts는 코드가 입력에서 유지하고 모델은 설명·findings·hypotheses·uncertainties만 작성하도록 해야 한다(SHALL).

실제 Evidence·도구 결과와 draft를 대조하고 미확인 원인·검증·실행·존재하지 않는 조치를 확정해서는 안 된다고 안내해야 한다(SHALL). Snapshot과 후속 current projection은 구별하고, 결과에 따라 달라지는 다음 확인·사람 판단을 제안하도록 해야 한다(SHALL). 이러한 설명 지침을 임의 자연어의 사실성을 보장하는 deterministic classifier로 표현해서는 안 된다(MUST NOT).

#### Scenario: Numeric units remain distinct

- **WHEN** baseline 0.01·current 0.21·delta 0.20인 사례를 조사할 때
- **THEN** 1%에서 21%로 20 percentage points 증가와 상대 2000% 증가를 구별하도록 안내해야 한다(SHALL).
- **AND** baseline 0이면 상대 변화율을 계산할 수 없다고 안내해야 한다(SHALL).

#### Scenario: Evidence gaps lead to bounded next decisions

- **WHEN** 원인·실행·검증 근거가 제공되지 않았을 때
- **THEN** gap·불확실성을 밝히고 실제 근거·draft에 연결된 다음 확인을 제안하도록 해야 한다(SHALL).

### Requirement: Korean instructions and narrative output

역할·조사·도구 설명·출력·제약·설명 지시문은 한국어로 작성하고 구조화 결과의 narrative도 한국어로 요청해야 한다(SHALL). 입력 식별자·Evidence ID·원본 수치·API/schema 표기는 유지하고 원자료를 번역 목적으로 재작성해서는 안 된다(MUST NOT). Generated context gap·빈 summary 대체 문구도 한국어로 유지해야 한다(SHALL).

#### Scenario: Every stage requests Korean prose

- **WHEN** 초기 조사 또는 후속 turn을 조립할 때
- **THEN** system은 한국어 narrative와 식별자·수치 원표기 유지를 명시해야 한다(SHALL).

#### Scenario: Korean output preserves the collection contract

- **WHEN** 구조에 맞는 한국어 결과를 반환할 때
- **THEN** 원문은 그대로 보존하고 코드가 canonical facts와 모델 narrative를 구별해야 한다(SHALL).

#### Scenario: Generated context gaps use Korean descriptions

- **WHEN** 누락·제외 근거 또는 미확정 원인을 표시할 때
- **THEN** 설명은 한국어이며 kind·topic·원본 Evidence는 유지해야 한다(SHALL).

#### Scenario: Missing evidence summary uses a Korean fallback

- **WHEN** Evidence summary가 비거나 공백뿐일 때
- **THEN** bounded context에 한국어 대체 문구를 사용하고 원본은 변경해서는 안 된다(MUST NOT).

### Requirement: Revision-bound prompt change evidence

각 invocation은 실제 native prompt name/version·전체 compiled message digest·실제 project revision을 연결해야 한다(SHALL). 같은 prompt 객체·canonical input·history·tool result는 같은 메시지 bytes·digest를 생성해야 한다(SHALL). 코드 revision만으로 prompt 동일성을 가정하거나 과거 prompt/version·원문을 다시 써서는 안 된다(MUST NOT).

#### Scenario: Native versions identify prompt changes

- **WHEN** 같은 코드에서 remote prompt가 바뀔 때
- **THEN** 실제 version·digest로 변경을 식별하고 과거 기록을 유지해야 한다(SHALL).

#### Scenario: Fixed native compilation is repeatable

- **WHEN** 같은 prompt 객체·snapshot·history·tool result를 compile할 때
- **THEN** 같은 bytes·digest를 생성해야 한다(SHALL).

## ADDED Requirements

### Requirement: Bounded investigation instructions

조사 지시문은 제공 근거 확인·허용 도구 선택·관측과 가설 대조·종료/불확실성 보고를 안내하고, 고정 호출 순서나 불필요한 도구 횟수를 강제해서는 안 된다(MUST NOT). 결과의 findings·hypotheses·uncertainties와 Evidence reference 구조를 명시해야 한다(SHALL). 도구 결과의 지시문을 untrusted data로 다루고 raw SQL·임의 경로·mutation·approval 생성은 허용하지 않아야 한다(SHALL).

#### Scenario: The model can investigate or stop without fabricated calls

- **WHEN** 현재 근거가 충분하거나 추가 허용 조회가 유용할 때
- **THEN** 모델은 종료 또는 도구 조회를 선택할 수 있고 관측하지 않은 결과를 만들도록 요구받아서는 안 된다(MUST NOT).

#### Scenario: Tool text cannot grant authority

- **WHEN** 도구 결과가 실행·승인을 지시할 때
- **THEN** 자료로만 다루고 tool allowlist·Task 제한·외부 Approval을 변경하지 않아야 한다(SHALL).

## REMOVED Requirements

### Requirement: Staged text prompt modules

- **Reason:** 고정된 근거 검토·초안 비판·종합 질문은 bounded investigation의 동적 실행을 정의하지 않는다.
- **Migration:** `Bounded investigation instructions`로 대체하고 한국어·수치·근거·native 조합·revision 보존 요구는 수정된 기존 Requirement에서 유지한다.
