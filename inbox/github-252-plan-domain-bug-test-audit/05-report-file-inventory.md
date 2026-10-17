---
type: report
title: Domain Source And Test Inventory
description: PR 252의 고정 baseline에서 찾은 도메인별 source/test/spec 파일과 첫 패스 확인 범위입니다.
tags:
  - reliability
  - testing
---

# Seven-Domain File Inventory

**Baseline:** `8bc62fa6ec995f2e57456d55712b36ff11b1f1d9`. PR head `b9f9c7657f1d65e5b583ed16afd035ec218e1ed6`의 domain code/spec와 동일하다. `reviewed (static, quality)`는 Quality specialist가 파일 전체를 읽고 관련 계약·테스트와 대조했음을 뜻한다. 102 source + 67 test + 18 spec = 187 reviewed, excluded 0. 두 reviewer 모두 모든 파일을 중복 전수 검토했다는 의미가 아니며, 실행 성공을 뜻하지도 않는다. 실행 결과는 [Cloud validation](08-report-cloud-validation.md), 독립 리뷰는 [Final review](09-review-cloud-audit.md)를 본다.

## reliability

**Source** (path prefix: `src/hmda_reliability/reliability/`)

- [x] `__init__.py` — reviewed (static, quality)
- [x] `contracts/__init__.py` — reviewed (static, quality)
- [x] `contracts/approval.py` — reviewed (static, quality)
- [x] `contracts/base.py` — reviewed (static, quality)
- [x] `contracts/evidence.py` — reviewed (static, quality)
- [x] `contracts/incident.py` — reviewed (static, quality)
- [x] `contracts/lineage.py` — reviewed (static, quality)
- [x] `contracts/profile.py` — reviewed (static, quality)
- [x] `contracts/recovery_proposal.py` — reviewed (static, quality)
- [x] `contracts/schema_recovery.py` — reviewed (static, quality)
- [x] `contracts/table_state.py` — reviewed (static, quality)
- [x] `contracts/validation.py` — reviewed (static, quality)
- [x] `detection/__init__.py` — reviewed (static, quality)
- [x] `detection/detector.py` — reviewed (static, quality)
- [x] `detection/request.py` — reviewed (static, quality)
- [x] `detection/result.py` — reviewed (static, quality)
- [x] `detection/thresholds.py` — reviewed (static, quality)
- [x] `errors.py` — reviewed (static, quality)
- [x] `evaluation/__init__.py` — reviewed (static, quality)
- [x] `evaluation/case_result.py` — reviewed (static, quality)
- [x] `evaluation/freshness_delay.py` — reviewed (static, quality)
- [x] `evaluation/null_spike.py` — reviewed (static, quality)
- [x] `evaluation/recovery_case.py` — reviewed (static, quality)
- [x] `evaluation/report.py` — reviewed (static, quality)
- [x] `evaluation/reporter.py` — reviewed (static, quality)
- [x] `evaluation/schema_drift.py` — reviewed (static, quality)
- [x] `evaluation/volume_drop.py` — reviewed (static, quality)
- [x] `impact/__init__.py` — reviewed (static, quality)
- [x] `impact/analyzer.py` — reviewed (static, quality)
- [x] `impact/manifest.py` — reviewed (static, quality)
- [x] `impact/request.py` — reviewed (static, quality)
- [x] `impact/result.py` — reviewed (static, quality)
- [x] `metadata/__init__.py` — reviewed (static, quality)
- [x] `metadata/builder.py` — reviewed (static, quality)
- [x] `metadata/request.py` — reviewed (static, quality)
- [x] `profiling/__init__.py` — reviewed (static, quality)
- [x] `profiling/profile_snapshot_builder.py` — reviewed (static, quality)
- [x] `profiling/profile_snapshot_request.py` — reviewed (static, quality)
- [x] `profiling/table_state_builder.py` — reviewed (static, quality)
- [x] `quality_gate.py` — reviewed (static, quality)
- [x] `recovery/__init__.py` — reviewed (static, quality)
- [x] `recovery/executor.py` — reviewed (static, quality)
- [x] `recovery/request.py` — reviewed (static, quality)
- [x] `recovery/result.py` — reviewed (static, quality)
- [x] `recovery/schema_candidate.py` — reviewed (static, quality)
- [x] `recovery/schema_executor.py` — reviewed (static, quality)
- [x] `recovery/schema_request.py` — reviewed (static, quality)
- [x] `recovery/schema_result.py` — reviewed (static, quality)
- [x] `remediation/__init__.py` — reviewed (static, quality)
- [x] `remediation/draft.py` — reviewed (static, quality)
- [x] `remediation/request.py` — reviewed (static, quality)
- [x] `remediation/workflow.py` — reviewed (static, quality)

**Tests** (path prefix: `tests/reliability/`)

- [x] `__init__.py` — reviewed (static, quality)
- [x] `conftest.py` — reviewed (static, quality)
- [x] `contracts/__init__.py` — reviewed (static, quality)
- [x] `contracts/test_approval.py` — reviewed (static, quality)
- [x] `contracts/test_evidence.py` — reviewed (static, quality)
- [x] `contracts/test_incident.py` — reviewed (static, quality)
- [x] `contracts/test_lineage.py` — reviewed (static, quality)
- [x] `contracts/test_profile.py` — reviewed (static, quality)
- [x] `contracts/test_recovery_proposal.py` — reviewed (static, quality)
- [x] `contracts/test_schema_recovery.py` — reviewed (static, quality)
- [x] `contracts/test_validation.py` — reviewed (static, quality)
- [x] `test_approval_backfill_validation.py` — reviewed (static, quality)
- [x] `test_basic_incident_detection.py` — reviewed (static, quality)
- [x] `test_evaluation_report.py` — reviewed (static, quality)
- [x] `test_fixtures.py` — reviewed (static, quality)
- [x] `test_freshness_delay_evaluation.py` — reviewed (static, quality)
- [x] `test_impact_analysis.py` — reviewed (static, quality)
- [x] `test_null_spike_evaluation.py` — reviewed (static, quality)
- [x] `test_profile_snapshots.py` — reviewed (static, quality)
- [x] `test_quality_gate.py` — reviewed (static, quality)
- [x] `test_recovery_runtime_evidence.py` — reviewed (static, quality)
- [x] `test_remediation_draft.py` — reviewed (static, quality)
- [x] `test_schema_drift_evaluation.py` — reviewed (static, quality)
- [x] `test_schema_recovery_candidate.py` — reviewed (static, quality)
- [x] `test_schema_recovery_executor.py` — reviewed (static, quality)
- [x] `test_table_metadata_evidence.py` — reviewed (static, quality)
- [x] `test_table_state_identity.py` — reviewed (static, quality)

## data operations

**Source** (path prefix: `src/hmda_reliability/data_operations/`)

- [x] `__init__.py` — reviewed (static, quality)
- [x] `dbt_result.py` — reviewed (static, quality)
- [x] `errors.py` — reviewed (static, quality)
- [x] `incident_lifecycle.py` — reviewed (static, quality)
- [x] `lifecycle_result.py` — reviewed (static, quality)
- [x] `quality_gate.py` — reviewed (static, quality)
- [x] `raw_result.py` — reviewed (static, quality)
- [x] `request.py` — reviewed (static, quality)
- [x] `runner.py` — reviewed (static, quality)

**Tests** (path prefix: `tests/data_operations/`)

- [x] `__init__.py` — reviewed (static, quality)
- [x] `test_dbt_runner.py` — reviewed (static, quality)
- [x] `test_incident_lifecycle.py` — reviewed (static, quality)
- [x] `test_quality_gate.py` — reviewed (static, quality)
- [x] `test_system_recovery_e2e.py` — reviewed (static, quality)

## hmda data

**Source** (path prefix: `src/hmda_reliability/hmda_data/`)

- [x] `__init__.py` — reviewed (static, quality)
- [x] `contracts/__init__.py` — reviewed (static, quality)
- [x] `eda/__init__.py` — reviewed (static, quality)
- [x] `eda/analysis.py` — reviewed (static, quality)
- [x] `eda/explorer.py` — reviewed (static, quality)
- [x] `errors.py` — reviewed (static, quality)
- [x] `ingestion/__init__.py` — reviewed (static, quality)
- [x] `ingestion/_common.py` — reviewed (static, quality)
- [x] `ingestion/_source_query.py` — reviewed (static, quality)
- [x] `ingestion/discovery.py` — reviewed (static, quality)
- [x] `ingestion/full_load.py` — reviewed (static, quality)
- [x] `ingestion/identity.py` — reviewed (static, quality)
- [x] `ingestion/partition.py` — reviewed (static, quality)
- [x] `synthetic/__init__.py` — reviewed (static, quality)
- [x] `synthetic/_source.py` — reviewed (static, quality)
- [x] `synthetic/_writer.py` — reviewed (static, quality)
- [x] `synthetic/cases.py` — reviewed (static, quality)

**Tests** (path prefix: `tests/hmda_data/`)

- [x] `__init__.py` — reviewed (static, quality)
- [x] `conftest.py` — reviewed (static, quality)
- [x] `eda/test_eda.py` — reviewed (static, quality)
- [x] `eda/test_eda_evidence.py` — reviewed (static, quality)
- [x] `eda/test_eda_explorer.py` — reviewed (static, quality)
- [x] `test_ingestion.py` — reviewed (static, quality)
- [x] `test_ingestion_partition.py` — reviewed (static, quality)
- [x] `test_synthetic.py` — reviewed (static, quality)

## data platform

**Source** (path prefix: `src/hmda_reliability/data_platform/`)

- [x] `__init__.py` — reviewed (static, quality)
- [x] `artifacts.py` — reviewed (static, quality)
- [x] `duckdb.py` — reviewed (static, quality)
- [x] `sql.py` — reviewed (static, quality)

**Tests** (path prefix: `tests/data_platform/`)

- [x] `__init__.py` — reviewed (static, quality)
- [x] `test_artifacts.py` — reviewed (static, quality)
- [x] `test_duckdb.py` — reviewed (static, quality)
- [x] `test_sql.py` — reviewed (static, quality)
- [x] `tests/dbt/test_analytics_foundation.py` — reviewed (static, quality) (별도 test root; 위 prefix 적용 제외)

## review ai

**Source** (path prefix: `src/hmda_reliability/review_ai/`)

- [x] `__init__.py` — reviewed (static, quality)
- [x] `context.py` — reviewed (static, quality)
- [x] `contracts.py` — reviewed (static, quality)
- [x] `evaluation/__init__.py` — reviewed (static, quality)
- [x] `evaluation/langfuse.py` — reviewed (static, quality)
- [x] `evaluation/value.py` — reviewed (static, quality)
- [x] `evidence.py` — reviewed (static, quality)
- [x] `prompt.py` — reviewed (static, quality)
- [x] `service.py` — reviewed (static, quality)
- [x] `settings.py` — reviewed (static, quality)
- [x] `store.py` — reviewed (static, quality)
- [x] `validator.py` — reviewed (static, quality)

**Tests** (path prefix: `tests/review_ai/`)

- [x] `__init__.py` — reviewed (static, quality)
- [x] `conftest.py` — reviewed (static, quality)
- [x] `evaluation/test_langfuse_projection.py` — reviewed (static, quality)
- [x] `evaluation/test_utility_evaluation.py` — reviewed (static, quality)
- [x] `test_context.py` — reviewed (static, quality)
- [x] `test_contracts.py` — reviewed (static, quality)
- [x] `test_dependency_boundaries.py` — reviewed (static, quality)
- [x] `test_evidence_store.py` — reviewed (static, quality)
- [x] `test_live_harness.py` — reviewed (static, quality)
- [x] `test_prompt_provider.py` — reviewed (static, quality)
- [x] `test_public_surface.py` — reviewed (static, quality)
- [x] `test_service.py` — reviewed (static, quality)
- [x] `test_settings.py` — reviewed (static, quality)
- [x] `test_validator.py` — reviewed (static, quality)

## runtime ai

**Source** (path prefix: `src/hmda_reliability/runtime_ai/`)

- [x] `__init__.py` — reviewed (static, quality)
- [x] `contracts.py` — reviewed (static, quality)
- [x] `provider.py` — reviewed (static, quality)
- [x] `settings.py` — reviewed (static, quality)

**Tests** (path prefix: `tests/runtime_ai/`)

- [x] `__init__.py` — reviewed (static, quality)
- [x] `test_provider.py` — reviewed (static, quality)
- [x] `test_settings.py` — reviewed (static, quality)

## orchestration

**Source** (path prefix: `src/hmda_reliability/orchestration/`)

- [x] `__init__.py` — reviewed (static, quality)
- [x] `config.py` — reviewed (static, quality)
- [x] `dags/__init__.py` — reviewed (static, quality)
- [x] `dags/hmda_data_plane.py` — reviewed (static, quality)

**Tests** (path prefix: `tests/orchestration/`)

- [x] `__init__.py` — reviewed (static, quality)
- [x] `test_airflow_dag.py` — reviewed (static, quality)
- [x] `test_airflow_dagrun.py` — reviewed (static, quality)
- [x] `test_airflow_execution.py` — reviewed (static, quality)
- [x] `test_config.py` — reviewed (static, quality)

## Normative Spec Inventory (unique: 18)

- [x] `data-operations-incident-lifecycle/spec.md` — reviewed (static, quality)
- [x] `data-operations-stage-execution/spec.md` — reviewed (static, quality)
- [x] `data-platform-dbt-analytics/spec.md` — reviewed (static, quality)
- [x] `data-platform-duckdb-access/spec.md` — reviewed (static, quality)
- [x] `hmda-data-eda-descriptive-evidence/spec.md` — reviewed (static, quality)
- [x] `hmda-data-ingestion/spec.md` — reviewed (static, quality)
- [x] `hmda-data-synthetic-defects/spec.md` — reviewed (static, quality)
- [x] `orchestration-pipeline/spec.md` — reviewed (static, quality)
- [x] `reliability-agentic-review/spec.md` — reviewed (static, quality)
- [x] `reliability-data-contracts/spec.md` — reviewed (static, quality)
- [x] `reliability-evaluation-report/spec.md` — reviewed (static, quality)
- [x] `reliability-evidence-table-metadata/spec.md` — reviewed (static, quality)
- [x] `reliability-impact-analysis/spec.md` — reviewed (static, quality)
- [x] `reliability-incident-detection/spec.md` — reviewed (static, quality)
- [x] `reliability-profile-snapshots/spec.md` — reviewed (static, quality)
- [x] `reliability-recovery-backfill/spec.md` — reviewed (static, quality)
- [x] `reliability-remediation-draft/spec.md` — reviewed (static, quality)
- [x] `reliability-schema-recovery/spec.md` — reviewed (static, quality)

## Self-Review

Inventory comes from complete Git tree (1,134 items, `truncated=false`), not filename guesses. All `__init__.py`, domain `conftest.py`, shared dbt test are retained. Data Platform의 dbt test는 별도 경로이므로 prefix 규칙에서 예외로 표기했다. No item is `reviewed` or `excluded` yet; the first-pass report never claimed file-by-file deep review. No tests were run. Domain-level completion stays pending.

## Supplemental Detector Review (2026-10-14)

[Zero-threshold 및 baseline 결측률 경계 감사](06-review-reliability-detection-boundaries.md)에서 detector source, threshold model, request/result contracts, canonical spec와 unit test를 대조했다. 위 8개 경로는 일부 함수·계약을 검토한 `sampled`이며 full-file semantic review나 pytest 완료가 아니다. 추가로 10개 테스트 모듈의 테스트 함수와 assertion/raises 구조를 표본 스캔했지만, assertion이 존재한다는 사실을 oracle 충실도 증명으로 간주하지 않아 각 파일의 status를 임의로 승격하지 않았다.
