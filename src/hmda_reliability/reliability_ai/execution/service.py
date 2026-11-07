"""위임된 작업 실행 및 감독자/인간 대상 보고 서비스 모듈."""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import duckdb

from hmda_reliability.reliability.errors import (
    ApprovalGateError,
    BackfillValidationError,
    SchemaRecoveryCandidateError,
    SchemaRecoveryValidationError,
)
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
    dbt_artifact_paths: tuple[Path, Path] | None = None,
    artifact_root: Path = Path(".local/artifacts"),
    clock: Callable[[], float] = time.monotonic,
) -> ReportEnvelope:
    """위임받은 조치 과업을 실행하거나 승인 필요 제안 및 불확실성을 보고한다.

    안전성 원칙:
    - 외부 승인(`Approval`) 없는 데이터베이스 변경은 엄격히 차단된다.
    - 허가되지 않은 도구 호출이나 작업(`allowed_actions`)은 시도되지 않는다.
    - 실행된 복구 작업에 대해서만 공식 `ExecutionReceipt`가 발행된다.
    """
    configured = ai_settings or ReliabilityAISettings()
    bounded_settings = ReliabilityAISettings(
        max_prompt_bytes=configured.max_prompt_bytes,
        max_tool_calls=min(configured.max_tool_calls, task.max_tool_calls),
        workflow_budget_seconds=min(
            configured.workflow_budget_seconds, task.workflow_budget_seconds
        ),
    )
    investigation_result = investigate_incident(
        review_input,
        settings=settings,
        ai_settings=bounded_settings,
        provider=provider,
        allowed_tools=task.allowed_tools,
        dbt_artifact_paths=dbt_artifact_paths,
        artifact_root=artifact_root,
        clock=clock,
    )

    if investigation_result.status != "completed":
        return ReportEnvelope(
            report_id=f"rep-{uuid.uuid4().hex}",
            task_id=task.task_id,
            recipient="supervisor" if task.recipient == "supervisor" else "human",
            status="failed",
            investigation=investigation_result,
            facts=investigation_result.facts,
            hypotheses=investigation_result.hypotheses,
            evidence_refs=tuple(review_input.incident.evidence_refs),
            blocked_or_unknown=(
                "investigation: "
                f"{investigation_result.failure_code or investigation_result.status}",
            ),
            next_requests=("조사 실패 원인 확인 필요",),
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
                backfill_validated = (
                    backfill_result.validation_passed
                    and backfill_result.freshness_validation_passed is not False
                )
                receipts.append(
                    ExecutionReceipt(
                        receipt_id=f"rec-backfill-{uuid.uuid4().hex[:8]}",
                        task_id=task.task_id,
                        action_type="backfill",
                        executor="reliability.remediation.execute_approved_backfill",
                        approval_id=approved_backfill_request.approval.approval_id,
                        proposal_id=approved_backfill_request.proposal.proposal_id,
                        executed_at=datetime.now(UTC),
                        success=backfill_validated,
                        mutation_state=backfill_result.mutation_state,
                        before_state=str(backfill_result.approved_before_identity),
                        after_state=str(backfill_result.actual_identity),
                        revalidated=backfill_validated,
                        reconciliation_action=backfill_result.reconciliation_action,
                        details=backfill_result.model_dump(mode="json"),
                    )
                )
                if not backfill_validated:
                    report_status = "partial"
                    blocked_or_unknown.append("backfill validation did not pass")
            except BackfillValidationError as exc:
                receipts.append(
                    _failed_recovery_receipt(
                        task,
                        action_type="backfill",
                        approval_id=approved_backfill_request.approval.approval_id,
                        proposal_id=approved_backfill_request.proposal.proposal_id,
                        error=exc,
                    )
                )
                blocked_or_unknown.append(f"backfill execution failed: {exc}")
                report_status = _recovery_failure_status(exc.mutation_state)
            except (OSError, duckdb.Error) as exc:
                receipts.append(
                    _failed_recovery_receipt(
                        task,
                        action_type="backfill",
                        approval_id=approved_backfill_request.approval.approval_id,
                        proposal_id=approved_backfill_request.proposal.proposal_id,
                        error=exc,
                    )
                )
                blocked_or_unknown.append(f"backfill execution state unknown: {exc}")
                report_status = "failed"
            except ApprovalGateError as exc:
                blocked_or_unknown.append(f"backfill execution failed: {exc}")
                report_status = "blocked"

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
                        proposal_id=approved_schema_recovery_request.proposal.proposal_id,
                        executed_at=datetime.now(UTC),
                        success=schema_result.validation_passed,
                        mutation_state=schema_result.mutation_state,
                        before_state=str(schema_result.approved_before_state),
                        after_state=str(schema_result.actual_state),
                        revalidated=schema_result.validation_passed,
                        reconciliation_action=schema_result.reconciliation_action,
                        details=schema_result.model_dump(mode="json"),
                    )
                )
                if not schema_result.validation_passed:
                    report_status = "partial"
                    blocked_or_unknown.append("schema recovery validation did not pass")
            except SchemaRecoveryValidationError as exc:
                receipts.append(
                    _failed_recovery_receipt(
                        task,
                        action_type="schema_recovery",
                        approval_id=approved_schema_recovery_request.approval.approval_id,
                        proposal_id=approved_schema_recovery_request.proposal.proposal_id,
                        error=exc,
                    )
                )
                blocked_or_unknown.append(f"schema recovery execution failed: {exc}")
                report_status = _recovery_failure_status(exc.mutation_state)
            except (SchemaRecoveryCandidateError, OSError, duckdb.Error) as exc:
                receipts.append(
                    _failed_recovery_receipt(
                        task,
                        action_type="schema_recovery",
                        approval_id=approved_schema_recovery_request.approval.approval_id,
                        proposal_id=approved_schema_recovery_request.proposal.proposal_id,
                        error=exc,
                    )
                )
                blocked_or_unknown.append(f"schema recovery execution failed: {exc}")
                report_status = "failed"
            except ApprovalGateError as exc:
                blocked_or_unknown.append(f"schema recovery execution failed: {exc}")
                report_status = "blocked"

    # 승인된 복구 실행이 없는 일반 조치 제안 생성 (승인 필요 상태 유지)
    needs_backfill = (
        bool(review_input.draft.backfill_actions)
        or review_input.draft.requires_approval
    )
    if not receipts and report_status == "completed" and needs_backfill:
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
    elif any(receipt.mutation_state == "not_reported" for receipt in receipts):
        next_reqs = ("복구 대상의 실제 상태와 도메인 오류 확인 필요",)
    else:
        next_reqs = ("원인 및 권한 확인 필요",)

    return ReportEnvelope(
        report_id=f"rep-{uuid.uuid4().hex[:8]}",
        task_id=task.task_id,
        recipient=recipient_type,
        status=report_status,
        investigation=investigation_result,
        facts=investigation_result.facts,
        hypotheses=investigation_result.hypotheses,
        proposed_actions=tuple(proposals),
        execution_receipts=tuple(receipts),
        blocked_or_unknown=tuple(blocked_or_unknown),
        evidence_refs=tuple(incident.evidence_refs),
        next_requests=next_reqs,
    )


def _recovery_failure_status(
    mutation_state: str | None,
) -> Literal["failed", "partial"]:
    return (
        "partial"
        if mutation_state
        in {
            "partition_changed",
            "partition_replaced",
            "already_recovered",
            "table_replaced",
            "already_restored",
        }
        else "failed"
    )


def _failed_recovery_receipt(
    task: TaskEnvelope,
    *,
    action_type: str,
    approval_id: str,
    proposal_id: str,
    error: (
        BackfillValidationError
        | SchemaRecoveryValidationError
        | SchemaRecoveryCandidateError
        | OSError
        | duckdb.Error
    ),
) -> ExecutionReceipt:
    mutation_state = "not_reported"
    reconciliation_action = None
    failure_stage = None
    context: dict[str, Any] = {}
    if isinstance(error, (BackfillValidationError, SchemaRecoveryValidationError)):
        mutation_state = error.mutation_state or mutation_state
        reconciliation_action = error.reconciliation_action
        context = error.context
        if isinstance(error, SchemaRecoveryValidationError):
            failure_stage = error.failure_stage
    elif isinstance(error, SchemaRecoveryCandidateError):
        mutation_state = "not_started"
        failure_stage = "before_target_mutation"
        context = error.context
    return ExecutionReceipt(
        receipt_id=f"rec-{uuid.uuid4().hex}",
        task_id=task.task_id,
        action_type=action_type,
        executor=(
            "reliability.remediation.execute_approved_backfill"
            if action_type == "backfill"
            else "reliability.remediation.execute_approved_schema_recovery"
        ),
        approval_id=approval_id,
        proposal_id=proposal_id,
        executed_at=datetime.now(UTC),
        success=False,
        mutation_state=mutation_state,
        failure_code=type(error).__name__,
        reconciliation_action=reconciliation_action,
        details={
            "failure_stage": failure_stage,
            "context": context,
            "failure_message": str(error),
        },
    )
