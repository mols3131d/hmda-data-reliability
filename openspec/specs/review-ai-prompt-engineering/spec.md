# review-ai-prompt-engineering Specification

## Purpose

Review AI의 현재 프롬프트를 책임별 모듈로 관리하고 retired version을 legacy로 보존하며, 한국어 설명과 변경 근거를 일관되게 유지한다. 입력·출력 shape, deterministic validation과 실행 권한은 [reliability-agentic-review](../reliability-agentic-review/spec.md)가 소유한다.

기존 v1/v2/v3 리소스와 JSON 응답 요구사항은 명시적 legacy structured 경로에만 적용한다. 단계별 텍스트 조합은 별도 `staged-v1` identity와 [Staged text prompt modules](#requirement-staged-text-prompt-modules) 계약을 따른다.

## Requirements

### Requirement: Staged text prompt modules

시스템은 단계별 검토 질문과 prose 출력 방식을 한국어 Markdown 모듈로 관리해야 한다(SHALL). 단계별 조합은 적용 가능한 기존 작업·검토 지침·자문 경계를 재사용하고, 현재 단계의 신뢰된 system 질문과 별도 canonical input 및 assistant 자료를 결합해야 한다(SHALL). 단계별 출력 지시는 JSON 객체·키·타입 생성을 모델에 요구해서는 안 된다(MUST NOT).

기존 버전별 JSON 지시문 요구사항은 structured 경로에 적용하고 staged text 조합은 별도 identity로 구분해야 한다(SHALL). 기존 v1/v2/v3 프롬프트와 과거 실행 기록을 staged 내용으로 바꿔서는 안 된다(MUST NOT).

#### Scenario: Each stage requests prose for one review concern

- **WHEN** 근거 검토, 초안 비판 또는 종합 단계의 프롬프트를 조립할 때
- **THEN** 현재 단계의 질문·한국어 일반 텍스트 출력·자문 경계가 system에 포함되고 기존 전체 JSON 출력 설명은 포함되지 않아야 한다(SHALL).

#### Scenario: Replaying old structured invocations

- **WHEN** 기존 identity·revision으로 과거 structured invocation을 재현할 때
- **THEN** staged 조합 선택이 기존 메시지·digest 또는 출력 계약을 바꾸어서는 안 된다(MUST NOT).

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

### Requirement: Korean instructions and narrative output

지원하는 모든 version의 역할·작업·제약·설명 지시문 및 내용 예시의 자연어는 한국어로 작성해야 한다(SHALL). 지시문은 `review_summary`, `findings[].description`, `uncertainties`의 각 항목과 `utility_contributions[].description`을 한국어로 작성하도록 모델에 요청해야 한다(SHALL). Review AI가 자체 생성하는 `review_context.gaps[].description`과 빈 근거 요약의 대체 문구도 한국어로 작성해야 한다(SHALL). JSON 필드명, 열거값, 입력 식별자·근거 ID와 구조화된 수치는 원표기를 유지하도록 요청해야 한다(SHALL). 원본 입력 데이터는 번역을 위해 재작성해서는 안 된다(MUST NOT).

#### Scenario: Every supported version requests Korean prose

- **WHEN** v1, v2 또는 v3 프롬프트를 선택할 때
- **THEN** system 지시문은 한국어이며 네 종류의 설명 필드에 한국어 작성을 명시해야 한다(SHALL).
- **AND** `null_spike`, `investigation_priority`, `high` 같은 계약 값은 번역하지 않도록 안내해야 한다(SHALL).

#### Scenario: Korean output preserves the structured contract

- **WHEN** 모델이 한국어 설명문과 원표기의 필드명·열거값·식별자·수치를 반환할 때
- **THEN** 기존 출력 schema와 structured-fact validator를 그대로 적용해야 한다(SHALL).

#### Scenario: Generated context gaps use Korean descriptions

- **WHEN** Review AI가 누락된 근거, 개수 제한으로 제외된 근거 또는 미확정 원인의 context gap을 생성할 때
- **THEN** 설명문은 한국어로 작성하고 gap의 kind, topic과 원본 Evidence 내용은 보존해야 한다(SHALL).

#### Scenario: Missing evidence summary uses a Korean fallback

- **WHEN** 제공된 Evidence의 summary가 비어 있거나 공백뿐일 때
- **THEN** bounded context에는 한국어 대체 문구를 사용하고 원본 Evidence는 변경하지 않아야 한다(SHALL).

### Requirement: Revision-bound prompt change evidence

지시문의 언어·내용·공백이 바뀌면 현재 메시지 바이트와 digest의 변경을 검증하고 기록해야 한다(SHALL). 현재 revision 안에서 동일 version과 canonical input의 렌더링은 결정적이어야 한다(SHALL). 과거 invocation의 identity, revision과 digest는 재작성해서는 안 되며(MUST NOT), 과거 프롬프트는 기록된 `project_revision`의 renderer와 리소스로 재생해야 한다(SHALL). version 이름이 같다는 이유만으로 서로 다른 revision의 digest가 같다고 간주해서는 안 된다(MUST NOT).

#### Scenario: Translation changes the current digest

- **WHEN** 지원하는 프롬프트의 영어 지시문을 한국어로 바꿀 때
- **THEN** 현재 한국어 메시지의 digest를 별도로 고정하고 과거 영어 invocation의 기록은 보존해야 한다(SHALL).

#### Scenario: Historical invocation replay uses its revision

- **WHEN** 저장된 version과 canonical input을 기록된 application revision의 renderer와 리소스에 제공할 때
- **THEN** 과거 invocation에 기록된 메시지 digest와 일치해야 한다(SHALL).

### Requirement: Language compliance remains an evaluation concern

한국어 작성 지시의 존재와 실제 모델의 언어·정확성·검토 가치를 구분해야 한다(SHALL). 프롬프트 번역이나 offline fixture 통과만으로 실제 출력의 한국어 준수 또는 품질 개선을 주장해서는 안 된다(MUST NOT). 실제 출력의 언어 준수는 보존된 모델 응답을 읽어 확인할 수 있어야 하며(SHALL), 언어 판별만으로 새 deterministic rejection을 추가해서는 안 된다(MUST NOT).

#### Scenario: A language mismatch remains inspectable

- **WHEN** 응답이 구조화된 계약은 만족하지만 일부 설명문을 영어로 작성할 때
- **THEN** 기존 validation 결과를 유지하고 보존된 응답에서 언어 미준수를 검토할 수 있어야 한다(SHALL).
