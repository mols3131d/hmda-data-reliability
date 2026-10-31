---
type: openspec-spec-driven-tdd-spec
category: spec
title: reliability-agentic-review
description: 한국어 프롬프트 작성 계약을 연결하고 historical replay를 기록된 revision에 고정합니다.
---

## MODIFIED Requirements

### Requirement: Canonical provider input projection

시스템은 provider user data와 invocation provenance에 사용할 `canonical_input`을 `AgenticReviewInput`에서 결정적으로 투영해야 하며(SHALL), 다음 allowlisted field 외의 runtime field를 포함해서는 안 된다(MUST NOT).

| Source | Allowed fields |
| --- | --- |
| `Incident` | `incident_id`, `incident_type`, `asset_name`, `partition`, `status`, `severity` |
| Each `Evidence` | `evidence_id`, `source`, `asset_name`, `partition`, `observed_at`, `summary`, `payload` |
| `RemediationDraft` | `incident_id`, `incident_type`, `asset_name`, `partition`, `rca_summary`, `evidence_refs`, `affected_assets`, `recommended_actions`, `dbt_test_suggestions`, `backfill_actions`, `validation_actions`, `requires_approval` |
| Review facts | `deterministic_facts` |

`canonical_input`은 같은 snapshot에서 같은 canonical JSON byte sequence를 생성해야 한다(SHALL). System instruction과 user data는 분리해야 하며(SHALL), `canonical_input` 안의 Evidence summary/payload와 draft text는 instruction이 아니라 untrusted data로 취급해야 한다(SHALL).

프롬프트 리소스, 한국어 지시문·설명문과 revision별 변경 추적은 [review-ai-prompt-engineering](../review-ai-prompt-engineering/spec.md) 계약을 따라야 한다(SHALL).

Rendered messages가 configured `max_prompt_bytes`를 넘으면 시스템은 provider call 전에 `input_rejected`를 반환하고 invocation evidence를 만들지 않아야 한다(MUST NOT).

#### Scenario: Canonical projection is deterministic and bounded

- **WHEN** 같은 valid `AgenticReviewInput`을 반복 render할 때
- **THEN** 같은 allowlisted `canonical_input`과 같은 prompt digest가 생성되어야 하며 allowlist 밖의 Incident, Evidence, Draft 또는 runtime field는 provider user data에 포함되지 않아야 한다(MUST NOT).

#### Scenario: Prompt-injection text remains data

- **WHEN** Evidence summary/payload 또는 draft text에 명령문 형태의 문자열이 있을 때
- **THEN** 문자열은 `canonical_input`의 data로만 serialize되어야 하며 system instruction 또는 execution command로 승격되어서는 안 된다(MUST NOT).

#### Scenario: Versioned output instructions preserve historical replay

- **WHEN** `v2` prompt를 render할 때
- **THEN** system instruction은 `evidence_used`, `findings`, `uncertainties`, `utility_contributions`와 nested `evidence_refs`의 배열 타입, 문자열·object element 구분, canonical facts 복사 및 `investigation_priority`만의 필수 `priority` 조건을 명시해야 한다(SHALL).
- **AND** 과거 prompt는 저장된 version과 canonical input을 기록된 `project_revision`의 renderer와 리소스에 제공해 재생할 수 있어야 하며(SHALL), 그 revision의 message digest와 일치해야 한다(SHALL).

#### Scenario: Oversized prompt is rejected before provider invocation

- **WHEN** canonical input을 포함한 rendered messages가 configured `max_prompt_bytes`를 넘을 때
- **THEN** 시스템은 `input_rejected` result를 반환하고 provider invocation 또는 invocation evidence 생성을 수행해서는 안 된다(MUST NOT).

### Requirement: Opt-in grounded review instructions

시스템은 `v3` prompt를 명시적으로 선택할 수 있어야 한다(SHALL). v3 instruction은 closed output의 field/type 및 conditional priority를 설명하면서 task-specific 내용 예시를 포함하지 않아야 한다(SHALL). Rate와 percentage-point 차이, delta threshold 및 baseline-zero에서 정의되지 않는 상대 변화율을 구별하도록 안내해야 한다(SHALL). Structured facts는 입력 값을 그대로 복사하고 설명에서만 읽기 쉬운 단위 표현을 사용하도록 안내해야 한다(SHALL).

Instruction은 제공된 evidence와 실제 draft를 대조하고 미확인 원인·검증 결과를 확정하지 않으며 존재하지 않는 draft action을 비판하지 않도록 안내해야 한다(SHALL). Utility는 단순 재서술을 넘어 확인 우선순위와 결과에 따라 달라지는 사람의 다음 판단에 연결하도록 안내해야 한다(SHALL). 이는 prompt 계약이며 임의 free-text를 거부하는 새 deterministic acceptance 규칙이 아니다.

현재 개발 비교 단계는 Python identity 기본 `v1`과 live harness 기본 `v2`를 사용한다. 채택 판단 이후에는 [review-ai-prompt-engineering](../review-ai-prompt-engineering/spec.md)의 lifecycle 계약에 따라 하나의 active 기본값으로 함께 전환해야 한다(SHALL). 과거 `v1`/`v2` 실행은 기록된 `project_revision`의 renderer와 리소스를 사용할 때 저장된 instruction과 digest를 재생할 수 있어야 한다(SHALL). 언어 변경으로 현재 revision의 digest가 달라져도 과거 invocation의 기록을 재작성해서는 안 된다(MUST NOT). v3 지원만으로 human utility나 candidate 채택을 주장해서는 안 된다(MUST NOT).

#### Scenario: Candidate version renders without content examples

- **WHEN** caller가 `v3`를 명시적으로 선택하고 기존 valid input을 render할 때
- **THEN** 동일 canonical projection과 advisory boundary를 사용하면서 위 수치·근거·draft 지침을 담은 별도 digest의 prompt를 생성해야 한다(SHALL).

#### Scenario: Historical versions retain replay identity

- **WHEN** 과거 canonical input과 `v1`, `v2` 또는 `v3` version을 기록된 `project_revision`의 renderer와 리소스로 다시 render할 때
- **THEN** 과거 invocation의 message digest와 같아야 하며(SHALL) 현재 active 기본값의 변경으로 저장된 version이나 과거 기록의 해석을 바꿔서는 안 된다(MUST NOT).
