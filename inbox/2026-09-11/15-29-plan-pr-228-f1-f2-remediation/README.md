---
type: plan
title: PR #228 F1/F2 Remediation Plan
description: orchestration-pipeline의 cross-domain executable routing과 최신 main 기준 prospective-merge evidence를 갱신하는 실행 계획이다.
tags:
  - ci
  - openspec
  - pr-228
  - review-remediation
---

# PR #228 F1/F2 Remediation Plan

## Target

- Pull Request: [#228](https://github.com/mols3131d/hmda-data-reliability/pull/228)
- Remote head before work: `4bca22830f2ad0693c5d3b9d2079a0b8e612683c`
- Latest base incorporated locally: `origin/main=6ef4e642f1cbe477ff1a1967f514649d2aae4772`
- Worktree: `task-228-progress`
- Branch: `agent/ci/openspec-and-dependency-admission`

## Goal

F1의 contract owner test surface를 canonical `orchestration-pipeline` Spec admission에 연결하고, 최신 `main`과 결합된 PR candidate의 CI evidence를 확보한다.

## Scope

- `.github/workflows/classify_changes.sh`의 `orchestration-pipeline` target mapping
- `tests/test_ci_classifier.py`의 canonical Spec regression
- 최신 `origin/main` merge commit을 포함한 PR branch update
- focused test, OpenSpec, dependency/runtime smoke, Python validation과 remote CI evidence
- Work/Review/Finalize Inbox artifacts

### Out of Scope

- application/domain implementation 또는 canonical Spec 내용 변경
- `--all --strict` coupling redesign
- PR approval, Ready 전환 또는 merge
- unrelated stale Inbox artifact 정리

## Acceptance

- `openspec/specs/orchestration-pipeline/spec.md` 입력 시 classifier target이 정확히 다음 네 개를 출력한다.
  - `tests/orchestration`
  - `tests/data_operations/test_quality_gate.py`
  - `tests/data_operations/test_dbt_runner.py`
  - `tests/reliability/test_quality_gate.py`
- `openspec_bulk=false`, `full_tests=false`를 유지한다.
- 기존 direct active Change pairing인 `orchestration-quality-gate`를 유지한다.
- classifier regression과 exact 74-test focused selection이 통과한다.
- latest `main=6ef4e64`를 포함한 pushed PR candidate의 prospective-merge CI가 성공한다.
- PR body와 Inbox Work/Review 기록이 실제 head와 validation evidence를 반영한다.

## Execution Order

1. Research — 최신 remote revision/base와 F1/F2 evidence, target collection을 고정한다.
1. Plan — exact-file scope와 acceptance를 고정한다.
1. Work — red regression을 먼저 갱신하고 classifier mapping을 수정한 뒤 focused validation을 실행한다.
1. Review — diff, selector contract, test evidence와 remote CI를 독립 관점으로 challenge한다.
1. Finalize — PR description/evidence를 갱신하고 human review handoff 상태를 확정한다.

## Validation Commands

```bash
uv run --no-sync pytest tests/test_ci_classifier.py -q -rs
uv run --no-sync pytest tests/orchestration tests/data_operations/test_quality_gate.py tests/data_operations/test_dbt_runner.py tests/reliability/test_quality_gate.py -q -rs
uv run --no-sync pytest tests/dbt/test_analytics_foundation.py tests/orchestration/test_airflow_dag.py -q -rs
npm exec --yes --package @fission-ai/openspec@1.12.0 -- openspec validate --all --strict
uv lock --check
uv build --wheel --out-dir /tmp/pr228-dist
```
