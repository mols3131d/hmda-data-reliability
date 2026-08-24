---
type: handoff
title: PR #140 Python package rename handoff
description: Python package rename PR의 현재 상태, 검증 근거, 남은 routing blocker와 merge 전 완료 절차를 기록한다.
tags: [python, packaging, pull-request, routing]
---

# PR #140 Python package rename handoff

## Current state

- PR: `#140 refactor: rename python package`
- Branch: `agent/refactor/rename-python-package`
- Reviewed head: `d1fc52c651bb94a28b72c5cd38710f7cdb8db762`
- Current `main`: `3053863f8d6178f84a53c1d6804d527c138b4e66`
- The branch is currently one commit behind `main`.
- GitHub reports the PR as mergeable and the PR is ready for review.
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

## Resolved blockers

The earlier package-lock and residual-import blockers are resolved.

- `uv.lock` now records the root editable package as `hmda-data-reliability`.
- `uv sync --locked` succeeds.
- `src/hmda_reliability/hmda_data/ingestion/_source_query.py` no longer imports `project_pivot`.
- Agent skill references reviewed in the latest commits use the renamed package path.
- `CI Lite #166` completed successfully on PR head `d1fc52c` using prospective merge commit `22a3dc92746a53ba5ccbc8fc8056a01fdf92e24e`.
- That CI run successfully completed locked dependency sync, Rulesync validation, and selected tests. The log shows 75 unit tests and 317 selected tests passing in its two pytest invocations.
- Generated chatbot route indexes (`.agents/route/rules.jsonl`, `.agents/route/skills.jsonl`) were regenerated via `scripts/generate_agent_routes.py` and validated with `scripts/generate_agent_routes.py --check`. All active rules now correctly target `src/hmda_reliability/**`.

## Completion procedure

1. Integrate current `main` into `agent/refactor/rename-python-package` without rewriting public history. (완료)
1. Run `python scripts/generate_agent_routes.py`. (완료)
1. Run `python scripts/generate_agent_routes.py --check` and confirm it exits successfully. (완료)
1. Verify `.agents/route/rules.jsonl` contains the `src/hmda_reliability/**` selectors and no active `src/project_pivot/**` selectors for Project, Reliability, or Orchestration routing. (완료)
1. Re-run the PR CI on the new head and verify locked sync, Rulesync validation, and tests remain green. (진행 중)
1. Re-review the compatibility boundary and generated routing diff. (완료)
1. Update the PR validation text with current evidence and squash-merge only after the routing blocker is resolved.

## Review notes

- `scripts/generate_agent_routes.py` treats `.agents/route/*.jsonl` as derived routing metadata; regenerate them from the canonical sources rather than hand-editing the JSONL.
- Historical/archived references should not be renamed merely to remove the old string; preserve evidence and snapshots unless they are active package or routing references.
- Current implementation and repository state are authoritative over this handoff. Re-check PR head, current `main`, CI, and generated route indexes if the branch changes.
