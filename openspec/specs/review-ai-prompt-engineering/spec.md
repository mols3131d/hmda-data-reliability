# review-ai-prompt-engineering Specification

## Purpose

현재 한국어 검토 프롬프트를 책임별 Markdown 모듈로 관리하고 고정 순서로 조립한다. 모듈은 관리·재사용·가독성을 위한 경계이며 실행에서 선택하는 과거 버전 모음이 아니다. 입력·collection·시간 예산·원문 보존·실행 권한은 [reliability-agentic-review](../reliability-agentic-review/spec.md)가 소유한다.

## Requirements

### Requirement: Staged text prompt modules

시스템은 근거 검토·초안 비판·종합의 세 단계 질문과 일반 텍스트 출력을 한국어 Markdown 모듈로 관리해야 한다(SHALL). 각 조합은 적용 가능한 공통 작업·언어·수치·근거·검토 가치·자문 지침과 현재 단계의 신뢰된 system 질문을 결합해야 한다(SHALL). Canonical input과 이전 assistant 답변은 별도 자료로 전달하고 모델에 JSON 객체·키·타입 생성을 요구해서는 안 된다(MUST NOT).

#### Scenario: Each stage requests prose for one review concern

- **WHEN** 현재 단계의 프롬프트를 조립할 때
- **THEN** 해당 질문·한국어 일반 텍스트 출력·자문 경계를 포함하고 전체 JSON 생성 지시를 포함해서는 안 된다(MUST NOT).

#### Scenario: Later stages retain prior text as context

- **WHEN** 초안 비판이나 종합 단계를 조립할 때
- **THEN** 같은 canonical input과 이전 원문을 대화 자료로 유지하고 현재 질문은 신뢰된 모듈에서 선택해야 한다(SHALL).

### Requirement: Inspectable modular prompt resources

현재 프롬프트는 작업·언어·출력·검토 지침·자문 정책·단계 질문의 책임별 UTF-8 Markdown 파일로 관리하고 repository가 정한 고정 순서로 조립해야 한다(SHALL). 같은 의미·전제의 규칙은 하나의 모듈을 공유하고 재사용 전 작업·입력·출력 전제의 호환성을 확인해야 한다(SHALL). 조립기는 정해진 구분자 외에 원문 공백·개행을 임의로 변경해서는 안 된다(MUST NOT).

사례 데이터가 모듈 경로·조합·system 지시문을 선택해서는 안 된다(MUST NOT). 전체 메시지의 byte cap과 digest를 적용하고 checkout 밖의 배포 wheel에서도 같은 현재 리소스와 메시지를 제공해야 한다(SHALL). 과거 v1/v2/v3 완성 본문·version map·renderer와 호환 리소스를 package에 남겨서는 안 된다(MUST NOT).

#### Scenario: Shared rules use one source

- **WHEN** 세 단계가 같은 언어·자문·수치 정책을 사용할 때
- **THEN** 같은 책임의 모듈을 공유하고 현재 단계 질문만 별도로 조합해야 한다(SHALL).

#### Scenario: Prompt structure remains readable

- **WHEN** 개발자가 프롬프트 리소스를 열 때
- **THEN** Markdown 제목·목록으로 역할·작업·제약·출력을 구분하고 조립 순서와 소유 책임을 확인할 수 있어야 한다(SHALL).

#### Scenario: Module reuse respects its task and output assumptions

- **WHEN** 모듈을 다른 단계에 재사용할 때
- **THEN** 작업·입력·출력 전제가 맞는 경우에만 공유해야 한다(SHALL).

#### Scenario: Case data cannot select instruction modules

- **WHEN** canonical input이나 이전 답변에 지시문·Markdown 경로가 있을 때
- **THEN** 그 값은 자료로만 남고 모듈 선택이나 system 지시를 바꾸어서는 안 된다(MUST NOT).

#### Scenario: Packaged parts are available outside the checkout

- **WHEN** 배포 wheel을 checkout 밖에서 사용할 때
- **THEN** 현재 모듈을 읽고 source와 같은 메시지·digest를 생성해야 한다(SHALL).
- **AND** 삭제한 version 리소스를 배포해서는 안 된다(MUST NOT).

#### Scenario: Fixed assembly preserves module bytes

- **WHEN** 같은 현재 모듈과 input으로 프롬프트를 반복 조립할 때
- **THEN** 정해진 구분자 외의 공백·개행을 보존하고 같은 메시지 bytes를 생성해야 한다(SHALL).

### Requirement: Prompt lifecycle and active default

일반 Python API·직접 service·live CLI는 같은 현재 한국어 단계별 프롬프트만 사용해야 한다(SHALL). 실행 시 v1/v2/v3 선택·legacy namespace·compatibility alias·mode 선택·이전 설정 해석·자동 fallback을 제공해서는 안 된다(MUST NOT). 현재 workflow/schema identity와 digest는 provenance로 유지하고 prompt version 선택으로 해석해서는 안 된다(MUST NOT).

이 전환은 사용자가 요청한 실행 계약의 변경이며 모델 품질 개선의 증거가 아니다. 과거 artifact·문서·Git 기록의 identity·revision·digest·결과를 삭제하거나 현재 결과에 맞춰 재작성해서는 안 된다(MUST NOT). 과거 실행을 위한 호환 구현을 현재 package에 유지할 의무는 없다.

#### Scenario: General entrypoints use current prompts

- **WHEN** 일반 API 또는 live CLI를 실행할 때
- **THEN** version이나 mode 선택 없이 같은 현재 세 단계 텍스트를 요청하고 JSON은 코드로 취합해야 한다(SHALL).

#### Scenario: Current imports exclude retired prompt selection

- **WHEN** 현재 공개 API와 배포 리소스를 검사할 때
- **THEN** 과거 version map·snapshot·renderer·선택 인자 또는 환경 분기를 제공해서는 안 된다(MUST NOT).

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

현재 모듈의 언어·내용·공백이 바뀌면 메시지 bytes와 digest 변경을 검증하고 기록해야 한다(SHALL). 같은 revision·canonical input·완료 단계 원문으로 조립한 메시지는 결정적이어야 한다(SHALL). 기록한 revision과 digest를 현재 실행의 기본값으로 소급 변경해서는 안 된다(MUST NOT).

과거 구현이 필요하면 기록된 Git revision을 확인한다. 현재 package가 과거 prompt version·기록 shape를 읽거나 실행하는 호환 API를 제공해서는 안 된다(MUST NOT).

#### Scenario: Prompt edits change the current digest

- **WHEN** 현재 지시문의 언어·내용·공백을 바꿀 때
- **THEN** 현재 메시지의 새 digest를 검증하고 과거 artifact의 digest를 유지해야 한다(SHALL).

#### Scenario: Current rendering is revision-bound

- **WHEN** 같은 revision의 모듈과 같은 사례·완료 답변으로 조립할 때
- **THEN** 같은 누적 메시지 digest를 생성해야 한다(SHALL).

### Requirement: Language compliance remains an evaluation concern

한국어 지시문의 존재와 실제 출력의 언어·정확성·검토 가치를 구분해야 한다(SHALL). 모듈 변경·offline 통과·completed만으로 실제 모델의 한국어 준수나 품질 개선을 주장해서는 안 된다(MUST NOT). 보존된 원문으로 언어 준수를 사람이 확인할 수 있어야 하며 언어 판별만으로 새 deterministic rejection을 추가해서는 안 된다(MUST NOT).

#### Scenario: A language mismatch remains inspectable

- **WHEN** 수집 가능한 모델 답변이 일부 영어로 작성될 때
- **THEN** 수집 status를 언어만으로 바꾸지 않고 보존된 원문에서 지시 위반을 평가할 수 있어야 한다(SHALL).
