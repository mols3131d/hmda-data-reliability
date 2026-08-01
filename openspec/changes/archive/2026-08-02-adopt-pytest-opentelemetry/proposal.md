---
type: openspec-rpi
category: proposal
title: Adopt pytest-opentelemetry
description: local pytest tracing hook을 pytest-opentelemetry plugin으로 교체한다.
relatedArtifacts:
  - adopt-pytest-opentelemetry
tags:
  - testing
  - opentelemetry
  - pytest
---

## Why

현재 project는 pytest tracing을 local hook으로 직접 유지한다. `pytest-opentelemetry`가 test·fixture span, xdist, OTLP export를 제공하므로 custom implementation을 제거하고 upstream contract를 사용한다.

## What Changes

- `pytest-opentelemetry`를 dev dependency로 추가한다.
- local pytest tracing hook과 전용 implementation test를 제거한다.
- plugin의 CLI registration, 기본 span 생성, xdist 실행을 focused test로 검증한다.
- OTLP export는 `--export-traces`와 표준 OpenTelemetry exporter 환경변수를 사용한다.
- Hypothesis property test는 유지한다.
- **BREAKING** local hook의 marker, phase outcome/duration, worker/run UID custom attribute contract를 upstream의 test·fixture·run span contract로 교체한다.

## Capabilities

### New Capabilities

없음.

### Modified Capabilities

- `test-quality-observability`: local hook 우선 계약을 검증된 pytest plugin 채택 계약으로 변경

## Impact

- `pyproject.toml`과 `uv.lock`
- pytest plugin loading과 trace export command
- test observability tests와 development 문서
- `test-quality-observability` main spec
