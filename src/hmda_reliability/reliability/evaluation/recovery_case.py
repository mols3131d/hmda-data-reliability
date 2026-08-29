"""복구 안전성 평가 케이스 어댑터 모듈."""

from collections.abc import Sequence

from hmda_reliability.reliability.evaluation.case_result import EvaluationCaseResult
from hmda_reliability.reliability.recovery import BackfillValidationResult


def build_recovery_evaluation_case(
    *,
    case_name: str,
    expected_incident_types: Sequence[str],
    detected_incident_types: Sequence[str],
    recovery: BackfillValidationResult | None = None,
    failure_stage: str | None = None,
    reconciliation_action: str | None = None,
    evidence_refs: Sequence[str] = (),
    artifact_projection_ids: Sequence[str] = (),
) -> EvaluationCaseResult:
    """복구 성공 또는 실패 결과를 관찰 가능한 평가 evidence로 변환한다."""

    target_mutated = None
    resolved_reconciliation_action = reconciliation_action
    if recovery is not None:
        target_mutated = recovery.mutation_state == "partition_changed"
        if resolved_reconciliation_action is None:
            resolved_reconciliation_action = recovery.reconciliation_action
    elif failure_stage is not None:
        target_mutated = failure_stage != "before_target_mutation"
    return EvaluationCaseResult(
        case_name=case_name,
        expected_incident_types=list(expected_incident_types),
        detected_incident_types=list(detected_incident_types),
        required_actions=(
            ["complete_recovery"]
            if failure_stage is not None
            or (recovery is not None and not recovery.validation_passed)
            else []
        ),
        evidence_refs=list(evidence_refs),
        target_mutated=target_mutated,
        failure_stage=failure_stage,
        reconciliation_action=resolved_reconciliation_action,
        artifact_projection_ids=list(artifact_projection_ids),
    )
