# Freshness Delay Evaluation Test Design

## Contract

The evaluator owns an isolated Bronze-ingestion clock experiment. It must keep
logical HMDA content and schema stable while changing only scoped `ingested_at`,
require exact external approval, recover through the compound content/temporal
gate, and replay without another overwrite.

## Scenarios

| Scenario | Oracle | Test |
| --- | --- | --- |
| Controlled delay and recovery | Exact fixed timestamps, one `freshness_delay`, equal identities, successful recovery and replay | `test_freshness_delay_vertical_slice_recovers_and_replays` |
| Existing or aliased database path | Reject before workspace creation or callback | `test_freshness_evaluation_rejects_existing_database_before_side_effects`, `test_freshness_evaluation_rejects_aliased_database_paths` |
| Invalid delay boundary | Reject `delay_minutes < max_age_minutes` before side effects | `test_freshness_evaluation_rejects_insufficient_delay` |
| Inexact controlled timestamp | Reject before validation or approval callbacks | `test_freshness_evaluation_rejects_inexact_controlled_timestamp` |
| Candidate changes during validation | Re-measure exported artifact and reject before proposal or approval | `test_freshness_evaluation_rejects_validation_mutation_before_approval` |
| Temporal target drift | No recovery mutation; request new validation and approval | `test_freshness_evaluation_reports_temporal_target_drift` |
| Expired replay | Preserve completed recovery and require new validation and approval | `test_freshness_evaluation_classifies_expired_replay_for_new_approval` |
| Invalid recovery or replay result | Stop before target validation and preserve the failed oracle | `test_freshness_evaluation_rejects_failed_recovery_validation` |
| Unresolved post-recovery incident | Stop before target validation with detected incident evidence | `test_freshness_evaluation_blocks_target_validation_for_unresolved_incident` |
| Failure after freshness acceptance | Preserve recovery/replay observations and resume verification | `test_freshness_evaluation_preserves_evidence_on_target_validation_failure`, `test_freshness_evaluation_preserves_evidence_on_post_lifecycle_failure` |
| Unavailable candidate measurement | Reject before candidate validation or approval | `test_freshness_evaluation_rejects_unavailable_candidate_before_approval` |

## Exclusions

- Source publication freshness, downloading, scheduling, alerting, and production
  database mutation are outside this evaluator.
- Exact transaction race coverage belongs to partition-loader and recovery-executor
  component tests.
