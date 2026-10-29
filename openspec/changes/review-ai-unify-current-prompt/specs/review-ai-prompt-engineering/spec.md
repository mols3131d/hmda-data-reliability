---
type: openspec-spec-driven-tdd-spec
category: spec
title: review-ai-prompt-engineering
description: 현재 프롬프트와 명시적 legacy 선택의 계약을 정의합니다.
---

## MODIFIED Requirements

### Requirement: Inspectable versioned prompt resources

현재 프롬프트는 작업·언어·출력·검토 지침·자문 정책·단계 질문의 책임별 UTF-8 Markdown 모듈로 관리하고 고정 순서로 조립해야 한다(SHALL). 같은 의미와 전제의 현재 모듈은 공유하고 사례 데이터가 모듈 선택이나 system 본문을 바꾸어서는 안 된다(MUST NOT). 조립기는 정해진 구분자 외의 공백·개행을 임의로 변경해서는 안 된다(MUST NOT).

Retired v1/v2/v3는 legacy 디렉터리의 고정된 완성 본문 snapshot으로 보존해야 한다(SHALL). 과거 snapshot의 내용은 현재 공유 모듈의 수정과 독립적이어야 하며 기존 메시지·digest를 유지해야 한다(SHALL). 이 역사 보존용 복제는 현재 모듈의 공통 규칙 중복 관리로 취급하지 않는다. 일반 실행을 import하거나 현재 프롬프트를 조립할 때 legacy version 맵이나 snapshot을 로드해서는 안 된다(MUST NOT).

현재 조합과 명시적으로 선택한 legacy 조합 모두 전체 메시지의 byte cap·digest를 적용하고 checkout 밖의 배포 wheel에서 같은 메시지를 제공해야 한다(SHALL). 모델 JSON 생성 지시는 legacy 조합에만 적용해야 한다(SHALL).

#### Scenario: Selected version composes its Markdown parts

- **WHEN** legacy version을 명시적으로 선택할 때
- **THEN** 선택한 version의 완성 Markdown snapshot을 그대로 읽고 canonical input과 분리해야 한다(SHALL).

#### Scenario: Shared rules use one source

- **WHEN** 현재 세 단계가 같은 언어·자문 정책을 사용할 때
- **THEN** 같은 책임의 현재 모듈을 고정 조합으로 공유해야 한다(SHALL).

#### Scenario: Prompt structure remains readable without changing the response contract

- **WHEN** 현재 모듈 또는 명시적으로 선택한 legacy snapshot을 읽을 때
- **THEN** 현재의 한국어 일반 텍스트 지시와 legacy JSON 계약을 구분할 수 있어야 한다(SHALL).

#### Scenario: Module reuse respects its task and output assumptions

- **WHEN** 현재 모듈을 다른 단계에 재사용할 때
- **THEN** 작업·입력·출력 전제의 호환성을 확인하고 legacy snapshot에는 영향을 주지 않아야 한다(SHALL).

#### Scenario: Case data cannot select instruction modules

- **WHEN** canonical input에 지시문이나 Markdown 경로가 들어 있을 때
- **THEN** 그 데이터가 현재 조합이나 legacy version을 선택해서는 안 된다(MUST NOT).

#### Scenario: Packaged parts are available outside the checkout

- **WHEN** 배포 wheel을 checkout 밖에서 사용할 때
- **THEN** 현재 모듈과 명시적 legacy snapshot을 읽고 source와 같은 메시지를 생성해야 한다(SHALL).

#### Scenario: Structural extraction preserves the rendered prompt

- **WHEN** 기존 완성 본문을 legacy snapshot으로 격리할 때
- **THEN** 공백·개행과 기존 메시지·digest를 보존해야 한다(SHALL).

### Requirement: Prompt lifecycle and active default

일반 Python API·직접 service 진입점과 기본 live CLI는 동일한 현재 한국어 단계별 텍스트 프롬프트를 사용해야 한다(SHALL). 일반 실행에 v1/v2/v3 기본 선택이나 자동 fallback을 두어서는 안 된다(MUST NOT). 현재 workflow identity와 prompt digest는 출처용으로 유지하며 retired prompt version 선택과 구분해야 한다(SHALL).

기존 버전과 JSON 검토는 명시적 legacy namespace 및 version 선택으로만 실행해야 한다(SHALL). CLI에서는 MODE=legacy와 LEGACY_PROMPT_VERSION을 함께 명시해야 하며(SHALL), 이전 MODE=structured는 호출 전에 이전 방법을 안내하고 거부해야 한다(SHALL). 일반 환경에 남은 PROMPT_VERSION은 현재 프롬프트를 바꾸어서는 안 되며(MUST NOT), 안내에 그 값이나 자격 증명을 포함해서는 안 된다(MUST NOT).

이 전환은 사용자가 요청한 실행 경로의 변경이며 모델 품질 개선이나 legacy v3의 품질 채택 근거로 해석해서는 안 된다(MUST NOT). 과거 identity·revision·digest와 결과를 현재 실행에 맞춰 재작성해서는 안 된다(MUST NOT).

#### Scenario: General entrypoints use current prompts

- **WHEN** 일반 API 또는 live CLI를 version 없이 실행할 때
- **THEN** 같은 현재 세 단계의 한국어 텍스트를 요청하고 결과 JSON을 코드로 취합해야 한다(SHALL).

#### Scenario: Stale version variables cannot choose a retired prompt

- **WHEN** 일반 환경에 기존 PROMPT_VERSION 값이 남아 있을 때
- **THEN** 현재 실행을 유지하고 안내에는 키 이름만 표시해야 한다(SHALL).

#### Scenario: Legacy selection requires an explicit version

- **WHEN** MODE=legacy이지만 LEGACY_PROMPT_VERSION이 없거나 유효하지 않을 때
- **THEN** 기존 version 기본값이나 옛 환경 변수로 fallback하지 않고 provider 호출 전에 거부해야 한다(SHALL).

#### Scenario: Removed structured mode cannot silently run legacy

- **WHEN** MODE=structured가 남아 있을 때
- **THEN** 현재 또는 legacy provider를 호출하지 않고 명시적 이전 방법을 안내해야 한다(SHALL).
