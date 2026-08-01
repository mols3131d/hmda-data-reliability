---
type: openspec-rpi
category: design
title: pytest-opentelemetry Adoption Design
description: local tracing hook을 upstream pytest plugin으로 교체하는 설계를 정의한다.
relatedArtifacts:
  - adopt-pytest-opentelemetry
tags:
  - testing
  - opentelemetry
  - pytest
---

## Context

`pytest-opentelemetry` 1.1.0은 Python 3.8 이상을 선언하고 `pytest11` entry point, test·fixture spans, xdist 전용 plugin, OTLP/gRPC export option을 제공한다. 현재 project의 local hook은 이 기능 일부를 중복 구현한다.

## Goals / Non-Goals

**Goals:**

- upstream plugin을 pytest auto-loading으로 사용한다.
- local tracing implementation과 유지보수 비용을 제거한다.
- 기본 test 실행은 network export를 수행하지 않는다.
- export behavior를 plugin option과 표준 OpenTelemetry exporter 환경변수 조합으로 제어한다.
- plugin CLI, test span, xdist 실행을 focused check로 검증한다.

**Non-Goals:**

- plugin source fork 또는 wrapper 작성
- collector와 observability backend 배포
- plugin이 제공하지 않는 custom span attribute 유지
- application runtime instrumentation

## Decisions

### Replace the local plugin

`pytest-opentelemetry`를 dev dependency로 추가하고 `tests/_telemetry.py`, root `tests/conftest.py`, local hook test를 제거한다. 동일 기능을 감싸는 adapter는 만들지 않는다.

### Use pytest entry-point loading

plugin은 `pytest11` entry point로 자동 로드한다. `--trace-per-test`, `--trace-parent`, `--export-traces` option은 upstream contract를 그대로 사용한다.

### Use upstream export semantics

기본 environment에서는 SDK span을 생성하지만 network exporter를 구성하지 않는다. `--export-traces`는 기본 OTLP/gRPC exporter를 구성하며, `OTEL_TRACES_EXPORTER`와 `OTEL_EXPORTER_OTLP_ENDPOINT`가 exporter 선택과 endpoint를 override할 수 있다.

### Test the public surface

implementation detail 대신 `pytest --help` option registration, console exporter의 fixture/test/run span payload, 실제 xdist 실행을 검증한다.

## Risks / Trade-offs

- **13개 transitive dependency 추가** → custom hook 제거와 OTLP/container resource 기능을 upstream에 위임하는 비용으로 수용한다.
- **기존 custom attributes 제거** → marker, phase outcome/duration, worker/run UID 대신 plugin의 `pytest.nodeid`, code, fixture/test/run span contract를 사용한다.
- **plugin release cadence 의존** → version lower bound와 focused integration tests로 회귀를 감지한다.
- **기본 span 생성 비용** → provider, resource detector, span hook이 controller와 worker에서 실행된다. overhead가 문제가 될 때 plugin opt-in loading을 별도 평가한다.

## Migration Plan

1. dependency와 lockfile을 갱신한다.
1. local tracing implementation과 tests를 제거한다.
1. upstream plugin public surface tests와 문서를 추가한다.
1. focused/전체 test와 static checks를 실행한다.
1. main spec을 sync하고 change를 review·archive한다.
