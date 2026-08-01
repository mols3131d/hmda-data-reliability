---
type: openspec-rpi
category: spec
title: Test Quality Observability Specification
description: pytest trace와 property-based testing의 요구사항을 정의한다.
relatedArtifacts:
  - add-test-observability-and-property-testing
tags:
  - testing
  - opentelemetry
  - hypothesis
---

## ADDED Requirements

### Requirement: Opt-in pytest tracing

Test suite는 명시적인 test tracing opt-in이 설정된 경우 각 test item의 실행 결과를 OpenTelemetry span으로 기록해야 한다(SHALL). Opt-in이 없으면 기존 pytest 동작과 결과를 유지해야 한다(MUST).

#### Scenario: Tracing disabled by default

- **WHEN** 사용자가 test tracing opt-in 없이 pytest를 실행한다
- **THEN** test suite는 OpenTelemetry provider나 exporter를 초기화하지 않고 기존 test 결과를 생성한다

#### Scenario: Tracing enabled

- **WHEN** 사용자가 test tracing opt-in을 설정하고 pytest를 실행한다
- **THEN** 각 test item span은 node ID, outcome, duration, execution phase를 포함한다

### Requirement: Distributed test identity

Test span은 xdist worker와 전체 test run을 구분할 수 있어야 한다(SHALL).

#### Scenario: xdist worker execution

- **WHEN** test item이 xdist worker에서 실행된다
- **THEN** span은 가능한 경우 worker ID와 shared test run UID를 attribute로 포함한다

### Requirement: Property-based invariant testing

Test suite는 deterministic pure helper의 입력 불변성을 Hypothesis로 검증해야 한다(SHALL).

#### Scenario: Generated SQL identifier input

- **WHEN** Hypothesis가 null 문자가 없는 non-empty identifier를 생성한다
- **THEN** quoting helper 결과는 외부 double quote와 내부 double quote escaping 계약을 만족한다

#### Scenario: Generated SQL string input

- **WHEN** Hypothesis가 임의의 string literal을 생성한다
- **THEN** quoting helper 결과는 외부 single quote와 내부 single quote escaping 계약을 만족한다

### Requirement: Supported dependency provenance

Test tooling dependency는 Python 3.13 호환성과 upstream provenance가 확인되어야 한다(MUST).

#### Scenario: Unverified pytest telemetry plugin

- **WHEN** telemetry plugin의 maintainer, source, Python 3.13 또는 xdist 계약을 확인할 수 없다
- **THEN** project는 해당 plugin을 설치하지 않고 공식 OpenTelemetry package와 local pytest hook을 사용한다
