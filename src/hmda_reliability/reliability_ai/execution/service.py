"""위임된 작업 실행 및 감독자/인간 대상 보고 서비스 모듈."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from hmda_reliability.reliability.errors import ApprovalGateError
from hmda_reliability.reliability.remediation import (
    ApprovedBackfillRequest,
    ApprovedSchemaRecoveryRequest,
    execute_approved_backfill,
    execute_approved_schema_recovery,
)
from hmda_reliability.reliability_ai.contracts import AgenticReviewInput
from hmda_reliability.reliability_ai.execution.contracts import (
    ActionProposal,
    ExecutionReceipt,
    ReportEnvelope,
    TaskEnvelope,
)
from hmda_reliability.reliability_ai.investigation.service import investigate_incident
from hmda_reliability.reliability_ai.settings import ReliabilityAISettings
from hmda_reliability.runtime_ai.provider import OpenAICompatibleAdapter
from hmda_reliability.runtime_ai.settings import RuntimeAISettings


def execute_delegated_task(
    task: TaskEnvelope,
    review_input: AgenticReviewInput,
    *,
    settings: RuntimeAISettings,
    ai_settings: ReliabilityAISettings | None = None,
    provider: OpenAICompatibleAdapter | None = None,
    connection: Any | None = None,
    approved_backfill_request: ApprovedBackfillRequest | None = None,
    approved_schema_recovery_request: ApprovedSchemaRecoveryRequest | None = None,
) -> ReportEnvelope:
    """위임받은 조치 과업을 실행하거나 승인 필요 제안 및 불확실성을 보고한다.

    안전성 원칙:
    - 외부 승인(`Approval`) 없는 데이터베이스 변경은 엄격히 차단된다.
    - 허가되지 않은 도구 호출이나 작업(`allowed_actions`)은 시도되지 않는다.
    - 실행된 복구 작업에 대해서만 공식 `ExecutionReceipt`가 발행된다.
    """
    investigation_result = investigate_incident(
        review_input,
        settings=settings,
        ai_settings=ai_settings,
        provider=provider,
    )

    incident = review_input.incident
    receipts: list[ExecutionReceipt] = []
    proposals: list[ActionProposal] = []
    blocked_or_unknown: list[str] = [
        f"{u.topic}: {u.description}" for u in investigation_result.uncertainties
    ]
    report_status = "completed"

    # 승인된 백필 요청이 제공되었고 허용 목록에 포함된 경우
    if approved_backfill_request is not None:
        if "execute_approved_backfill" not in task.allowed_actions:
            blocked_or_unknown.append(
                "execute_approved_backfill is not in task.allowed_actions"
            )
            report_status = "blocked"
        elif connection is None:
            blocked_or_unknown.append(
                "connection is required to execute approved backfill"
            )
            report_status = "blocked"
        else:
            try:
                backfill_result = execute_approved_backfill(
                    connection, approved_backfill_request
                )
                receipts.append(
                    ExecutionReceipt(
                        receipt_id=f"rec-backfill-{uuid.uuid4().hex[:8]}",
                        task_id=task.task_id,
                        action_type="backfill",
                        executor="reliability.remediation.execute_approved_backfill",
                        approval_id=approved_backfill_request.approval.approval_id,
                        proposal_id=approved_backfill_request.proposal.incident_id,
                        executed_at=datetime.now(UTC),
                        success=backfill_result.validation_passed,
                        mutation_state=backfill_result.mutation_state,
                        before_state=str(backfill_result.approved_before_identity),
                        after_state=str(backfill_result.actual_identity),
                        revalidated=backfill_result.validation_passed,
                        details={"row_count": backfill_result.row_count},
                    )
                )
            except (ApprovalGateError, Exception) as exc:
                blocked_or_unknown.append(f"backfill execution failed: {exc}")
                report_status = "failed"

    # 승인된 스키마 복구 요청이 제공되었고 허용 목록에 포함된 경우
    elif approved_schema_recovery_request is not None:
        if "execute_approved_schema_recovery" not in task.allowed_actions:
            blocked_or_unknown.append(
                "execute_approved_schema_recovery is not in task.allowed_actions"
            )
            report_status = "blocked"
        else:
            try:
                schema_result = execute_approved_schema_recovery(
                    approved_schema_recovery_request
                )
                receipts.append(
                    ExecutionReceipt(
                        receipt_id=f"rec-schema-{uuid.uuid4().hex[:8]}",
                        task_id=task.task_id,
                        action_type="schema_recovery",
                        executor="reliability.remediation.execute_approved_schema_recovery",
                        approval_id=approved_schema_recovery_request.approval.approval_id,
                        proposal_id=approved_schema_recovery_request.proposal.table_name,
                        executed_at=datetime.now(UTC),
                        success=schema_result.validation_passed,
                        mutation_state=schema_result.mutation_state,
                        before_state=str(schema_result.approved_before_state),
                        after_state=str(schema_result.actual_state),
                        revalidated=schema_result.validation_passed,
                        details={
                            "executed_actions": list(schema_result.executed_actions)
                        },
                    )
                )
            except Exception as exc:
                blocked_or_unknown.append(f"schema recovery execution failed: {exc}")
                report_status = "failed"

    # 승인된 복구 실행이 없는 일반 조치 제안 생성 (승인 필요 상태 유지)
    needs_backfill = (
        bool(review_input.draft.backfill_actions)
        or review_input.draft.requires_approval
    )
    if not receipts and report_status != "failed" and needs_backfill:
        proposals.append(
            ActionProposal(
                proposal_id=f"prop-{uuid.uuid4().hex[:8]}",
                task_id=task.task_id,
                action_type="prepare_partition_backfill",
                target_asset=incident.asset_name,
                partition=incident.partition,
                parameters={
                    "recommended_actions": review_input.draft.recommended_actions
                },
                requires_approval=True,
                status="awaiting_approval",
                risk_assessment="데이터 백필은 파티션 검증 및 외부 승인이 필요합니다.",
            )
        )
        report_status = "awaiting_approval"

    recipient_type = "supervisor" if task.recipient == "supervisor" else "human"

    if report_status == "completed":
        next_reqs = tuple(review_input.draft.validation_actions)
    elif report_status == "awaiting_approval":
        next_reqs = ("외부 승인 필요",)
    else:
        next_reqs = ("원인 및 권한 확인 필요",)

    return ReportEnvelope(
        report_id=f"rep-{uuid.uuid4().hex[:8]}",
        task_id=task.task_id,
        recipient=recipient_type,
        status=report_status,
        facts=investigation_result.facts,
        hypotheses=investigation_result.hypotheses,
        proposed_actions=tuple(proposals),
        execution_receipts=tuple(receipts),
        blocked_or_unknown=tuple(blocked_or_unknown),
        evidence_refs=tuple(incident.evidence_refs),
        next_requests=next_reqs,
    )
