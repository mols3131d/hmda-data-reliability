---
type: openspec-rpi
category: proposal
title: Test Observability and Property Testing
description: pytest 실행 trace와 property-based testing을 최소 구성으로 도입한다.
relatedArtifacts:
  - add-test-observability-and-property-testing
tags:
  - testing
  - opentelemetry
  - hypothesis
---

## Why

현재 test suite는 pass/fail과 HTML report는 제공하지만, 분산 실행의 test별 timing과 실패 흐름을 표준 telemetry로 내보내는 계약이 없다. 경계값과 조합을 example-based test만으로 검증해 입력 공간의 결함을 놓칠 위험도 있다.

## What Changes

- pytest test item을 OpenTelemetry span으로 기록하는 opt-in test tracing을 추가한다.
- `pytest-xdist` worker와 test run을 구분할 수 있는 trace attribute를 포함한다.
- Hypothesis를 dev dependency로 추가하고 순수 helper의 핵심 불변성을 property test로 검증한다.
- 검증되지 않은 제3자 `pytest-opentelemetry` plugin은 직접 채택하지 않고, 공식 OpenTelemetry SDK와 pytest hook으로 필요한 최소 동작을 구현한다.
- production application instrumentation, collector 배포, 원격 backend 운영은 제외한다.

## Capabilities

### New Capabilities

- `test-quality-observability`: pytest 실행 telemetry와 property-based testing의 동작 및 검증 계약

### Modified Capabilities

없음.

## Impact

- `pyproject.toml` dev dependency와 pytest 설정
- pytest plugin 또는 root `conftest.py`
- 대표 unit test
- local/CI 환경의 선택적 console trace 출력
