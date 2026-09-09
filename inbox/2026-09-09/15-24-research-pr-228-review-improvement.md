---
type: research
title: PR #228 Review Improvement Research
description: PR #228의 현재 보강 head를 Inbox review와 repository CI contract에 대조해 남은 개선 범위와 검증 기준을 정리한다.
tags:
  - ci
  - openspec
  - pr-228
  - review-improvement
---

# PR #228 Review Improvement Research

> [!NOTE]
> PR #228의 `f7b8ee8`은 원 review의 F1 executable test routing, F2 dependency runtime smoke와 F3 affected OpenSpec validation을 대부분 반영했다. 다만 canonical `openspec/specs/<capability>/**` 변경이 그 capability를 직접 수정하는 active Change까지 OpenSpec validation에 포함하는지는 보강되지 않아, 이 범위를 fail-safe하게 닫는 것이 이번 loop의 최소 개선이다.

## Question

PR #228의 Inbox review가 제기한 admission gap이 현재 `f7b8ee8`에서 실제로 닫혔는지 확인하고, 남은 material gap만 개선 branch에서 재현·보강할 수 있는가?

## Scope

- PR [#228](https://github.com/mols3131d/hmda-data-reliability/pull/228)의 reviewed change와 current head `f7b8ee808e416519c596f0767e1e30d5283c4bcd`
- 기존 Inbox review `inbox/2026-09-09/11-26-review-ci-admission-pr-228.md`의 F1–F4
- `.github/workflows/classify_changes.sh`, `.github/workflows/ci-lite.yml`, `tests/test_ci_classifier.py`, `lefthook.yml`
- `docs/development/ci.md`, `docs/development/testing.md`, `docs/development/test-design.md`의 admission·test contract

## Findings

### Current review findings are mostly implemented

`f7b8ee8`은 known canonical Spec를 `tests/<domain>` executable target으로 연결하고, unknown/config/schema scope는 `openspec_bulk=true`와 full test fallback으로 넓힌다. `.python-version`, `pyproject.toml`, `uv.lock` 변경에는 `runtime_smoke=true`를 설정해 dbt/DuckDB integration과 Airflow DAG contract를 별도 실행한다. current PR body도 head와 validation evidence에 맞게 갱신되어 F4는 해소된 상태다.

#### Evidence

- `uv run --no-sync pytest tests/test_ci_classifier.py -q -rs` — `46 passed`
- `uv run --no-sync pytest tests/dbt/test_analytics_foundation.py tests/orchestration/test_airflow_dag.py -q -rs` — `5 passed`
- `npm exec --yes --package @fission-ai/openspec@1.12.0 -- openspec validate --all --strict` — `20 passed, 0 failed`
- `uv lock --check` — pass
- `uv build --wheel --out-dir /tmp/pr228-dist` — pass; current uv version warning만 관찰

### Canonical Spec and direct active Change are not paired

현재 classifier는 `openspec/specs/<capability>/**` 변경을 해당 Spec target으로만 변환한다. 하지만 active Change가 `openspec/changes/<change>/specs/<capability>/spec.md`에서 같은 capability의 delta를 소유할 수 있으므로, canonical Spec 변경 시 해당 active Change도 `openspec validate <change> --type change --strict`로 함께 확인해야 한다. 이 관계를 놓치면 Spec과 active delta의 구조적 정합성 검증이 서로 다른 scope로 분리된다.

#### Evidence

- `openspec/specs/orchestration-pipeline/spec.md`
- `openspec/changes/orchestration-quality-gate/specs/orchestration-pipeline/spec.md`
- `openspec/specs/hmda-data-synthetic-defects/spec.md`
- `openspec/changes/reliability-synthetic-2026-evaluation/specs/hmda-data-synthetic-defects/spec.md`
- `f7b8ee8:.github/workflows/classify_changes.sh`는 `openspec_spec_targets`와 `openspec_change_targets`를 별도로 수집하지만 canonical Spec branch에서 related active Change를 탐색하지 않는다.

## Decision

known canonical capability를 선택한 뒤 `openspec/changes/*/specs/<capability>/`를 탐색해 직접 연결된 active Change를 추가한다. 이름·directory state를 안전하게 판정할 수 없으면 기존 `openspec_bulk=true` fallback을 유지한다. 기존 unknown/config/archive routing과 dependency runtime smoke contract는 보존하고, mixed Spec/Change 입력과 direct pairing regression을 추가한다.

## Limits

- `actionlint`, `shellcheck`, `yamllint`는 local environment에 없어 직접 실행하지 못한다.
- 이 artifact는 PR #228의 `f7b8ee8` current head를 기준으로 한 개선 계획이며, Inbox는 canonical CI contract를 대체하지 않는다.
