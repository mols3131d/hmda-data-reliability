---
type: openspec-spec-driven-tdd-proposal
category: proposal
title: Migrate data-plane orchestration to Apache Airflow
description: Replace the active Dagster data-plane orchestration surface with Apache Airflow while preserving Data Operations and Reliability ownership.
tags:
  - domain:orchestration
  - capability:orchestration-pipeline
---

## Why

Project Pivot currently exposes the full data-plane workflow through Dagster. The repository has verified that Apache Airflow 3.3.0 can coexist with the current Python 3.13 project dependency graph when Airflow official constraints are used for the Airflow-first installation only and the final project resolution is performed without applying those constraints globally. The orchestration vendor can therefore be changed without redesigning ingestion, dbt execution, artifact promotion or Reliability safety boundaries.

## What Changes

- Replace the active Dagster data-plane orchestration surface with an Apache Airflow data-plane workflow.
- Preserve the ordered raw load → dbt build → artifact promotion behavior owned by Data Operations.
- Preserve task failure, disabled-dbt skip and artifact promotion safety semantics.
- Generalize orchestration-derived Reliability evidence to a vendor-neutral orchestration source.
- Remove active Dagster runtime, configuration and documentation references after the Airflow behavior is verified.

## Boundaries

- **In Scope:** The existing `orchestration-pipeline` capability and its active implementation, tests, configuration and durable documentation; the vendor-specific orchestration value in `reliability-data-contracts`.
- **Out of Scope:** Scheduling, automatic retry, distributed execution, sensors, dynamic task mapping, custom operators/plugins/executors, production metadata deployment, reliability or recovery DAGs, LLMOps task orchestration and domain logic changes.

## Capabilities

### Modified Capabilities

#### `orchestration-pipeline`

- The existing data-plane workflow is provided by Airflow rather than Dagster.
- Existing ordered stage execution, domain delegation, configuration authority, execution evidence and control-plane exclusions remain observable contracts.

#### `reliability-data-contracts`

- Evidence collected from orchestration execution is represented without coupling the contract to Dagster or another specific vendor.
