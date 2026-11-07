"""위임된 작업 실행 및 결과 보고 계약 모델 정의 모듈."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from hmda_reliability.reliability.contracts.base import ReliabilityContract
from hmda_reliability.reliability_ai.investigation.contracts import (
    InvestigationHypothesis,
    InvestigationResult,
)


class TaskEnvelope(ReliabilityContract):
    """상위 모델 또는 인간 감독자가 위임하는 작업 명세 봉투."""

    task_id: str = Field(min_length=1)
    parent_task_id: str | None = None
    requester: str = Field(min_length=1)
    recipient: str = Field(min_length=1)
    goal: str = Field(min_length=1)
    allowed_tools: tuple[str, ...] = Field(default_factory=tuple)
    allowed_actions: tuple[str, ...] = Field(default_factory=tuple)
    max_tool_calls: int = Field(default=5, ge=1, le=20)
    workflow_budget_seconds: float = Field(default=60.0, gt=0)
    requires_external_approval: bool = True
    snapshot_refs: tuple[str, ...] = Field(default_factory=tuple)


class ActionProposal(ReliabilityContract):
    """에이전트가 제안하는 조치 권고안 (실행 권한이나 승인 그 자체가 아님)."""

    proposal_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    action_type: str = Field(min_length=1)
    target_asset: str = Field(min_length=1)
    partition: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = True
    status: Literal["proposed", "awaiting_approval", "rejected"] = "awaiting_approval"
    risk_assessment: str = ""


class ExecutionReceipt(ReliabilityContract):
    """승인된 복구 조치 수행 후 실제 도메인이 발행하는 공식 실행 영수증."""

    receipt_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    action_type: str = Field(min_length=1)
    executor: str = Field(min_length=1)
    approval_id: str | None = None
    proposal_id: str | None = None
    executed_at: datetime
    success: bool
    mutation_state: str
    before_state: str | None = None
    after_state: str | None = None
    revalidated: bool = False
    failure_code: str | None = None
    reconciliation_action: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ReportEnvelope(ReliabilityContract):
    """인간 또는 상위 감독자 모델에게 전달하는 최종 구조화 보고서."""

    report_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    recipient: Literal["human", "supervisor"]
    status: Literal["completed", "blocked", "awaiting_approval", "failed", "partial"]
    investigation: InvestigationResult | None = None
    facts: dict[str, Any] = Field(default_factory=dict)
    hypotheses: tuple[InvestigationHypothesis, ...] = Field(default_factory=tuple)
    proposed_actions: tuple[ActionProposal, ...] = Field(default_factory=tuple)
    execution_receipts: tuple[ExecutionReceipt, ...] = Field(default_factory=tuple)
    blocked_or_unknown: tuple[str, ...] = Field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = Field(default_factory=tuple)
    next_requests: tuple[str, ...] = Field(default_factory=tuple)
