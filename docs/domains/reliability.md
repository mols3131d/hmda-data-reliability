# Reliability: Read-Only Analysis And Approved Recovery

**`reliability`는 read-only 분석과 승인된 side effect를 분리한다.** Raw table과 dbt artifact로 incident, downstream 영향, remediation draft를 계산하며, 승인된 backfill과 evaluation report 작성은 별도 API로만 제공한다.

> [!IMPORTANT]
> **Lifecycle은 데이터를 변경하지 않는다.** approval 생성, source 접근, partition overwrite, validation, report file write를 수행하지 않는다.

## Scope

| In scope | Out of scope |
| --- | --- |
| table metadata와 profile snapshot 생성 | 자동 backfill, 자동 승인 |
| profile 기반 incident 탐지 | dbt 모델 수정 또는 `dbt build` 실행 |
| dbt lineage 영향 분석과 remediation draft | Dagster job 등록 |
| 승인된 backfill validation, synthetic case 평가 | human approval UI, 장기 모니터링 |

원천 적재와 dbt 모델 계약은 [`hmda-data.md`](hmda-data.md), [`data-platform.md`](data-platform.md)에 있다. application lifecycle 조합은 [`data-operations.md`](data-operations.md)가 소유한다.

## Read-only Lifecycle

`run_incident_lifecycle(request, baseline)`는 다음 순서로 current 상태를 읽고 결과를 조합한다.

```mermaid
flowchart LR
    raw[Raw DuckDB table] --> metadata[Table metadata evidence]
    raw --> profile[Current profile snapshot]
    baseline[Caller baseline] --> detection[Incident detection]
    profile --> detection
    detection --> impact[dbt impact analysis]
    artifacts[manifest.json + run_results.json] --> impact
    impact --> draft[Remediation draft]
```

| Step | Input | Output |
| --- | --- | --- |
| Metadata | raw DuckDB table | row count evidence |
| Profile | raw DuckDB table, partition, profile columns | `ProfileSnapshot` |
| Detection | baseline, current profile, thresholds | `DetectionResult[]` |
| Impact | incident, `manifest.json`, `run_results.json` | `ImpactAnalysisResult` |
| Remediation | incident, evidence, lineage evidence | `RemediationDraft` |

baseline과 current는 같은 asset·partition이어야 한다. lifecycle은 metadata, profile, artifact만 읽고 `LifecycleResult`를 반환한다. 각 요약 목록은 처음 탐지한 순서를 유지하며 중복을 제거한다.

## Detection And Impact

`detect_basic_incidents(DetectionRequest)`는 baseline/current profile을 비교한다.

| Incident | Default threshold | Evidence |
| --- | --- | --- |
| `volume_drop` | row count 감소 비율 $\geq 0.5$ | baseline/current row count, drop ratio |
| `null_spike` | null rate 증가량 $\geq 0.1$ | 컬럼, baseline/current null rate |
| `schema_drift` | schema hash 변경 | baseline/current schema hash |
| `freshness_delay` | freshness 지연 $\geq 60$분 | delay, threshold minutes |

threshold는 `DetectionThresholds`로 교체할 수 있다. `analyze_dbt_impact(ImpactAnalysisRequest)`는 manifest의 source/model dependency를 따라 downstream asset을 계산하고, manifest와 run results 경로를 `LineageEvidence`에 기록한다. 유효하지 않거나 누락된 artifact는 `ImpactAnalysisError`다.

`create_remediation_draft(RemediationDraftRequest)`는 evidence와 lineage를 바탕으로 권장 조치, backfill 조치, validation 조치, dbt test 제안을 결정론적으로 만든다. draft는 실행 지시가 아니라 approval 검토 대상이다.

## Approved Recovery And Evaluation

Lifecycle 밖의 side effect는 명시적 API로만 실행한다.

| Capability | API | Boundary |
| --- | --- | --- |
| Recovery | `execute_approved_backfill(connection, request)` | 승인 상태와 `overwrite_partition`, `rerun_profile_snapshot` action을 검증한 뒤 partition을 덮어쓰고 profile을 다시 만든다. |
| Evaluation | `build_evaluation_report(cases)` | synthetic case 결과를 집계한다. |
| Volume-drop evaluation | `evaluate_volume_drop_vertical_slice(...)` | Clean baseline, controlled `volume_drop`, external approval, content recovery와 replay를 deterministic evidence로 조합한다. |
| Null-spike evaluation | `evaluate_null_spike_vertical_slice(...)` | Single profiled column의 controlled `null_spike`, exact clean candidate, external approval, content recovery, null-rate restoration과 replay를 조합한다. |
| Recovery case evidence | `build_recovery_evaluation_case(...)` | Mutation 여부, failure stage, reconciliation과 artifact projection을 evaluation case로 변환한다. |
| Evaluation output | `write_evaluation_report(report, output_path)` | Markdown report 파일을 쓴다. |

`RecoveryProposal`은 incident, target partition, candidate content identity, validation evidence, approved before/after identity, dbt projection과 target action을 하나의 immutable contract로 묶는다. `Approval`과 `ApprovedBackfillRequest`의 exact proposal이 다르거나 필수 action이 없으면 source 접근과 target mutation 전에 `ApprovalGateError`로 차단한다.

Recovery는 current partition identity를 승인된 before/after state와 비교한다. Before state면 transaction 내부 compare-and-replace를 실행하고, expected after state면 overwrite 없이 profile verification을 재개한다. 어느 state와도 다르면 기존 approval로 추가 mutation하지 않는다. `BackfillValidationResult`는 content identity를 최종 oracle로 사용하고 mutation state와 reconciliation action을 함께 반환한다.

Null-spike evaluation은 recovery executor의 content identity oracle을 변경하지 않는다. Expected recovery identity와 target column null rate를 original clean fixture에서 유도하고, residual-null candidate는 approval과 mutation 전에 차단한다. 성공한 recovery에서는 baseline, recovery와 replay null rate를 별도 evidence로 보존하고 post-recovery lifecycle에서 incident가 해소됐는지 확인한다. Recovery와 replay quality acceptance가 완료된 뒤 post-recovery lifecycle 또는 target validation이 실패해도 evaluator는 이미 확정한 세 null-rate evidence를 post-mutation failure case에 보존하고 `resume_verification` reconciliation을 반환한다. 반대로 content validation failure는 `request_new_validation_and_approval`, null-rate-only mismatch는 `resume_verification`으로 구분한다. 첫 vertical slice는 전체 lifecycle incident가 target-column `null_spike` 하나인 경우로 제한한다.

Synthetic setup과 recovery mutation evidence를 분리하기 위해 evaluation target, workspace clean database와 candidate database는 모두 새 path여야 한다. 하나라도 이미 존재하면 source load와 external callback 전에 요청을 거부하며 기존 content를 변경하지 않는다. Existing operational database를 직접 평가하거나 같은 연도의 다른 source-file population과 profile을 합치는 흐름은 이 API의 범위가 아니다.

## Public Surface

외부 호출자는 [`reliability/__init__.py`](../../src/project_pivot/reliability/__init__.py)의 re-export를 사용한다.

| Area | Main APIs |
| --- | --- |
| Profile and metadata | `create_profile_snapshot`, `create_table_metadata_evidence` |
| Detection | `detect_basic_incidents` |
| Impact and draft | `analyze_dbt_impact`, `create_remediation_draft` |
| Recovery | `execute_approved_backfill` |
| Evaluation | `evaluate_volume_drop_vertical_slice`, `evaluate_null_spike_vertical_slice`, `build_recovery_evaluation_case`, `build_evaluation_report`, `render_evaluation_report_markdown`, `write_evaluation_report` |

계약 모델은 `reliability/contracts`에 있으며, 알 수 없는 필드는 거부되고 모델은 변경 불가다.

## Reading Order

1. [`reliability/__init__.py`](../../src/project_pivot/reliability/__init__.py)
1. [`incident_lifecycle.py`](../../src/project_pivot/data_operations/incident_lifecycle.py)
1. [`tests/reliability/test_basic_incident_detection.py`](../../tests/reliability/test_basic_incident_detection.py)
1. [`tests/reliability/test_impact_analysis.py`](../../tests/reliability/test_impact_analysis.py)
1. [`tests/reliability/test_approval_backfill_validation.py`](../../tests/reliability/test_approval_backfill_validation.py)
1. [`tests/reliability/test_evaluation_report.py`](../../tests/reliability/test_evaluation_report.py)
1. [`tests/reliability/test_null_spike_evaluation.py`](../../tests/reliability/test_null_spike_evaluation.py)
