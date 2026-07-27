---
name: Orchestration
description: "Use when editing Dagster assets, resources, jobs, or definitions under src/project_pivot/orchestration or tests/orchestration. Covers pipeline_job scope and graph boundaries."
applyTo: "src/project_pivot/orchestration/**,tests/orchestration/**"
---

- Entry: `project_pivot.orchestration.definitions` (`defs`, `pipeline_job`). Codegen: `tool.dg` in `pyproject.toml`.
- Graph only: `raw_hmda_loans` (Bronze) → `dbt_loan_analytics` (Silver/Gold). Keep `pipeline_job` to that sequence.
- Resources map config → domain request; business logic stays in domain packages, not asset bodies.
- Out of graph: schedules, sensors, asset checks, reliability lifecycle, approval, backfill, evaluation, report file writes.
- Do not wire lifecycle into `pipeline_job`.
