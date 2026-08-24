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

## Verified blocker

`uv.lock` is stale relative to `pyproject.toml`.

The root editable package entry still uses:

```toml
[[package]]
name = "project-pivot"
version = "0.1.0"
source = { editable = "." }
```

while `pyproject.toml` now declares `hmda-data-reliability`.

`CI Lite #145` on head `cad7abf` failed at `Sync dependencies`. The runner used `uv 0.11.32`; `uv sync --locked` resolved 210 packages and then rejected the stale lockfile because it needs to be updated. This is a merge blocker; do not remove or weaken `--locked` to bypass it.

## Completion procedure

1. In a checkout with package-index access, run `uv lock` from the repository root and commit the generated `uv.lock` without hand-editing unrelated lock entries.
1. Verify `uv sync --locked` succeeds.
1. Run the PR's required CI/checks and confirm the current head is green.
1. Re-review the lockfile diff and namespace/runtime-identifier boundary.
1. Update the PR Validation section with actual evidence, mark the Draft PR ready, and squash-merge only after required checks are complete.

## Review notes

- Historical/archived references should not be renamed merely to remove the old string; preserve evidence and snapshots unless they are active package references.
- Current implementation evidence is authoritative over this handoff. If the branch changes, re-check PR head, current `main`, CI, and `uv.lock` rather than assuming this snapshot is current.
