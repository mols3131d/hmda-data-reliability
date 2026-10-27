---
type: report
title: Test Design Review Coverage Inventory
description: 고정 revision의 테스트·fixture·설계 파일별 담당 영역과 실제 독립 검토 범위를 확인합니다.
tags:
  - testing
  - review
---

# Test Design Review Coverage Inventory

Revision: `3ab899100fc0b35e23d464bd761f3b144a978ae7`. 추적 중인 tests 파일 94개: test module 74개, support 17개, design 문서 3개다. [tests/AGENTS.md](../../../tests/AGENTS.md)는 검토 대상 대신 적용 지침으로 읽었다. 파일 분류나 test 개수는 설계 품질 점수가 아니다. 두 specialist가 각 batch의 모든 파일 본문·fixture·assertion을 읽었으며 source·Spec은 관련 계약을 대조했다. Targeted-only·unreviewed target은 없다.

| Batch | Target Files | Report |
| --- | --- | --- |
| A | 19 | HMDA Data·Data Platform·Data Operations |
| B | 23 | Reliability core |
| C | 5 | Reliability evaluation |
| D | 24 | Review AI·Runtime AI·Orchestration |
| E | 23 | Common Support·CI |

| Domain | Batch | Type | File | Review State |
| --- | --- | --- | --- | --- |
| cross_cutting | E | support | [tests/__init__.py](../../../tests/__init__.py) | Full: quality + adversarial |
| data_operations | A | support | [tests/data_operations/__init__.py](../../../tests/data_operations/__init__.py) | Full: quality + adversarial |
| data_operations | A | test | [tests/data_operations/test_dbt_runner.py](../../../tests/data_operations/test_dbt_runner.py) | Full: quality + adversarial |
| data_operations | A | test | [tests/data_operations/test_incident_lifecycle.py](../../../tests/data_operations/test_incident_lifecycle.py) | Full: quality + adversarial |
| data_operations | A | test | [tests/data_operations/test_quality_gate.py](../../../tests/data_operations/test_quality_gate.py) | Full: quality + adversarial |
| data_operations | A | design | [tests/data_operations/test_system_recovery_e2e.design.md](../../../tests/data_operations/test_system_recovery_e2e.design.md) | Full: quality + adversarial |
| data_operations | A | test | [tests/data_operations/test_system_recovery_e2e.py](../../../tests/data_operations/test_system_recovery_e2e.py) | Full: quality + adversarial |
| data_platform | A | support | [tests/data_platform/__init__.py](../../../tests/data_platform/__init__.py) | Full: quality + adversarial |
| data_platform | A | test | [tests/data_platform/test_artifacts.py](../../../tests/data_platform/test_artifacts.py) | Full: quality + adversarial |
| data_platform | A | test | [tests/data_platform/test_duckdb.py](../../../tests/data_platform/test_duckdb.py) | Full: quality + adversarial |
| data_platform | A | test | [tests/data_platform/test_sql.py](../../../tests/data_platform/test_sql.py) | Full: quality + adversarial |
| data_platform | A | test | [tests/dbt/test_analytics_foundation.py](../../../tests/dbt/test_analytics_foundation.py) | Full: quality + adversarial |
| hmda_data | A | support | [tests/hmda_data/__init__.py](../../../tests/hmda_data/__init__.py) | Full: quality + adversarial |
| hmda_data | A | support | [tests/hmda_data/conftest.py](../../../tests/hmda_data/conftest.py) | Full: quality + adversarial |
| hmda_data | A | test | [tests/hmda_data/eda/test_eda.py](../../../tests/hmda_data/eda/test_eda.py) | Full: quality + adversarial |
| hmda_data | A | test | [tests/hmda_data/eda/test_eda_evidence.py](../../../tests/hmda_data/eda/test_eda_evidence.py) | Full: quality + adversarial |
| hmda_data | A | test | [tests/hmda_data/eda/test_eda_explorer.py](../../../tests/hmda_data/eda/test_eda_explorer.py) | Full: quality + adversarial |
| hmda_data | A | test | [tests/hmda_data/test_ingestion.py](../../../tests/hmda_data/test_ingestion.py) | Full: quality + adversarial |
| hmda_data | A | test | [tests/hmda_data/test_ingestion_partition.py](../../../tests/hmda_data/test_ingestion_partition.py) | Full: quality + adversarial |
| hmda_data | A | test | [tests/hmda_data/test_synthetic.py](../../../tests/hmda_data/test_synthetic.py) | Full: quality + adversarial |
| orchestration | D | support | [tests/orchestration/__init__.py](../../../tests/orchestration/__init__.py) | Full: quality + adversarial |
| orchestration | D | test | [tests/orchestration/test_airflow_dag.py](../../../tests/orchestration/test_airflow_dag.py) | Full: quality + adversarial |
| orchestration | D | design | [tests/orchestration/test_airflow_dagrun.design.md](../../../tests/orchestration/test_airflow_dagrun.design.md) | Full: quality + adversarial |
| orchestration | D | test | [tests/orchestration/test_airflow_dagrun.py](../../../tests/orchestration/test_airflow_dagrun.py) | Full: quality + adversarial |
| orchestration | D | test | [tests/orchestration/test_airflow_execution.py](../../../tests/orchestration/test_airflow_execution.py) | Full: quality + adversarial |
| orchestration | D | test | [tests/orchestration/test_config.py](../../../tests/orchestration/test_config.py) | Full: quality + adversarial |
| reliability | B | support | [tests/reliability/__init__.py](../../../tests/reliability/__init__.py) | Full: quality + adversarial |
| reliability | B | support | [tests/reliability/conftest.py](../../../tests/reliability/conftest.py) | Full: quality + adversarial |
| reliability | B | support | [tests/reliability/contracts/__init__.py](../../../tests/reliability/contracts/__init__.py) | Full: quality + adversarial |
| reliability | B | test | [tests/reliability/contracts/test_approval.py](../../../tests/reliability/contracts/test_approval.py) | Full: quality + adversarial |
| reliability | B | test | [tests/reliability/contracts/test_evidence.py](../../../tests/reliability/contracts/test_evidence.py) | Full: quality + adversarial |
| reliability | B | test | [tests/reliability/contracts/test_incident.py](../../../tests/reliability/contracts/test_incident.py) | Full: quality + adversarial |
| reliability | B | test | [tests/reliability/contracts/test_lineage.py](../../../tests/reliability/contracts/test_lineage.py) | Full: quality + adversarial |
| reliability | B | test | [tests/reliability/contracts/test_profile.py](../../../tests/reliability/contracts/test_profile.py) | Full: quality + adversarial |
| reliability | B | test | [tests/reliability/contracts/test_recovery_proposal.py](../../../tests/reliability/contracts/test_recovery_proposal.py) | Full: quality + adversarial |
| reliability | B | test | [tests/reliability/contracts/test_schema_recovery.py](../../../tests/reliability/contracts/test_schema_recovery.py) | Full: quality + adversarial |
| reliability | B | test | [tests/reliability/contracts/test_validation.py](../../../tests/reliability/contracts/test_validation.py) | Full: quality + adversarial |
| reliability | B | test | [tests/reliability/test_approval_backfill_validation.py](../../../tests/reliability/test_approval_backfill_validation.py) | Full: quality + adversarial |
| reliability | B | test | [tests/reliability/test_basic_incident_detection.py](../../../tests/reliability/test_basic_incident_detection.py) | Full: quality + adversarial |
| reliability | C | test | [tests/reliability/test_evaluation_report.py](../../../tests/reliability/test_evaluation_report.py) | Full: quality + adversarial |
| reliability | B | test | [tests/reliability/test_fixtures.py](../../../tests/reliability/test_fixtures.py) | Full: quality + adversarial |
| reliability | C | design | [tests/reliability/test_freshness_delay_evaluation.design.md](../../../tests/reliability/test_freshness_delay_evaluation.design.md) | Full: quality + adversarial |
| reliability | C | test | [tests/reliability/test_freshness_delay_evaluation.py](../../../tests/reliability/test_freshness_delay_evaluation.py) | Full: quality + adversarial |
| reliability | B | test | [tests/reliability/test_impact_analysis.py](../../../tests/reliability/test_impact_analysis.py) | Full: quality + adversarial |
| reliability | C | test | [tests/reliability/test_null_spike_evaluation.py](../../../tests/reliability/test_null_spike_evaluation.py) | Full: quality + adversarial |
| reliability | B | test | [tests/reliability/test_profile_snapshots.py](../../../tests/reliability/test_profile_snapshots.py) | Full: quality + adversarial |
| reliability | B | test | [tests/reliability/test_quality_gate.py](../../../tests/reliability/test_quality_gate.py) | Full: quality + adversarial |
| reliability | B | test | [tests/reliability/test_recovery_runtime_evidence.py](../../../tests/reliability/test_recovery_runtime_evidence.py) | Full: quality + adversarial |
| reliability | B | test | [tests/reliability/test_remediation_draft.py](../../../tests/reliability/test_remediation_draft.py) | Full: quality + adversarial |
| reliability | C | test | [tests/reliability/test_schema_drift_evaluation.py](../../../tests/reliability/test_schema_drift_evaluation.py) | Full: quality + adversarial |
| reliability | B | test | [tests/reliability/test_schema_recovery_candidate.py](../../../tests/reliability/test_schema_recovery_candidate.py) | Full: quality + adversarial |
| reliability | B | test | [tests/reliability/test_schema_recovery_executor.py](../../../tests/reliability/test_schema_recovery_executor.py) | Full: quality + adversarial |
| reliability | B | test | [tests/reliability/test_table_metadata_evidence.py](../../../tests/reliability/test_table_metadata_evidence.py) | Full: quality + adversarial |
| reliability | B | test | [tests/reliability/test_table_state_identity.py](../../../tests/reliability/test_table_state_identity.py) | Full: quality + adversarial |
| review_ai | D | support | [tests/review_ai/__init__.py](../../../tests/review_ai/__init__.py) | Full: quality + adversarial |
| review_ai | D | support | [tests/review_ai/conftest.py](../../../tests/review_ai/conftest.py) | Full: quality + adversarial |
| review_ai | D | support | [tests/review_ai/evaluation/fixtures/utility_comparison_6e64cc7.json](../../../tests/review_ai/evaluation/fixtures/utility_comparison_6e64cc7.json) | Full: quality + adversarial |
| review_ai | D | test | [tests/review_ai/evaluation/test_langfuse_projection.py](../../../tests/review_ai/evaluation/test_langfuse_projection.py) | Full: quality + adversarial |
| review_ai | D | test | [tests/review_ai/evaluation/test_utility_evaluation.py](../../../tests/review_ai/evaluation/test_utility_evaluation.py) | Full: quality + adversarial |
| review_ai | D | test | [tests/review_ai/test_context.py](../../../tests/review_ai/test_context.py) | Full: quality + adversarial |
| review_ai | D | test | [tests/review_ai/test_contracts.py](../../../tests/review_ai/test_contracts.py) | Full: quality + adversarial |
| review_ai | D | test | [tests/review_ai/test_dependency_boundaries.py](../../../tests/review_ai/test_dependency_boundaries.py) | Full: quality + adversarial |
| review_ai | D | test | [tests/review_ai/test_evidence_store.py](../../../tests/review_ai/test_evidence_store.py) | Full: quality + adversarial |
| review_ai | D | test | [tests/review_ai/test_live_harness.py](../../../tests/review_ai/test_live_harness.py) | Full: quality + adversarial |
| review_ai | D | test | [tests/review_ai/test_prompt_provider.py](../../../tests/review_ai/test_prompt_provider.py) | Full: quality + adversarial |
| review_ai | D | test | [tests/review_ai/test_public_surface.py](../../../tests/review_ai/test_public_surface.py) | Full: quality + adversarial |
| review_ai | D | test | [tests/review_ai/test_service.py](../../../tests/review_ai/test_service.py) | Full: quality + adversarial |
| review_ai | D | test | [tests/review_ai/test_settings.py](../../../tests/review_ai/test_settings.py) | Full: quality + adversarial |
| review_ai | D | test | [tests/review_ai/test_validator.py](../../../tests/review_ai/test_validator.py) | Full: quality + adversarial |
| runtime_ai | D | support | [tests/runtime_ai/__init__.py](../../../tests/runtime_ai/__init__.py) | Full: quality + adversarial |
| runtime_ai | D | test | [tests/runtime_ai/test_provider.py](../../../tests/runtime_ai/test_provider.py) | Full: quality + adversarial |
| runtime_ai | D | test | [tests/runtime_ai/test_settings.py](../../../tests/runtime_ai/test_settings.py) | Full: quality + adversarial |
| cross_cutting | E | support | [tests/scripts/__init__.py](../../../tests/scripts/__init__.py) | Full: quality + adversarial |
| cross_cutting | E | support | [tests/scripts/ci/__init__.py](../../../tests/scripts/ci/__init__.py) | Full: quality + adversarial |
| cross_cutting | E | support | [tests/scripts/ci/conftest.py](../../../tests/scripts/ci/conftest.py) | Full: quality + adversarial |
| cross_cutting | E | support | [tests/scripts/ci/helpers.py](../../../tests/scripts/ci/helpers.py) | Full: quality + adversarial |
| cross_cutting | E | test | [tests/scripts/ci/test_ci_classifier.py](../../../tests/scripts/ci/test_ci_classifier.py) | Full: quality + adversarial |
| cross_cutting | E | test | [tests/scripts/ci/test_ci_classifier_openspec.py](../../../tests/scripts/ci/test_ci_classifier_openspec.py) | Full: quality + adversarial |
| cross_cutting | E | test | [tests/scripts/ci/test_ci_classifier_python.py](../../../tests/scripts/ci/test_ci_classifier_python.py) | Full: quality + adversarial |
| cross_cutting | E | test | [tests/scripts/ci/test_ci_pytest.py](../../../tests/scripts/ci/test_ci_pytest.py) | Full: quality + adversarial |
| cross_cutting | E | test | [tests/scripts/ci/test_ci_steps.py](../../../tests/scripts/ci/test_ci_steps.py) | Full: quality + adversarial |
| cross_cutting | E | test | [tests/scripts/ci/test_ci_workflow.py](../../../tests/scripts/ci/test_ci_workflow.py) | Full: quality + adversarial |
| cross_cutting | E | test | [tests/scripts/test_agent_assets.py](../../../tests/scripts/test_agent_assets.py) | Full: quality + adversarial |
| cross_cutting | E | test | [tests/scripts/test_bootstrap.py](../../../tests/scripts/test_bootstrap.py) | Full: quality + adversarial |
| cross_cutting | E | test | [tests/scripts/test_clean.py](../../../tests/scripts/test_clean.py) | Full: quality + adversarial |
| cross_cutting | E | test | [tests/scripts/test_commands.py](../../../tests/scripts/test_commands.py) | Full: quality + adversarial |
| cross_cutting | E | test | [tests/scripts/test_generate_agent_routes.py](../../../tests/scripts/test_generate_agent_routes.py) | Full: quality + adversarial |
| cross_cutting | E | test | [tests/scripts/test_generate_docs_indexes.py](../../../tests/scripts/test_generate_docs_indexes.py) | Full: quality + adversarial |
| cross_cutting | E | test | [tests/scripts/test_log_agent_event.py](../../../tests/scripts/test_log_agent_event.py) | Full: quality + adversarial |
| cross_cutting | E | test | [tests/scripts/test_tach.py](../../../tests/scripts/test_tach.py) | Full: quality + adversarial |
| cross_cutting | E | test | [tests/scripts/test_tach_config.py](../../../tests/scripts/test_tach_config.py) | Full: quality + adversarial |
| cross_cutting | E | test | [tests/scripts/test_tool_wrappers.py](../../../tests/scripts/test_tool_wrappers.py) | Full: quality + adversarial |
| cross_cutting | E | test | [tests/scripts/test_validate_inbox_artifacts.py](../../../tests/scripts/test_validate_inbox_artifacts.py) | Full: quality + adversarial |
| cross_cutting | E | test | [tests/test_pytest_opentelemetry.py](../../../tests/test_pytest_opentelemetry.py) | Full: quality + adversarial |

공통 fixture와 source는 여러 batch에서 참고할 수 있지만 inventory의 primary 담당은 한 번만 부여한다. Full static review와 targeted inspection, runtime 실행 및 미실행은 최종 보고서에서 구분한다.
