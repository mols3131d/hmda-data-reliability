---
type: openspec-spec-driven-tdd-spec
category: spec
title: Optional Review Projection
description: 검증된 합성 invocation의 외부 projection과 human annotation 경계를 정의한다.
---

## ADDED Requirements

### Requirement: Optional synthetic invocation projection

시스템은 기존 synthetic live harness에서 별도 opt-in으로만 Langfuse projection을 수행해야 한다(SHALL). 비활성 상태에서는 SDK import, 초기화와 외부 호출을 하지 않아야 한다(MUST). 기존 core result, local provenance와 exit 의미를 유지해야 한다(MUST).

#### Scenario: Disabled integration without SDK

- **WHEN** Langfuse opt-in이 없고 SDK가 설치되지 않았다
- **THEN** 기존 harness 동작이 유지되고 Langfuse를 import하거나 호출하지 않는다

#### Scenario: Verified accepted record

- **WHEN** harness provenance 검증을 통과한 accepted record의 canonical input이 현재 합성 사례와 일치한다
- **THEN** invocation, revision, prompt identity/digest, rubric과 exact output digest를 보존한 allowlist projection을 생성한다
- **AND** bounded facts, draft, evidence와 context gaps 및 accepted structured output을 사람에게 제공한다

#### Scenario: Unsafe or missing evidence

- **WHEN** input rejection, provenance failure, provenance 검증 실패, 합성 입력 불일치 또는 65536 UTF-8 byte 초과 projection이 발생한다
- **THEN** 외부 전송을 생략하고 잘린 context/output을 채점 대상으로 표시하지 않는다

#### Scenario: Durable failed record

- **WHEN** 검증된 unavailable 또는 validation_failed record를 표시한다
- **THEN** identity와 typed status만 표시하고 input, partial output, raw failure text와 annotation target을 포함하지 않는다

#### Scenario: Export boundary failure

- **WHEN** init, projection, export, flush, shutdown 또는 configured timeout이 실패한다
- **THEN** sanitized integration status를 별도로 출력하고 기존 core result, local record와 exit 의미를 유지한다
- **AND** 외부 연동 대기는 기본 5초, 설정 범위 0초 초과 60초 이하로 제한한다

#### Scenario: Remote ingestion is unknown

- **WHEN** exporter가 오류 없이 반환했지만 원격 조회를 수행하지 않았다
- **THEN** submitted_unverified로 보고하고 delivery 또는 human proof 성공을 주장하지 않는다
- **AND** projection 시간과 실제 기록된 model latency를 구분한다

### Requirement: Integration-local human annotation mapping

수동 annotation은 invocation_id, exact output_digest와 rubric_v1에 결합되어야 한다(MUST). 각 criterion의 0/1/2 integer와 non-empty rationale가 정확히 한 번씩 있을 때만 complete로 판정해야 한다(SHALL). 이 판정은 human provenance, utility acceptance 또는 repository evaluation 생성 권한을 부여하지 않는다(MUST).

#### Scenario: Missing or invalid annotation

- **WHEN** 다섯 항목 중 누락, 중복, 범위 밖 값, 비정수, 빈 rationale 또는 target 불일치가 있다
- **THEN** incomplete로 판정하며 UI 완료 표시는 이를 덮어쓰지 않는다

#### Scenario: Complete local annotation shape

- **WHEN** exact accepted output target과 다섯 유효한 criterion/rationale가 제공된다
- **THEN** integration-local completeness만 확인하며 HumanUtilityEvaluation, candidate 승인 또는 recovery action을 만들지 않는다
