---
type: openspec-spec-driven-tdd-spec
category: spec
title: review-ai-prompt-engineering
description: Markdown 프롬프트 리소스와 JSON 응답 형식의 분리를 정의합니다.
---

## MODIFIED Requirements

### Requirement: Inspectable versioned prompt resources

시스템은 system 지시문을 역할·출력 언어·출력 계약·검토 기준 등 책임별 UTF-8 Markdown(`.md`) 조각으로 관리하고, 지원하는 각 version의 명시된 고정 순서로 조립해야 한다(SHALL). 공통 역할·언어·자문 경계와 같은 규칙은 버전별 본문에 복제하지 않고 같은 리소스를 공유해야 한다(SHALL). 작성자는 조합 정의에서 각 version이 사용하는 조각과 순서를 확인할 수 있어야 한다(SHALL).

각 조각은 제목과 목록으로 읽기 쉽게 구분하고 식별자는 인라인 코드로 표시해야 한다(SHALL). JSON 예시가 있는 버전은 언어가 표시된 코드 블록을 사용해야 한다(SHALL). 조립기는 정해진 구분자만 추가하고 조각의 Markdown 표기·공백·마지막 개행을 임의로 제거해서는 안 된다(MUST NOT). 선택한 조합은 작업 디렉터리와 관계없이 source checkout 및 배포 wheel에서 같은 메시지와 digest를 생성해야 한다(SHALL).

Markdown은 지시문의 작성 형식이며 모델의 응답 형식은 기존 JSON 객체 하나임을 명시해야 한다(SHALL). 응답에 마크다운 제목·목록·코드 펜스나 JSON 밖의 설명문을 덧붙이지 않도록 안내해야 한다(SHALL).

#### Scenario: Selected version composes its Markdown parts

- **WHEN** caller가 지원하는 version으로 프롬프트를 렌더링할 때
- **THEN** system 메시지는 해당 version의 명시된 Markdown 조각을 정해진 순서와 구분자로 조립한 내용과 같아야 한다(SHALL).
- **AND** 데이터 블록은 기존 canonical projection과 분리된 user 메시지로 유지되어야 한다(SHALL).

#### Scenario: Shared rules use one source

- **WHEN** 여러 version이 같은 역할·언어·자문 규칙을 사용할 때
- **THEN** 각 조합은 같은 공통 리소스를 한 번씩 참조해야 하며 version별로 독립된 복사본을 유지해서는 안 된다(MUST NOT).

#### Scenario: Prompt structure remains readable without changing the response contract

- **WHEN** 사람이 프롬프트 조각과 조합 정의를 읽거나 모델에 조립된 system 메시지를 전달할 때
- **THEN** 역할·언어·출력·권한 경계를 구분할 수 있어야 하며 모델에는 기존 JSON 출력 계약을 안내해야 한다(SHALL).
- **AND** 예시의 코드 펜스를 응답에 포함하도록 지시해서는 안 된다(MUST NOT).

#### Scenario: Packaged parts are available outside the checkout

- **WHEN** 빌드된 wheel을 checkout 밖에서 import하고 지원하는 version을 렌더링할 때
- **THEN** 조합에 필요한 모든 Markdown 조각이 포함되어 있어야 하고 동일 version과 canonical input의 메시지 및 digest는 source 렌더링과 같아야 한다(SHALL).

#### Scenario: Structural extraction preserves the rendered prompt

- **WHEN** 기존 전체 Markdown을 내용 변경 없이 조각으로 분리할 때
- **THEN** 조립한 system 메시지의 순서·공백·개행과 prompt digest는 분리 전과 같아야 한다(SHALL).
