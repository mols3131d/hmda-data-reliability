---
type: openspec-rpi
title: "Review: add-test-observability-and-property-testing"
description: OpenTelemetry test tracing과 Hypothesis 도입 구현을 검증하고 승인한다.
category: review
status: approved
relatedArtifacts:
  - add-test-observability-and-property-testing
---

# Review: add-test-observability-and-property-testing

## Summary

**Approved.** 공식 OpenTelemetry API/SDK와 Hypothesis가 Python 3.13 dev dependency로 추가됐고, opt-in console tracing, phase별 test 결과, xdist identity, property-based escaping 계약이 구현과 test에서 일치한다. 미해결 Blocker와 Major finding은 없다.

## Reconciliation

| Axis | Result | Evidence |
| --- | --- | --- |
| Completeness | Pass | spec 요구사항 ↔ pytest hook, root gate, Hypothesis tests |
| Correctness | Pass | in-memory span assertions, setup/teardown failure tests, opt-in runtime span |
| Coherence | Pass | proposal/design/docs가 console-only export와 OTLP 제외 범위로 정렬됨 |
| Regression | Pass | default-disabled gate, actual `-n 2` worker registration, full suite 117 tests |
| Evidence | Pass | pytest, Ruff, mypy, rumdl, OpenSpec, lockfile checks |
| Risk | Pass | worker console payload 수집은 후속 backend/exporter change에서 검증 |

## Findings

| Level | Owner | Finding | Evidence | Required action |
| --- | --- | --- | --- | --- |
| Note | Implement | 실제 xdist test는 worker registration과 identity environment를 검증하고, span payload는 동일 plugin의 in-memory test로 검증한다. xdist worker console payload 자체는 stdout 전달 제한으로 직접 assertion하지 않는다. | `tests/test_telemetry.py`, `pytest-xdist` subprocess 7 tests pass | 병렬 console output을 공식 contract로 확장할 때 file 또는 OTLP exporter integration test 추가 |
| Note | Implement | `SimpleSpanProcessor`는 span 종료 시 동기 export하며 provider shutdown 호출 횟수는 별도 spy로 검증하지 않는다. | `tests/_telemetry.py`, OpenTelemetry 1.44.0 console exporter | 비동기 exporter를 도입할 때 flush/shutdown failure test 추가 |
| Note | Implement | `uv` resolver가 기존 `pyzmq` PyPy marker를 정규화했다. | `uv.lock`, `uv lock --check` pass | 없음 |

## Validation Observed

| Check | Result | Notes |
| --- | --- | --- |
| `uv run pytest -n 0 tests/test_telemetry.py` | Pass | 7 passed; gate, phase failure, actual xdist worker integration 포함 |
| `uv run pytest` | Pass | 117 passed |
| `OTEL_TEST_TRACING=1 uv run pytest -n 0 -q tests/data_platform/test_sql.py::test_quote_identifier_escapes_double_quotes` | Pass | setup/call/teardown span과 duration console JSON 확인 |
| `uv run ruff format --check ... && uv run ruff check ...` | Pass | 변경 Python 4 files |
| `MYPYPATH=src uv run mypy ...` | Pass | 변경 Python 4 files |
| `uv run rumdl check docs/DEVELOPMENT.md openspec/changes/add-test-observability-and-property-testing` | Pass | Markdown 문제 없음 |
| `openspec validate add-test-observability-and-property-testing` | Pass | change valid |
| `uv lock --check` | Pass | 196 packages resolved, lock consistent |

## Amendments

| Amendment | Reflected in OpenSpec? | Review impact |
| --- | --- | --- |
| exporter scope를 선택형 OTLP에서 opt-in console-only로 축소 | Yes | 구현과 문서 불일치 해소 |
| OpenTelemetry import를 opt-in branch 내부로 이동 | Yes | default-disabled 비용과 coupling 제거 |
| root gate, setup/teardown failure, actual xdist worker tests 추가 | Yes | 초기 validation gap 해소 |

## Route

| Status | Next action |
| --- | --- |
| approved | OpenSpec archive 가능 |
