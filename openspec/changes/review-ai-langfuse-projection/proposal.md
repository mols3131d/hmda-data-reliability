---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Optional Langfuse Projection
description: 합성 live review의 검증된 record를 optional 관찰 및 human annotation 대상으로 표시한다.
---

## Why

현재 사람은 invocation JSON에서 input/output과 provenance를 찾아 별도로 다섯 rubric 항목을 기록한다. 동일 합성 사례의 정보를 한 화면에 표시하고 항목별 comment를 남길 수 있도록 optional Langfuse projection을 추가한다. 실제 작업 절감은 live human proof 전까지 가설이다.

## What Changes

- 기존 synthetic live harness의 명시적 opt-in으로 검증된 record만 전송한다.
- 외부 연동 실패와 종료 지연을 core 결과에서 격리하고 SDK를 선택 설치한다.
- exact output에 대한 `rubric_v1` 수동 setup과 completeness 확인 절차를 제공한다.

## Boundaries

- **In Scope:** 실행 후 projection, offline 계약 검증, 수동 annotation 안내.
- **Out of Scope:** 자동 human score 작성, annotation importer, evaluation core 변경, provider 자동 계측, prompt 관리, production self-hosting, recovery authority 변경.
- 사용자가 live destination 없이 로컬 구현·검증을 먼저 진행하도록 지정했다. 실제 ingestion과 human annotation은 별도 미검증으로 유지한다.

## Capabilities

### Modified Capabilities

#### `reliability-agentic-review`

- 기존 invocation evidence에 optional 외부 projection 경계를 추가한다.

## Impact

- Review AI 전용 연동 모듈, live harness, 선택 dependency, 관련 테스트와 사용 안내.

## Contract Handoff

로컬 구현의 두 요구사항은 #251의 문서 정합성 후속 작업에서 [canonical Spec](../../specs/reliability-agentic-review/spec.md)으로 동기화했다. Current behavior의 normative owner는 canonical Spec이며, 이 Change는 구현 의도와 delta 이력을 보존한다.

이 Change는 #251의 문서·Spec 정합성 수정이 전달되는 동안 active로 유지하고, 해당 변경의 병합 후 archive 대상으로 정리한다. 실제 ingestion/UI와 human annotation은 별도 후속 검증이며 로컬 구현의 완료, Spec 동기화 또는 archive 조건에 포함하지 않는다. 미검증 상태는 [Testing Guide](../../../docs/development/testing.md#optional-langfuse-projection)의 실행 절차와 revision별 evidence에서 계속 구분한다.
