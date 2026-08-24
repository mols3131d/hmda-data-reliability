---
paths:
  - src/project_pivot/orchestration/**
  - tests/orchestration/**
---

- Entry: `project_pivot.orchestration.dags.project_pivot_data_plane` (`project_pivot_data_plane`). Use the `airflow.sdk` public authoring surface.
- Graph only: `load_raw_hmda_loans` (Bronze) → `build_dbt_loan_analytics` (Silver/Gold). Keep one DAG, `schedule=None`, `catchup=False`, `max_active_runs=1` and task `retries=0`.
- Runtime config maps only supported trigger values to `DataOperationRequest`; business logic stays in Data Operations and Reliability packages.
- Use logical `Asset` outlets for update evidence. Do not transport domain requests/results, DataFrames or Arrow tables through task payloads.
- Out of graph: schedules, automatic retry, sensors, dynamic mapping, distributed executor, custom operator/plugin, reliability lifecycle, approval, backfill, evaluation, LLMOps and report file writes.
- Do not wire lifecycle or recovery into `project_pivot_data_plane`.
