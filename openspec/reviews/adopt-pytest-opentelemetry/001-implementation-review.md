---
type: openspec-rpi
title: "Review: adopt-pytest-opentelemetry"
description: pytest-opentelemetry 채택 구현을 검증하고 승인한다.
category: review
status: approved
relatedArtifacts:
  - adopt-pytest-opentelemetry
---

# Review: adopt-pytest-opentelemetry

## Summary

**Approved.** `pytest-opentelemetry==1.1.0`의 provenance와 Python 3.13 실행을 확인했고, CLI, fixture/test/run span payload, xdist 실행을 durable integration tests로 검증했다. 미해결 Blocker와 Major finding은 없다.

## Reconciliation

| Axis | Result | Evidence |
| --- | --- | --- |
| Completeness | Pass | dependency, local hook 제거, docs, tests, spec sync 완료 |
| Correctness | Pass | console exporter span contract와 `-n 2` xdist subprocess tests |
| Coherence | Pass | BREAKING custom attribute 제거와 upstream export semantics가 artifact에 반영됨 |
| Regression | Pass | full suite 113 tests |
| Evidence | Pass | focused/full pytest, Ruff, mypy, rumdl, OpenSpec, lock checks |
| Risk | Pass | exact pin과 public contract tests로 upstream release risk 제한 |

## Findings

| Level | Owner | Finding | Evidence | Required action |
| --- | --- | --- | --- | --- |
| Note | Implement | xdist test는 worker lifecycle과 plugin 실행 성공을 검증하지만 cross-process parent relation payload는 assertion하지 않는다. | `tests/test_pytest_opentelemetry.py` | distributed trace parent relation이 consumer contract가 될 때 collector integration test 추가 |
| Note | Implement | plugin auto-load는 기본 실행에서도 resource detection과 span 생성 overhead가 있다. | plugin source, design risk | 전체 test runtime budget을 초과할 때 opt-in plugin loading 평가 |

## Validation Observed

| Check | Result | Notes |
| --- | --- | --- |
| `uv run pytest -n 0 tests/test_pytest_opentelemetry.py tests/data_platform/test_sql.py` | Pass | 10 passed |
| `uv run pytest` | Pass | 113 passed |
| `uv run ruff format --check ... && uv run ruff check ...` | Pass | 2 files |
| `MYPYPATH=src uv run mypy ...` | Pass | 2 files |
| `uv run rumdl check ...` | Pass | docs와 OpenSpec files |
| `openspec validate adopt-pytest-opentelemetry` | Pass | change valid |
| `uv lock --check` | Pass | 209 packages resolved |

## Amendments

| Amendment | Reflected in OpenSpec? | Review impact |
| --- | --- | --- |
| plugin을 `1.1.0` exact pin | Yes | 검증하지 않은 future release 유입 방지 |
| local custom attributes 제거를 BREAKING으로 명시 | Yes | 동등 교체 오해 해소 |
| export contract를 option과 표준 OTel environment semantics로 수정 | Yes | upstream behavior와 일치 |
| console exporter span regression test 추가 | Yes | 이전 Major finding 해소 |

## Route

| Status | Next action |
| --- | --- |
| approved | OpenSpec archive 후 domain별 commit |
