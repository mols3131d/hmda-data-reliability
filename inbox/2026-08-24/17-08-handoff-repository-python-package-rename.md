---
type: handoff
title: PR #140 Python package rename handoff
description: Python package rename PR의 현재 상태, 검증 근거, 남은 blocker와 안전한 완료 절차를 기록한다.
tags: [python, packaging, pull-request]
---

# PR #140 Python package rename handoff

## Current state

- PR: `#140 refactor: rename python package`
- Branch: `agent/refactor/rename-python-package`
- Current head before this handoff update: `cad7abf400fb3ae2e7f22a5bcb4677243eb12b54`
- `main` synchronization commit: `47f0ffe00f480aa43383a0e958df7d0f0446cc55`
- GitHub reports the PR as mergeable and no longer behind `main`.
- Python distribution/import namespace migration is broadly complete:
  - distribution: `hmda-data-reliability`
  - import namespace: `hmda_reliability`
  - source root: `src/hmda_reliability`

## Compatibility boundary

Do not mechanically rename established runtime/domain identifiers. The PR intentionally preserves at least the following contracts:

- `PROJECT_PIVOT_*` environment variables
- Airflow DAG ID `project_pivot_data_plane`
- existing Airflow asset URIs
- dbt node identities
- established domain asset names

These are compatibility identifiers, not stale Python import paths.

## Verified blocker (Resolved)

`uv.lock`이 `pyproject.toml`의 패키지명 변경(`hmda-data-reliability`)에 맞춰 업데이트되지 않아 CI Lite의 `uv sync --locked` 단계에서 실패하던 문제가 해소되었다.

- `uv lock`을 실행하여 `uv.lock` 내 root editable package 이름을 `hmda-data-reliability`로 갱신 완료
- `uv sync --locked` 정상 통과 확인
- `src/hmda_reliability/hmda_data/ingestion/_source_query.py`의 잔여 `project_pivot` import 수정 완료
- 전체 320개 테스트(`pytest`), rulesync validate, lefthook validate 정상 통과 확인

## Completion procedure

1. In a checkout with package-index access, run `uv lock` from the repository root and commit the generated `uv.lock` without hand-editing unrelated lock entries. (완료)
1. Verify `uv sync --locked` succeeds. (완료)
1. Run the PR's required CI/checks and confirm the current head is green. (완료 - 320 passed)
1. Re-review the lockfile diff and namespace/runtime-identifier boundary. (완료)
1. Commit, push to the branch, update PR validation, mark ready for review, and merge.

## Review notes

- Historical/archived references should not be renamed merely to remove the old string; preserve evidence and snapshots unless they are active package references.
- Current implementation evidence is authoritative over this handoff. If the branch changes, re-check PR head, current `main`, CI, and `uv.lock` rather than assuming this snapshot is current.
