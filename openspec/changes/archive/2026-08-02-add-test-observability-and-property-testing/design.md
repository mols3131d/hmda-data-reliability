---
type: openspec-rpi
category: design
title: Test Observability and Property Testing Design
description: pytest hook 기반 OpenTelemetry span과 Hypothesis property test의 최소 설계를 정의한다.
relatedArtifacts:
  - add-test-observability-and-property-testing
tags:
  - testing
  - opentelemetry
  - hypothesis
---

## Context

pytest는 기본적으로 `pytest-xdist -n auto`를 사용한다. OpenTelemetry Python은 API와 SDK를 분리한다. `pytest-opentelemetry`는 공식 OpenTelemetry 또는 pytest project가 관리하는 plugin으로 확인되지 않았고 Python 3.13과 xdist 지원 계약도 검증되지 않았다.

## Goals / Non-Goals

**Goals:**

- test item별 duration, outcome, marker, worker/run identity를 span으로 기록한다.
- tracing을 명시적으로 활성화하지 않은 일반 test 실행에는 동작과 비용을 추가하지 않는다.
- property test가 순수 helper의 넓은 입력 공간에서 불변성을 검증한다.
- dependency와 hook을 Python 3.13 및 현재 pytest 설정으로 검증한다.

**Non-Goals:**

- application runtime 자동 instrumentation
- collector, backend, dashboard 배포
- metrics와 logs export
- 검증되지 않은 제3자 plugin 채택

## Decisions

### Official SDK and local pytest hooks

`opentelemetry-api`와 `opentelemetry-sdk`를 dev dependency로 사용하고 root `tests/conftest.py`의 pytest hooks에서 span lifecycle을 관리한다. 제3자 `pytest-opentelemetry`를 직접 설치하는 대안은 공급망 provenance와 xdist 호환성이 확인될 때까지 보류한다.

### Opt-in tracing

`OTEL_TEST_TRACING=1`일 때만 OpenTelemetry module을 import하고 `TracerProvider`와 `ConsoleSpanExporter`를 만들어 test span을 기록한다. 기본 실행은 기존 pass/fail, parallelism, report 생성 동작을 유지한다. OTLP export는 collector와 backend가 정해진 뒤 별도 change에서 추가한다.

### Worker-safe attributes

각 span은 test `nodeid`, phase, outcome, duration과 함께 `PYTEST_XDIST_WORKER`, `PYTEST_XDIST_TESTRUNUID` 값을 기록한다. worker process마다 provider를 초기화하고 session 종료에서 flush와 shutdown을 수행한다.

### Focused property test

Hypothesis를 dev dependency로 추가하고 DuckDB identifier/string quoting helper의 escaping 불변성을 검증한다. database I/O나 large fixture 생성에는 property test를 적용하지 않는다.

## Risks / Trade-offs

- **Console output은 중앙 수집을 제공하지 않음** → backend 도입 시 OTLP exporter dependency와 환경 설정을 별도 change로 추가한다.
- **xdist worker마다 provider가 존재함** → worker와 run UID를 attribute로 기록하고 worker 종료 시 flush한다.
- **Hypothesis example 수가 test 시간을 늘림** → 빠른 순수 helper에만 적용하고 deadline과 profile을 과도하게 custom하지 않는다.
- **custom pytest hook 유지보수 비용** → 필요한 hook과 attribute만 구현하고 upstream plugin 검증 시 교체 가능하게 test 경계에 한정한다.

## Migration Plan

1. dev dependency와 lockfile을 갱신한다.
1. opt-in pytest tracing hook을 추가한다.
1. 대표 property test와 tracing hook unit test를 추가한다.
1. focused test, 전체 lint, OpenSpec validation을 실행한다.

Rollback은 dependency, hook, property test를 제거하는 것으로 완료된다. production data와 runtime contract에는 migration이 없다.

## Open Questions

- CI 또는 local collector가 정해지면 OTLP HTTP와 gRPC 중 어느 exporter를 표준으로 사용할지 별도 결정한다.
- `pytest-opentelemetry`의 maintainer, source repository, Python 3.13 및 xdist 지원이 검증되면 custom hook 대체 여부를 재평가한다.
