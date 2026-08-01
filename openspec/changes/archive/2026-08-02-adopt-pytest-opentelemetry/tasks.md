---
type: openspec-rpi
category: tasks
title: Adopt pytest-opentelemetry Tasks
description: upstream pytest tracing plugin 채택 작업을 추적한다.
relatedArtifacts:
  - adopt-pytest-opentelemetry
tags:
  - testing
  - opentelemetry
  - pytest
---

## 1. Dependency and Implementation

- [x] 1.1 `pytest-opentelemetry` dev dependency와 lockfile을 갱신한다
- [x] 1.2 local pytest tracing hook과 중복 implementation test를 제거한다

## 2. Plugin Contract

- [x] 2.1 plugin CLI registration과 test span 생성을 검증한다
- [x] 2.2 실제 xdist 실행 호환성을 검증한다
- [x] 2.3 development 문서에 plugin 사용법과 OTLP export command를 반영한다

## 3. Validation and Lifecycle

- [x] 3.1 focused test와 전체 test suite를 실행한다
- [x] 3.2 Ruff, mypy, rumdl, OpenSpec, lockfile validation을 실행한다
- [x] 3.3 main spec sync, 독립 review, archive를 완료한다
- [x] 3.4 변경을 도메인별 commit으로 분리한다
