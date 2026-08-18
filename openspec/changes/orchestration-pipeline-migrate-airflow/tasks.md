---
type: openspec-spec-driven-tdd-tasks
category: tasks
title: Implement Apache Airflow data-plane orchestration migration
description: Implement the Airflow thin adapter, preserve domain and evidence boundaries, remove active Dagster and validate the resulting runtime.
tasks_completed: 7
tasks_total: 7
---

## Tasks

- [x] Add the validated Airflow dependency graph to the project
  - **Done when:** `apache-airflow==3.3.0` is declared, `uv.lock` resolves without applying Airflow constraints globally, the shared graph retains `dbt-core==1.12.0` and `dbt-duckdb==1.10.1`, and `uv sync --locked` plus `uv pip check` succeed.

- [x] Extract the framework-independent runtime configuration adapter
  - **Covers:** `orchestration-pipeline` configuration boundary scenarios.
  - **Test first:** Fix explicit > environment > default precedence, invalid-environment masking, invalid explicit year, empty path and empty `source_file` observations in Airflow-independent unit tests.
  - **Done when:** `data_operation_request_from_runtime()` returns a validated `DataOperationRequest` for the supported overrides and the focused configuration tests pass without importing Airflow.

- [x] Implement the Airflow data-plane DAG structure
  - **Covers:** `orchestration-pipeline` workflow graph, single owner, control-plane exclusion and task data boundary scenarios.
  - **Test first:** Fix one DAG, two task IDs, one raw → analytics dependency, no schedule, no catchup, one active run, zero retries, logical asset outlets and no domain result transport at the parse boundary.
  - **Done when:** the DAG imports without parse-time I/O and Airflow structure tests pass using the `airflow.sdk` public authoring surface.

- [x] Implement and test raw, analytics, failure and skip execution semantics
  - **Covers:** ordered stage execution, execution/data-update evidence and disabled analytics requirements.
  - **Test first:** Fix normal execution, raw failure, dbt-disabled skip, dbt build failure, promotion failure and invalid request outcomes with independent task-state and asset-evidence assertions.
  - **Done when:** tasks call only the Data Operations public APIs; successful promotion is required for analytics update evidence; raw failure prevents analytics execution; disabled dbt is `SKIPPED`; and focused orchestration execution tests pass.

- [x] Decouple Reliability evidence from orchestration vendors
  - **Covers:** `reliability-data-contracts` Evidence contract.
  - **Test first:** Fix serialization and validation for `EvidenceSource.ORCHESTRATION`, and reject vendor-specific `DAGSTER`/`AIRFLOW` values.
  - **Done when:** the public Reliability contract, related tests and canonical delta spec use `ORCHESTRATION` without changing lifecycle, approval, recovery or evaluation behavior.

- [x] Remove the active Dagster runtime and replace its tests and configuration
  - **Covers:** single pipeline owner and active cleanup boundary.
  - **Done when:** direct Dagster dependencies, `[tool.dg]` configuration, Dagster definitions/assets/resources, Dagster-only tests and active Dagster imports are removed or replaced; the lock no longer contains stale Dagster packages required only by the removed runtime.

- [x] Align active documentation and complete Airflow runtime validation
  - **Covers:** all modified orchestration and Reliability requirements.
  - **Done when:** active README, development, architecture, domain, agent-rule and canonical Spec references describe Airflow; a local SQLite Airflow DB bootstrap succeeds; DAG parsing, import/version checks, `dbt --version`, project import, pytest collection, focused orchestration tests and the active-surface vendor scan pass or are explicitly classified.
