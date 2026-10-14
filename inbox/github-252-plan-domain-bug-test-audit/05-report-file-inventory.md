---
type: report
title: Domain Source And Test Inventory
description: PR 252의 고정 baseline에서 찾은 도메인별 source/test/spec 파일과 첫 패스 확인 범위입니다.
tags:
  - reliability
  - testing
---

# Seven-Domain File Inventory

**All paths are at `8bc62fa6ec995f2e57456d55712b36ff11b1f1d9`.** `sampled` = 일부 함수와 관련 테스트를 정적으로 확인했으나 전수 검토 전. `pending` = 아직 파일별 의미론 검토 전. 이 목록은 체크리스트의 L1 산출물이며 L2–L8 완료 증거가 아니다.

## reliability

**Source** (path prefix: `src/hmda_reliability/reliability/`)

- [ ] `__init__.py` — pending
- [ ] `contracts/__init__.py` — pending
- [ ] `contracts/approval.py` — sampled
- [ ] `contracts/base.py` — pending
- [ ] `contracts/evidence.py` — pending
- [ ] `contracts/incident.py` — pending
- [ ] `contracts/lineage.py` — pending
- [ ] `contracts/profile.py` — pending
- [ ] `contracts/recovery_proposal.py` — pending
- [ ] `contracts/schema_recovery.py` — sampled
- [ ] `contracts/table_state.py` — pending
- [ ] `contracts/validation.py` — pending
- [ ] `detection/__init__.py` — pending
- [ ] `detection/detector.py` — pending
- [ ] `detection/request.py` — pending
- [ ] `detection/result.py` — pending
- [ ] `detection/thresholds.py` — pending
- [ ] `errors.py` — pending
- [ ] `evaluation/__init__.py` — pending
- [ ] `evaluation/case_result.py` — pending
- [ ] `evaluation/freshness_delay.py` — pending
- [ ] `evaluation/null_spike.py` — pending
- [ ] `evaluation/recovery_case.py` — pending
- [ ] `evaluation/report.py` — pending
- [ ] `evaluation/reporter.py` — pending
- [ ] `evaluation/schema_drift.py` — pending
- [ ] `evaluation/volume_drop.py` — pending
- [ ] `impact/__init__.py` — pending
- [ ] `impact/analyzer.py` — pending
- [ ] `impact/manifest.py` — pending
- [ ] `impact/request.py` — pending
- [ ] `impact/result.py` — pending
- [ ] `metadata/__init__.py` — pending
- [ ] `metadata/builder.py` — pending
- [ ] `metadata/request.py` — pending
- [ ] `profiling/__init__.py` — pending
- [ ] `profiling/profile_snapshot_builder.py` — pending
- [ ] `profiling/profile_snapshot_request.py` — pending
- [ ] `profiling/table_state_builder.py` — pending
- [ ] `quality_gate.py` — pending
- [ ] `recovery/__init__.py` — pending
- [ ] `recovery/executor.py` — sampled
- [ ] `recovery/request.py` — pending
- [ ] `recovery/result.py` — pending
- [ ] `recovery/schema_candidate.py` — sampled
- [ ] `recovery/schema_executor.py` — sampled
- [ ] `recovery/schema_request.py` — sampled
- [ ] `recovery/schema_result.py` — pending
- [ ] `remediation/__init__.py` — pending
- [ ] `remediation/draft.py` — pending
- [ ] `remediation/request.py` — pending
- [ ] `remediation/workflow.py` — pending

**Tests** (path prefix: `tests/reliability/`)

- [ ] `__init__.py` — pending
- [ ] `conftest.py` — pending
- [ ] `contracts/__init__.py` — pending
- [ ] `contracts/test_approval.py` — pending
- [ ] `contracts/test_evidence.py` — pending
- [ ] `contracts/test_incident.py` — pending
- [ ] `contracts/test_lineage.py` — pending
- [ ] `contracts/test_profile.py` — pending
- [ ] `contracts/test_recovery_proposal.py` — pending
- [ ] `contracts/test_schema_recovery.py` — pending
- [ ] `contracts/test_validation.py` — pending
- [ ] `test_approval_backfill_validation.py` — sampled
- [ ] `test_basic_incident_detection.py` — pending
- [ ] `test_evaluation_report.py` — pending
- [ ] `test_fixtures.py` — pending
- [ ] `test_freshness_delay_evaluation.py` — pending
- [ ] `test_impact_analysis.py` — pending
- [ ] `test_null_spike_evaluation.py` — pending
- [ ] `test_profile_snapshots.py` — pending
- [ ] `test_quality_gate.py` — pending
- [ ] `test_recovery_runtime_evidence.py` — pending
- [ ] `test_remediation_draft.py` — pending
- [ ] `test_schema_drift_evaluation.py` — sampled
- [ ] `test_schema_recovery_candidate.py` — sampled
- [ ] `test_schema_recovery_executor.py` — sampled
- [ ] `test_table_metadata_evidence.py` — pending
- [ ] `test_table_state_identity.py` — pending

## data operations

**Source** (path prefix: `src/hmda_reliability/data_operations/`)

- [ ] `__init__.py` — pending
- [ ] `dbt_result.py` — pending
- [ ] `errors.py` — pending
- [ ] `incident_lifecycle.py` — pending
- [ ] `lifecycle_result.py` — pending
- [ ] `quality_gate.py` — sampled
- [ ] `raw_result.py` — pending
- [ ] `request.py` — pending
- [ ] `runner.py` — sampled

**Tests** (path prefix: `tests/data_operations/`)

- [ ] `__init__.py` — pending
- [ ] `test_dbt_runner.py` — sampled
- [ ] `test_incident_lifecycle.py` — pending
- [ ] `test_quality_gate.py` — sampled
- [ ] `test_system_recovery_e2e.py` — pending

## hmda data

**Source** (path prefix: `src/hmda_reliability/hmda_data/`)

- [ ] `__init__.py` — pending
- [ ] `contracts/__init__.py` — pending
- [ ] `eda/__init__.py` — pending
- [ ] `eda/analysis.py` — pending
- [ ] `eda/explorer.py` — pending
- [ ] `errors.py` — pending
- [ ] `ingestion/__init__.py` — pending
- [ ] `ingestion/_common.py` — pending
- [ ] `ingestion/_source_query.py` — pending
- [ ] `ingestion/discovery.py` — pending
- [ ] `ingestion/full_load.py` — pending
- [ ] `ingestion/identity.py` — sampled
- [ ] `ingestion/partition.py` — sampled
- [ ] `synthetic/__init__.py` — pending
- [ ] `synthetic/_source.py` — pending
- [ ] `synthetic/_writer.py` — pending
- [ ] `synthetic/cases.py` — pending

**Tests** (path prefix: `tests/hmda_data/`)

- [ ] `__init__.py` — pending
- [ ] `conftest.py` — pending
- [ ] `eda/test_eda.py` — pending
- [ ] `eda/test_eda_evidence.py` — pending
- [ ] `eda/test_eda_explorer.py` — pending
- [ ] `test_ingestion.py` — pending
- [ ] `test_ingestion_partition.py` — sampled
- [ ] `test_synthetic.py` — sampled

## data platform

**Source** (path prefix: `src/hmda_reliability/data_platform/`)

- [ ] `__init__.py` — pending
- [ ] `artifacts.py` — sampled
- [ ] `duckdb.py` — sampled
- [ ] `sql.py` — pending

**Tests** (path prefix: `tests/data_platform/`)

- [ ] `__init__.py` — pending
- [ ] `test_artifacts.py` — sampled
- [ ] `test_duckdb.py` — sampled
- [ ] `test_sql.py` — pending
- [ ] `tests/dbt/test_analytics_foundation.py` — pending (별도 test root; 위 prefix 적용 제외)

## review ai

**Source** (path prefix: `src/hmda_reliability/review_ai/`)

- [ ] `__init__.py` — pending
- [ ] `context.py` — pending
- [ ] `contracts.py` — pending
- [ ] `evaluation/__init__.py` — pending
- [ ] `evaluation/langfuse.py` — sampled
- [ ] `evaluation/value.py` — pending
- [ ] `evidence.py` — sampled
- [ ] `prompt.py` — pending
- [ ] `service.py` — sampled
- [ ] `settings.py` — pending
- [ ] `store.py` — pending
- [ ] `validator.py` — sampled

**Tests** (path prefix: `tests/review_ai/`)

- [ ] `__init__.py` — pending
- [ ] `conftest.py` — pending
- [ ] `evaluation/test_langfuse_projection.py` — pending
- [ ] `evaluation/test_utility_evaluation.py` — pending
- [ ] `test_context.py` — pending
- [ ] `test_contracts.py` — pending
- [ ] `test_dependency_boundaries.py` — pending
- [ ] `test_evidence_store.py` — pending
- [ ] `test_live_harness.py` — pending
- [ ] `test_prompt_provider.py` — pending
- [ ] `test_public_surface.py` — pending
- [ ] `test_service.py` — sampled
- [ ] `test_settings.py` — pending
- [ ] `test_validator.py` — sampled

## runtime ai

**Source** (path prefix: `src/hmda_reliability/runtime_ai/`)

- [ ] `__init__.py` — pending
- [ ] `contracts.py` — pending
- [ ] `provider.py` — sampled
- [ ] `settings.py` — sampled

**Tests** (path prefix: `tests/runtime_ai/`)

- [ ] `__init__.py` — pending
- [ ] `test_provider.py` — sampled
- [ ] `test_settings.py` — pending

## orchestration

**Source** (path prefix: `src/hmda_reliability/orchestration/`)

- [ ] `__init__.py` — pending
- [ ] `config.py` — sampled
- [ ] `dags/__init__.py` — pending
- [ ] `dags/hmda_data_plane.py` — sampled

**Tests** (path prefix: `tests/orchestration/`)

- [ ] `__init__.py` — pending
- [ ] `test_airflow_dag.py` — sampled
- [ ] `test_airflow_dagrun.py` — pending
- [ ] `test_airflow_execution.py` — sampled
- [ ] `test_config.py` — sampled

## Normative Spec Inventory (unique: 18)

- [ ] `data-operations-incident-lifecycle/spec.md` — pending
- [ ] `data-operations-stage-execution/spec.md` — sampled
- [ ] `data-platform-dbt-analytics/spec.md` — pending
- [ ] `data-platform-duckdb-access/spec.md` — pending
- [ ] `hmda-data-eda-descriptive-evidence/spec.md` — pending
- [ ] `hmda-data-ingestion/spec.md` — pending
- [ ] `hmda-data-synthetic-defects/spec.md` — pending
- [ ] `orchestration-pipeline/spec.md` — sampled
- [ ] `reliability-agentic-review/spec.md` — pending
- [ ] `reliability-data-contracts/spec.md` — pending
- [ ] `reliability-evaluation-report/spec.md` — pending
- [ ] `reliability-evidence-table-metadata/spec.md` — pending
- [ ] `reliability-impact-analysis/spec.md` — pending
- [ ] `reliability-incident-detection/spec.md` — pending
- [ ] `reliability-profile-snapshots/spec.md` — pending
- [ ] `reliability-recovery-backfill/spec.md` — sampled
- [ ] `reliability-remediation-draft/spec.md` — pending
- [ ] `reliability-schema-recovery/spec.md` — sampled

## Self-Review

Inventory comes from complete Git tree (1,134 items, `truncated=false`), not filename guesses. All `__init__.py`, domain `conftest.py`, shared dbt test are retained. Data Platform의 dbt test는 별도 경로이므로 prefix 규칙에서 예외로 표기했다. No item is `reviewed` or `excluded` yet; the first-pass report never claimed file-by-file deep review. No tests were run. Domain-level completion stays pending.
