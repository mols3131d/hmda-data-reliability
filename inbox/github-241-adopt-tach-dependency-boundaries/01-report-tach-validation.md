---
type: report
title: "Tach Dependency Boundary Validation"
description: "PR #241 Tach 구현 범위, negative-path proof와 실행한 검증을 기록합니다."
tags:
  - python
  - tooling
  - architecture
---

# Tach Dependency Boundary Validation

## Result

PR #241의 계획을 구현했다. Tach 0.35.1은 Python 3.13에서 runtime import의 네 AI 금지 방향을 검사한다. 기존 AST guard는 type-only import까지 계속 검사한다.

## Decisions

- `src` source root, package root module과 현재 10개 top-level package를 선언했다. `root_module = "forbid"`, 빈 exclude, Git ignore 미적용으로 source 누락을 제한한다.
- `cannot_depend_on`만 사용한다. Full import allowlist와 global no-cycle policy는 도입하지 않았다.
- `architecture` CI selector는 Tach configuration 단독 변경에서도 Python/uv setup, locked sync와 boundary 검증을 실행한다. Local hook은 변경하지 않았다.
- `uv add --dev 'tach>=0.35.1'`로 lockfile을 생성했다. 기존 package version은 변경하지 않고 Tach와 필요한 dependency만 추가했다.
- Docs index generator가 기존 ai-agent README metadata의 `Subagent` 항목 누락도 함께 교정했다.

## Validation

Local environment: CPython 3.13.13, uv 0.12.5, Tach 0.35.1. 아래 결과는 이 report를 포함한 구현 변경에서 실행했다. Remote CI 결과는 PR check를 기준으로 확인한다.

| Check | Result |
| --- | --- |
| `uv run --no-sync tach check` | Pass |
| `tests/scripts/test_ci_classifier.py` | 62 passed |
| `tests/scripts/test_tach.py`, `tests/review_ai/test_dependency_boundaries.py` | 9 passed |
| `uv run --no-sync pytest -q -p no:sugar --tb=short -n 4 -m 'unit and not memory and not stress'` | 299 passed |
| `tests/dbt/test_analytics_foundation.py`, `tests/orchestration/test_airflow_dag.py` | 5 passed |
| `uv lock --check`, wheel build, `ty check` | Pass |
| Changed Python Ruff check and format check | Pass |
| Changed TOML Tombi format and lint | Pass |
| Changed Markdown rumdl check and docs index check | Pass |

Negative-path regression은 source copy를 temporary project에 만들고 실제 Tach CLI를 실행한다. `reliability`에서 `review_ai/runtime_ai`로, `runtime_ai`에서 `review_ai/reliability`로의 runtime import는 각각 nonzero exit와 해당 import diagnostic을 확인한다. Type-only import, 허용된 advisory/root import는 통과하고 implicit root 참조는 실패한다.

## Integration Finding

PR #242의 OpenSpec archive 이후 기존 classifier test 3개가 실제 `orchestration-quality-gate`를 active로 가정해 실패함을 재현했다. Active pairing 검증에 temporary directory fixture를 사용해 production classifier와 기대 계약은 유지하고 archive lifecycle 의존을 제거했다.

## Boundary

Application source, architecture contract와 approval/recovery authority는 변경하지 않았다. Ready 전환, 승인과 merge는 수행하지 않는다.
