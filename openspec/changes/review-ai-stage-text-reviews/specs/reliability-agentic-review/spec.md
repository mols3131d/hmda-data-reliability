---
type: openspec-spec-driven-tdd-spec
category: spec
title: reliability-agentic-review
description: 단계별 prose 수집과 코드 JSON 조립의 실행·보존 경계를 정의합니다.
---

## ADDED Requirements
<!-- provider wire 계약의 수정은 아래 MODIFIED Requirements에서 정의한다. -->

### Requirement: Staged prose review collection

시스템은 같은 immutable 사례의 근거 검토·초안 비판·종합을 고정 순서로 실행하고 모델에 JSON 생성 대신 한국어 텍스트를 요청해야 한다(SHALL). 호출마다 원래 canonical input과 완료된 이전 assistant 응답을 유지하고 전체 요청의 byte cap과 digest를 계산해야 한다(SHALL). 사례 데이터나 이전 모델 답변이 단계·system 지시를 선택해서는 안 된다(MUST NOT).

시스템은 원입력 식별자·대상·수치와 단계 ID·순서·반환된 텍스트를 코드로 결합해 별도 JSON collection을 생성해야 한다(SHALL). 답변의 공백·개행을 보존하며(SHALL), prose에서 기존 structured output의 분류·근거 참조·권고 enum을 추측해 생성해서는 안 된다(MUST NOT). 완료 상태는 수집·저장 완료로 한정하며 기존 accepted나 사람의 품질 평가를 의미해서는 안 된다(MUST NOT).

#### Scenario: Three text answers are mechanically collected

- **WHEN** 같은 사례의 세 단계가 비어 있지 않은 정상 텍스트를 반환할 때
- **THEN** 코드는 고정 순서의 원문과 원입력 facts를 JSON으로 저장하고 completed 및 저장 경로를 반환해야 한다(SHALL).
- **AND** provider 요청은 JSON response_format을 강제해서는 안 된다(MUST NOT).

#### Scenario: Later turns retain the same case and prior answers

- **WHEN** 두 번째 또는 세 번째 단계를 호출할 때
- **THEN** 원본 canonical input과 완료 단계 원문을 대화 자료로 유지하고, 누적 요청 전체의 한도를 호출 전에 확인해야 한다(SHALL).

#### Scenario: A failed or incomplete answer stops the workflow

- **WHEN** 단계 호출이 unavailable, oversized, empty 또는 알려진 length·filter·tool 종료로 완료될 때
- **THEN** 후속 호출을 중단하고 원문이 반환된 경우 검증 전에 보존하며, 실패 단계와 완료된 단계 정보를 반환해야 한다(SHALL).
- **AND** 세 단계를 완료한 output을 생성하거나 completed를 반환해서는 안 된다(MUST NOT).

#### Scenario: Existing structured review remains explicit

- **WHEN** 기존 structured API 또는 명시적 structured live 모드를 사용할 때
- **THEN** 기존 JSON 출력·검증·invocation 계약을 유지해야 한다(SHALL).
- **AND** live 모드가 생략되면 단계별 텍스트 경로를 사용해야 한다(SHALL).

### Requirement: Staged review provenance and failure retention

시스템은 workflow·stage identity, revision·설정·원입력, 요청·응답 digest·상태·usage·attempt·원문 경로 및 코드 조립 결과 digest를 연결해야 한다(SHALL). 각 단계가 끝나면 기록을 보존하고 실패 시 이전 기록·원문을 덮어써서는 안 된다(MUST NOT). 모델 원문과 코드가 조립한 JSON의 출처를 구별해야 한다(SHALL).

기록과 collection은 bounded create-only atomic private 파일로 저장해야 하며(SHALL), identity 충돌은 provider 호출 전에 거부해야 한다(SHALL). 저장 실패는 provenance_failed로 반환하고 생성된 진단 경로를 가능한 범위에서 제공해야 한다(SHALL). 기존 invocation 또는 외부 projection에 단계 원문을 추가해서는 안 된다(MUST NOT). 호출 수는 세 단계와 설정된 per-call retry 범위로 제한해야 한다(SHALL).

#### Scenario: A later failure preserves earlier evidence

- **WHEN** 첫 단계가 저장된 뒤 두 번째 단계가 실패할 때
- **THEN** 첫 단계 원문·요청 digest·checkpoint와 두 번째 단계의 반환된 원문·실패 기록을 보존하고 세 번째 단계는 호출하지 않아야 한다(SHALL).

#### Scenario: Collection or manifest persistence fails

- **WHEN** 단계 원문 저장 이후 결과 JSON 또는 manifest 저장이 실패할 때
- **THEN** 성공을 반환하지 않고 이전 raw·checkpoint와 이미 생성된 경로를 보존해야 한다(SHALL).

#### Scenario: Credentials and raw text stay out of metadata

- **WHEN** 단계별 또는 workflow metadata를 저장하거나 콘솔에 결과 위치를 출력할 때
- **THEN** API key·provider exception 원문·단계 답변 본문은 metadata나 자동 콘솔 로그에 포함하지 않아야 한다(SHALL).
- **AND** 답변 본문은 별도 raw 파일과 사용자가 열어 보는 collection JSON에서 확인할 수 있어야 한다(SHALL).

## MODIFIED Requirements

### Requirement: Provider-compatible bounded invocation

시스템은 동일한 review contract와 configuration boundary를 사용해 OpenAI-compatible `chat.completions` endpoint를 제공하는 local Ollama model과 OpenAI API를 호출할 수 있어야 한다(SHALL). `base_url`은 userinfo(username/password), query parameter 또는 URL fragment를 포함해서는 안 되며(MUST NOT), Provider 차이는 credentials-free `base_url`, `SecretStr` credential(`api_key`), model과 bounded configuration으로 표현해야 하며 Reliability domain의 incident/evidence/recovery code가 provider별 business rule을 소유해서는 안 된다(MUST NOT).

이 Capability의 common wire profile은 다음 조건을 만족해야 한다(SHALL). Runtime은 assistant 대화 메시지를 보존하며 호출별 출력 모드를 명시할 수 있어야 한다(SHALL). 기존 structured 호출의 기본 JSON 모드는 유지해야 한다(SHALL).

| Request / behavior | Contract |
| --- | --- |
| Response | Non-streaming. Structured는 JSON object, staged text는 response_format 생략 |
| Sampling | `temperature=0` |
| Token limit | Domain `max_output_tokens`를 wire `max_tokens`로 매핑 |
| Tools and stream | `stream=false`, no-tools |
| Retry | 유한한 timeout과 `max_retries` 이하의 transport retry만 허용 |
| No-retry cases | SDK hidden retry, schema failure, guard failure와 client 4xx retry 금지 |

#### Scenario: Local and cloud-compatible configuration

- **WHEN** 같은 `AgenticReviewInput`에 Ollama의 OpenAI-compatible base URL 또는 OpenAI base URL과 각각의 model/credential을 설정할 때
- **THEN** 시스템은 동일한 review adapter boundary에서 common wire profile request를 만들고 provider-specific Reliability/domain code 변경 없이 선택한 경로의 response를 처리해야 한다(SHALL).

#### Scenario: Provider timeout or unavailability

- **WHEN** configured endpoint가 timeout, connection failure 또는 bounded retry 이후 unavailable 상태를 반환할 때
- **THEN** 시스템은 unavailable invocation result와 failure provenance를 반환하고 review output, approval, recovery 또는 mutation authority를 생성해서는 안 된다(MUST NOT).

#### Scenario: Provider returns schema-invalid content

- **WHEN** structured 경로의 provider가 HTTP-level success를 반환했지만 JSON 또는 `AgenticReviewOutput`으로 검증할 수 없는 content를 반환할 때
- **THEN** 시스템은 validation_failed result와 failure provenance를 반환하고 accepted advisory review 또는 외부 action을 반환해서는 안 된다(MUST NOT).

#### Scenario: Text invocation keeps history without JSON forcing

- **WHEN** caller가 assistant 이력과 text 출력 모드를 명시할 때
- **THEN** Runtime은 메시지 순서와 원문을 보존하고 SDK wire에 response_format을 보내지 않아야 한다(SHALL).
- **AND** 같은 adapter의 다음 기본 호출은 기존 JSON 모드를 사용해야 한다(SHALL).
