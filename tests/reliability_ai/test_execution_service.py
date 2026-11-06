"""Tests for delegated execution, recovery guards, and reporting."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from hmda_reliability.reliability import (
    ApprovedBackfillRequest,
    BackfillValidationResult,
)
from hmda_reliability.reliability_ai import (
    AgenticReviewInput,
    TaskEnvelope,
    execute_delegated_task,
)
from hmda_reliability.runtime_ai.contracts import (
    ChatCompletionRequest,
    TransportResponse,
)
from hmda_reliability.runtime_ai.provider import OpenAICompatibleAdapter
from hmda_reliability.runtime_ai.settings import RuntimeAISettings

from .conftest import NullSpikeReviewMaterial

pytestmark = pytest.mark.unit


def _settings() -> RuntimeAISettings:
    return RuntimeAISettings(
        base_url="http://localhost:11434/v1",
        api_key="test",
        model="test-model",
        max_retries=0,
    )


class ScriptedTransport:
    def __init__(self, responses: list[TransportResponse]) -> None:
        self.responses = list(responses)

    def create(self, request: ChatCompletionRequest) -> TransportResponse:
        if not self.responses:
            return TransportResponse(content="{}")
        return self.responses.pop(0)


def test_delegated_task_unapproved_remediation_generates_action_proposal(
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    material = null_spike_review_material
    # backfill action이 있는 draft 생성
    draft = material.draft.model_copy(
        update={
            "backfill_actions": ["prepare_partition_backfill"],
            "requires_approval": True,
        }
    )
    review_input = AgenticReviewInput(
        incident=material.detection.incident,
        evidence=[material.detection.evidence],
        draft=draft,
        project_revision="rev-1",
    )

    task = TaskEnvelope(
        task_id="task_1",
        requester="supervisor_agent",
        recipient="human",
        goal="인시던트 조사 및 조치 방안 수립",
        allowed_tools=("get_incident_evidence",),
        allowed_actions=(),
    )

    transport = ScriptedTransport(
        [TransportResponse(content='{"facts": {"rule": "null_spike"}}')]
    )
    adapter = OpenAICompatibleAdapter(_settings(), transport=transport)

    report = execute_delegated_task(
        task,
        review_input,
        settings=_settings(),
        provider=adapter,
    )

    assert report.task_id == "task_1"
    assert report.recipient == "human"
    assert report.status == "awaiting_approval"
    assert len(report.proposed_actions) == 1
    assert report.proposed_actions[0].status == "awaiting_approval"
    assert report.proposed_actions[0].requires_approval is True
    assert len(report.execution_receipts) == 0


def test_delegated_task_blocks_unauthorized_action(
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    material = null_spike_review_material
    review_input = AgenticReviewInput(
        incident=material.detection.incident,
        evidence=[material.detection.evidence],
        draft=material.draft,
        project_revision="rev-1",
    )

    # allowed_actions에 execute_approved_backfill이 없음
    task = TaskEnvelope(
        task_id="task_2",
        requester="supervisor_agent",
        recipient="supervisor",
        goal="승인되지 않은 백필 시도",
        allowed_actions=(),
    )

    fake_backfill_req = MagicMock(spec=ApprovedBackfillRequest)

    report = execute_delegated_task(
        task,
        review_input,
        settings=_settings(),
        provider=OpenAICompatibleAdapter(_settings(), transport=ScriptedTransport([])),
        approved_backfill_request=fake_backfill_req,
    )

    assert report.status == "blocked"
    assert any("allowed_actions" in item for item in report.blocked_or_unknown)
    assert len(report.execution_receipts) == 0


def test_delegated_task_executes_approved_backfill_and_issues_receipt(
    null_spike_review_material: NullSpikeReviewMaterial,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    material = null_spike_review_material
    review_input = AgenticReviewInput(
        incident=material.detection.incident,
        evidence=[material.detection.evidence],
        draft=material.draft,
        project_revision="rev-1",
    )

    task = TaskEnvelope(
        task_id="task_3",
        requester="supervisor_agent",
        recipient="human",
        goal="승인된 백필 실행",
        allowed_actions=("execute_approved_backfill",),
    )

    # Fake approved request
    mock_request = MagicMock()
    mock_request.approval.approval_id = "app_123"
    mock_request.proposal.incident_id = material.detection.incident.incident_id

    # Mock execute_approved_backfill
    fake_val_result = MagicMock(spec=BackfillValidationResult)
    fake_val_result.validation_passed = True
    fake_val_result.mutation_state = "partition_replaced"
    fake_val_result.approved_before_identity = "hash_before"
    fake_val_result.actual_identity = "hash_after"
    fake_val_result.row_count = 100

    from hmda_reliability.reliability_ai.execution import service as exec_service

    monkeypatch.setattr(
        exec_service, "execute_approved_backfill", lambda conn, req: fake_val_result
    )

    report = execute_delegated_task(
        task,
        review_input,
        settings=_settings(),
        provider=OpenAICompatibleAdapter(_settings(), transport=ScriptedTransport([])),
        connection=MagicMock(),
        approved_backfill_request=mock_request,
    )

    assert report.status == "completed"
    assert len(report.execution_receipts) == 1
    receipt = report.execution_receipts[0]
    assert receipt.action_type == "backfill"
    assert receipt.success is True
    assert receipt.approval_id == "app_123"
    assert receipt.revalidated is True
