---
type: openspec-spec-driven-tdd-spec
category: spec
title: reliability-agentic-review
description: 일반 실행과 명시적 legacy 실행 경계를 정의합니다.
---

## MODIFIED Requirements

### Requirement: Staged prose review collection

일반 review_null_spike API와 직접 service 및 기본 live CLI는 동일한 현재 실행을 사용해야 한다(SHALL). 시스템은 같은 immutable 사례의 근거 검토·초안 비판·종합을 고정 순서로 실행하고 모델에 JSON 생성 대신 한국어 텍스트를 요청해야 한다(SHALL). 호출마다 원래 canonical input과 완료된 이전 assistant 응답을 유지하고 전체 요청의 byte cap과 digest를 계산해야 한다(SHALL). 사례 데이터나 이전 모델 답변이 단계·system 지시를 선택해서는 안 된다(MUST NOT).

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

- **WHEN** 명시적 legacy API 또는 MODE=legacy와 LEGACY_PROMPT_VERSION으로 선택한 live 모드를 사용할 때
- **THEN** 기존 JSON 출력·검증·invocation 계약을 유지해야 한다(SHALL).
- **AND** live 모드가 생략되면 단계별 텍스트 경로를 사용해야 한다(SHALL).

### Requirement: Structured null-spike review input

시스템은 `null_spike` `Incident`, 실제 제공된 하나 이상의 `Evidence`, 기존 `RemediationDraft`, `PromptIdentity`와 caller가 제공한 non-empty `project_revision`을 보존하는 call-scoped snapshot `AgenticReviewInput`을 받아야 한다(SHALL). Snapshot 생성 뒤 caller가 보유한 nested list 또는 mapping을 변경해도 prompt, validation과 provenance에 사용되는 input은 변하지 않아야 한다(SHALL).

Input은 다음 invariant를 모두 만족할 때만 provider review 대상으로 인정해야 한다(SHALL).

- **Incident and draft identity:** `incident.incident_type`와 `draft.incident_type`는 정확히 `null_spike`이고, incident와 draft의 `incident_id`, `asset_name`과 `partition`이 일치한다.
- **Evidence linkage:** 제공된 Evidence ID는 unique하고 `incident.evidence_refs` 및 `draft.evidence_refs`와 같은 set이어야 한다. 각 Evidence는 자신이 나타내는 asset과 partition identity를 보존해야 한다.
- **Canonical target:** 정확히 하나의 canonical target Evidence가 있어야 하며, 그 asset과 partition은 incident와 일치해야 한다. 이 Evidence는 `source=profile`, `payload.rule=null_spike`, non-empty string `column`, finite numeric `baseline_null_rate`, `current_null_rate`, `delta`와 `threshold`를 가져야 한다. Target column과 numeric facts는 이 Evidence에서만 유도한다. 명시적으로 참조된 bounded contextual Evidence는 다른 asset 또는 partition을 나타낼 수 있다.
- **Prompt metadata:** 기존 PromptIdentity의 template_id와 v1/v2/v3는 legacy 실행 및 과거 snapshot 해석을 위해 보존한다. 내부 canonical projection에서 이 계약을 재사용하더라도 일반 실행의 현재 프롬프트 선택에 version을 사용해서는 안 된다(MUST NOT). Legacy API 호출자는 identity를 명시하고 CLI는 LEGACY_PROMPT_VERSION을 명시해야 한다(SHALL).

이 Capability의 review entry point는 `null_spike` 외 incident type을 지원해서는 안 된다(MUST NOT).

#### Scenario: Valid evidence-bound input

- **WHEN** 위의 identity 관계, complete Evidence set, unique canonical target Evidence, `PromptIdentity`와 `project_revision`을 만족하는 `null_spike` 입력이 제공될 때
- **THEN** 시스템은 snapshot `AgenticReviewInput`을 만들고 provider invocation을 진행할 수 있어야 한다.

#### Scenario: Mismatched input is rejected before invocation

- **WHEN** Evidence가 incident 또는 draft의 reference set에서 누락되거나 incident/draft의 identity 또는 type이 다르거나 canonical target Evidence의 asset/partition이 incident와 다를 때
- **THEN** 시스템은 `input_rejected` result를 반환하고 provider invocation 또는 invocation evidence 생성을 수행해서는 안 된다(MUST NOT).

#### Scenario: Referenced contextual evidence retains its own identity

- **GIVEN** incident identity와 일치하는 canonical target Evidence 및 incident/draft가 명시적으로 참조한 다른 asset의 contextual Evidence가 주어질 때
- **WHEN** review input을 생성할 때
- **THEN** canonical target의 asset과 partition은 incident와 일치해야 하고 contextual Evidence는 자체 identity를 보존한 채 input 및 bounded context에 포함될 수 있어야 한다.

#### Scenario: Invalid canonical target evidence

- **WHEN** canonical target Evidence가 없거나 둘 이상이거나 rule, column 또는 required numeric fact가 없거나 non-finite일 때
- **THEN** 시스템은 `input_rejected` result를 반환하고 provider invocation을 수행해서는 안 된다(MUST NOT).

#### Scenario: Unsupported incident type

- **WHEN** `volume_drop`, `schema_drift` 또는 `freshness_delay` Incident를 이 Capability의 review entry point에 제공할 때
- **THEN** 시스템은 명시적인 `input_rejected` result를 반환하고 provider invocation, approval 또는 recovery를 수행해서는 안 된다(MUST NOT).

### Requirement: Opt-in grounded review instructions

시스템은 `v3` prompt를 명시적으로 선택할 수 있어야 한다(SHALL). v3 instruction은 closed output의 field/type 및 conditional priority를 설명하면서 task-specific 내용 예시를 포함하지 않아야 한다(SHALL). Rate와 percentage-point 차이, delta threshold 및 baseline-zero에서 정의되지 않는 상대 변화율을 구별하도록 안내해야 한다(SHALL). Structured facts는 입력 값을 그대로 복사하고 설명에서만 읽기 쉬운 단위 표현을 사용하도록 안내해야 한다(SHALL).

Instruction은 제공된 evidence와 실제 draft를 대조하고 미확인 원인·검증 결과를 확정하지 않으며 존재하지 않는 draft action을 비판하지 않도록 안내해야 한다(SHALL). Utility는 단순 재서술을 넘어 확인 우선순위와 결과에 따라 달라지는 사람의 다음 판단에 연결하도록 안내해야 한다(SHALL). 이는 prompt 계약이며 임의 free-text를 거부하는 새 deterministic acceptance 규칙이 아니다.

과거 Python identity 기본 v1과 live harness 기본 v2는 legacy 기록 해석에만 해당한다. 일반 API와 live 기본은 현재 한국어 단계별 텍스트 실행을 사용해야 하며(SHALL), legacy 실행은 version을 명시해야 한다(SHALL). 과거 v1/v2/v3 실행은 기록된 project_revision의 renderer와 리소스로 재현하고 저장된 identity·digest를 재작성해서는 안 된다(MUST NOT). v3 지원이나 현재 실행 경로의 전환만으로 human utility 또는 모델 품질 채택을 주장해서는 안 된다(MUST NOT).

#### Scenario: Candidate version renders without content examples

- **WHEN** caller가 `v3`를 명시적으로 선택하고 기존 valid input을 render할 때
- **THEN** 동일 canonical projection과 advisory boundary를 사용하면서 위 수치·근거·draft 지침을 담은 별도 digest의 prompt를 생성해야 한다(SHALL).

#### Scenario: Historical versions retain replay identity

- **WHEN** 과거 canonical input과 `v1`, `v2` 또는 `v3` version을 기록된 `project_revision`의 renderer와 리소스로 다시 render할 때
- **THEN** 과거 invocation의 message digest와 같아야 하며(SHALL) 현재 active 기본값의 변경으로 저장된 version이나 과거 기록의 해석을 바꿔서는 안 된다(MUST NOT).
