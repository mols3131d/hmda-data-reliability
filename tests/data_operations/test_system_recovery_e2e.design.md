# System Recovery Deterministic E2E Test Design

## Contract

The deterministic system recovery E2E verification proves the complete loop across the Data Plane (Bronze partition ingestion, read-only quality gate, quality-gated real dbt build, artifact promotion) and the Reliability Control Plane (read-only incident lifecycle, candidate validation via real dbt, exact proposal binding, approval gate, partition recovery backfill, post-recovery re-validation, and replay reconciliation) without external model or network dependency.

## Scenarios

| Scenario | Oracle | Test |
| --- | --- | --- |
| S0: Clean Data Plane Execution | Clean 2025 partition loads, quality gate passes, real dbt build succeeds, candidate artifacts are promoted to current projection, staging/mart rows are verifiable | `test_deterministic_system_recovery_e2e` |
| S1: Controlled Defect Injection & Gate Block | Synthetic `null_spike(income)` (50% null) loads into target, preserves row count, alters content identity, quality gate raises `QualityGateError(null_spike(income))`, quality-gated dbt build is blocked | `test_deterministic_system_recovery_e2e` |
| S2: Read-Only Incident Analysis | Lifecycle compares target profile against clean baseline, detects single `null_spike`, leaves target content identity strictly unchanged (zero mutation) | `test_deterministic_system_recovery_e2e` |
| S3: Candidate Validation with Real dbt | Clean source loaded to isolated candidate DB, real dbt candidate build returns valid projection ID, exact proposal binds dirty before-identity, clean candidate identity, and required actions | `test_deterministic_system_recovery_e2e` |
| S5: Approved Recovery Execution | Valid `Approval` fixture matching exact proposal enables backfill, returns `partition_changed`, validates post-recovery content identity against clean fixture identity | `test_deterministic_system_recovery_e2e` |
| S6: Post-Recovery Re-validation & Analytics | Target quality gate passes, lifecycle detects 0 incidents, quality-gated dbt build succeeds, new projection promoted, staging/mart queries succeed | `test_deterministic_system_recovery_e2e` |
| S7: Replay Reconciliation | Second backfill on recovered target reconciles with `mutation_state="already_recovered"` without redundant partition rewrite | `test_deterministic_system_recovery_e2e` |
| Vertical Slice Evaluator with Real dbt | `evaluate_null_spike_vertical_slice` executes end-to-end using real dbt build and promotion callbacks with zero mocks | `test_null_spike_evaluator_real_dbt_e2e` |
| S4-A: Pre-Approval Safety (Rejected Approval) | Rejected approval raises `ApprovalGateError`, dirty target content identity and measured null rate remain strictly unchanged | `test_pre_approval_safety_rejected_approval_zero_mutation` |
| S4-B: Pre-Approval Safety (Mismatched Identity) | Approval with mismatched before-identity raises `ApprovalGateError`, dirty target content identity remains strictly unchanged | `test_pre_approval_safety_mismatched_identity_zero_mutation` |
| S4-C: Pre-Approval Safety (Mismatched Actions) | Approval with missing/altered actions raises `ApprovalGateError`, dirty target content identity remains strictly unchanged | `test_pre_approval_safety_mismatched_actions_zero_mutation` |

## Exclusions

- Human review, Agentic review, live LLM API calls, and provider routing are excluded from this deterministic core.
- Modifying Airflow DAG definitions to add recovery or incident lifecycle tasks is forbidden.
- Test-only bypasses or mock authorizations are strictly prohibited.
- Production multi-partition edge cases belong to individual component/integration test suites.
