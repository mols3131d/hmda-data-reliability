---
type: openspec-spec-driven-tdd-spec
category: spec
title: review-ai-prompt-engineering
description: 한국어 모듈을 native Prompt Management에 등록하고 실행별 prompt version을 고정합니다.
---

## MODIFIED Requirements

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

### Requirement: Revision-bound prompt change evidence

각 실행은 실제 native prompt name/version과 전체 compiled message digest·project revision을 함께 보존해야 한다(SHALL). 같은 로드된 prompt 객체·canonical input·완료 원문으로 compile한 메시지는 결정적이어야 한다(SHALL). Repository revision만으로 실행 프롬프트가 같다고 가정해서는 안 된다(MUST NOT).

과거 실행의 자료를 현재 prompt version으로 소급 변경하거나 과거 local renderer를 호환 실행 경로로 제공해서는 안 된다(MUST NOT).

#### Scenario: Native versions identify prompt changes

- **WHEN** 같은 코드 revision에서 remote prompt를 수정해 실행할 때
- **THEN** 실제 prompt version과 compiled digest로 변경을 식별하고 과거 기록을 보존해야 한다(SHALL).

#### Scenario: Fixed native compilation is repeatable

- **WHEN** 같은 native prompt 객체·canonical input·history를 반복 compile할 때
- **THEN** 같은 메시지 bytes와 digest를 생성해야 한다(SHALL).
