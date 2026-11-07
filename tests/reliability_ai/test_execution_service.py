"""Tests for delegated execution, recovery guards, and reporting."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import duckdb
import pytest

from hmda_reliability.reliability import (
    ApprovedBackfillRequest,
    ApprovedSchemaRecoveryRequest,
    BackfillValidationResult,
)
from hmda_reliability.reliability.errors import (
    BackfillValidationError,
    SchemaRecoveryCandidateError,
    SchemaRecoveryValidationError,
)
from hmda_reliability.reliability_ai import (
    AgenticReviewInput,
    TaskEnvelope,
    execute_delegated_task,
)
from hmda_reliability.runtime_ai.contracts import (
    ChatCompletionRequest,
    ToolCall,
    ToolCallFunction,
    TransportResponse,
)
from hmda_reliability.runtime_ai.provider import (
    OpenAICompatibleAdapter,
    ProviderUnavailableError,
)
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
        self.requests: list[ChatCompletionRequest] = []

    def create(self, request: ChatCompletionRequest) -> TransportResponse:
        self.requests.append(request)
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


@pytest.mark.parametrize("freshness_validated", [None, True, False])
def test_delegated_task_preserves_backfill_validation_outcome(
    null_spike_review_material: NullSpikeReviewMaterial,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    freshness_validated: bool | None,
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
    mock_request.proposal.proposal_id = "proposal_123"

    # Mock execute_approved_backfill
    fake_val_result = MagicMock(spec=BackfillValidationResult)
    fake_val_result.validation_passed = True
    fake_val_result.freshness_validation_passed = freshness_validated
    fake_val_result.mutation_state = "partition_replaced"
    fake_val_result.reconciliation_action = "overwrite_partition"
    fake_val_result.approved_before_identity = "hash_before"
    fake_val_result.actual_identity = "hash_after"
    fake_val_result.row_count = 100
    fake_val_result.model_dump.return_value = {
        "row_count": 100,
        "freshness_validation_passed": freshness_validated,
        "actual_freshness": {"freshness_status": "unavailable"},
    }

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
        artifact_root=tmp_path,
    )

    assert report.status == ("partial" if freshness_validated is False else "completed")
    assert len(report.execution_receipts) == 1
    receipt = report.execution_receipts[0]
    assert receipt.action_type == "backfill"
    assert receipt.success is (freshness_validated is not False)
    assert receipt.approval_id == "app_123"
    assert receipt.revalidated is (freshness_validated is not False)
    assert receipt.details["freshness_validation_passed"] is freshness_validated
    assert receipt.details["actual_freshness"] == {"freshness_status": "unavailable"}


def test_delegated_task_enforces_empty_tool_allowlist_and_timeout(
    null_spike_review_material: NullSpikeReviewMaterial, tmp_path: Path
) -> None:
    material = null_spike_review_material
    transport = ScriptedTransport(
        [
            TransportResponse(
                content="",
                tool_calls=(
                    ToolCall(
                        id="forbidden",
                        function=ToolCallFunction(
                            name="get_incident_evidence",
                            arguments='{"evidence_id":"x"}',
                        ),
                    ),
                ),
            )
        ]
    )
    execute_delegated_task(
        TaskEnvelope(
            task_id="restricted",
            requester="human",
            recipient="human",
            goal="read nothing",
            allowed_tools=(),
            workflow_budget_seconds=0.001,
        ),
        AgenticReviewInput(
            incident=material.detection.incident,
            evidence=[material.detection.evidence],
            draft=material.draft,
            project_revision="limit-regression",
        ),
        settings=_settings(),
        provider=OpenAICompatibleAdapter(_settings(), transport=transport),
        artifact_root=tmp_path,
        clock=lambda: 0.0,
    )
    assert len(transport.requests) == 1
    assert transport.requests[0].tools is None
    assert transport.requests[0].tool_choice == "none"
    assert transport.requests[0].timeout is not None
    assert transport.requests[0].timeout.read <= 0.001


def test_provider_failure_is_not_reported_as_completed(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from hmda_reliability.reliability_ai.execution import service

    material = null_spike_review_material
    recover = MagicMock()
    monkeypatch.setattr(service, "execute_approved_backfill", recover)
    provider = MagicMock(spec=OpenAICompatibleAdapter)
    provider.invoke.side_effect = ProviderUnavailableError(
        failure_code="provider_connection_error", attempt_count=1, latency_ms=0
    )
    report = execute_delegated_task(
        TaskEnvelope(
            task_id="failed",
            requester="human",
            recipient="human",
            goal="read",
            allowed_actions=("execute_approved_backfill",),
        ),
        AgenticReviewInput(
            incident=material.detection.incident,
            evidence=[material.detection.evidence],
            draft=material.draft,
            project_revision="failure-regression",
        ),
        settings=_settings(),
        provider=provider,
        artifact_root=tmp_path,
        connection=object(),
        approved_backfill_request=MagicMock(spec=ApprovedBackfillRequest),
    )
    assert report.status == "failed"
    assert report.investigation is not None
    assert report.investigation.failure_code == "provider_connection_error"
    assert report.blocked_or_unknown
    assert not report.execution_receipts
    recover.assert_not_called()


@pytest.mark.parametrize(
    ("mutation_state", "expected_status"),
    [(None, "failed"), ("partition_changed", "partial")],
)
def test_post_mutation_failure_preserves_reconciliation_evidence(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation_state: str | None,
    expected_status: str,
) -> None:
    from hmda_reliability.reliability_ai.execution import service

    material = null_spike_review_material
    request = MagicMock(spec=ApprovedBackfillRequest)
    request.approval = MagicMock(approval_id="approved")
    request.proposal = MagicMock(proposal_id="proposal")

    def fail_recovery(*args: object) -> None:
        raise BackfillValidationError(
            "verification failed after commit",
            mutation_state=mutation_state,
            reconciliation_action="resume_verification",
            context={"actual_identity": {"digest": "after"}},
        )

    monkeypatch.setattr(service, "execute_approved_backfill", fail_recovery)
    report = execute_delegated_task(
        TaskEnvelope(
            task_id="partial",
            requester="human",
            recipient="supervisor",
            goal="recover",
            allowed_actions=("execute_approved_backfill",),
        ),
        AgenticReviewInput(
            incident=material.detection.incident,
            evidence=[material.detection.evidence],
            draft=material.draft,
            project_revision="failure-regression",
        ),
        settings=_settings(),
        provider=OpenAICompatibleAdapter(_settings(), transport=ScriptedTransport([])),
        connection=object(),
        approved_backfill_request=request,
        artifact_root=tmp_path,
    )
    assert report.status == expected_status
    receipt = report.execution_receipts[0]
    assert receipt.success is False
    assert receipt.revalidated is False
    assert receipt.mutation_state == (mutation_state or "not_reported")
    assert receipt.reconciliation_action == "resume_verification"
    assert receipt.details["context"] == {"actual_identity": {"digest": "after"}}


@pytest.mark.parametrize(
    ("mutation_state", "expected_status"),
    [("rolled_back", "failed"), ("table_replaced", "partial")],
)
def test_schema_recovery_failure_preserves_stage_and_mutation_state(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation_state: str,
    expected_status: str,
) -> None:
    from hmda_reliability.reliability_ai.execution import service

    material = null_spike_review_material
    request = MagicMock(spec=ApprovedSchemaRecoveryRequest)
    request.approval = MagicMock(approval_id="schema-approval")
    request.proposal = MagicMock(proposal_id="schema-proposal")

    def fail_recovery(*args: object) -> None:
        raise SchemaRecoveryValidationError(
            "schema verification failed",
            failure_stage="verification",
            mutation_state=mutation_state,
            reconciliation_action="resume_verification",
            context={"actual_state": {"digest": "after"}},
        )

    monkeypatch.setattr(service, "execute_approved_schema_recovery", fail_recovery)
    report = execute_delegated_task(
        TaskEnvelope(
            task_id="schema-failure",
            requester="human",
            recipient="supervisor",
            goal="recover schema",
            allowed_actions=("execute_approved_schema_recovery",),
        ),
        AgenticReviewInput(
            incident=material.detection.incident,
            evidence=[material.detection.evidence],
            draft=material.draft,
            project_revision="failure-regression",
        ),
        settings=_settings(),
        provider=OpenAICompatibleAdapter(_settings(), transport=ScriptedTransport([])),
        approved_schema_recovery_request=request,
        artifact_root=tmp_path,
    )
    assert report.status == expected_status
    receipt = report.execution_receipts[0]
    assert receipt.success is False
    assert receipt.mutation_state == mutation_state
    assert receipt.proposal_id == "schema-proposal"
    assert receipt.details["failure_stage"] == "verification"
    assert receipt.details["context"] == {"actual_state": {"digest": "after"}}


@pytest.mark.parametrize("failure_type", ["candidate", "os"])
def test_schema_preflight_failure_preserves_known_or_unknown_mutation_state(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_type: str,
) -> None:
    from hmda_reliability.reliability_ai.execution import service

    material = null_spike_review_material
    request = MagicMock(spec=ApprovedSchemaRecoveryRequest)
    request.approval = MagicMock(approval_id="schema-approval")
    request.proposal = MagicMock(proposal_id="schema-proposal")
    context = {"candidate_database_path": str(tmp_path / "missing.duckdb")}

    def fail_recovery(*args: object) -> None:
        if failure_type == "os":
            raise OSError("no staging space")
        raise SchemaRecoveryCandidateError("candidate unavailable", context=context)

    monkeypatch.setattr(service, "execute_approved_schema_recovery", fail_recovery)
    report = execute_delegated_task(
        TaskEnvelope(
            task_id="schema-candidate-failure",
            requester="human",
            recipient="supervisor",
            goal="recover schema",
            allowed_actions=("execute_approved_schema_recovery",),
        ),
        AgenticReviewInput(
            incident=material.detection.incident,
            evidence=[material.detection.evidence],
            draft=material.draft,
            project_revision="failure-regression",
        ),
        settings=_settings(),
        provider=OpenAICompatibleAdapter(_settings(), transport=ScriptedTransport([])),
        approved_schema_recovery_request=request,
        artifact_root=tmp_path,
    )
    assert report.status == "failed"
    receipt = report.execution_receipts[0]
    assert receipt.approval_id == "schema-approval"
    assert receipt.proposal_id == "schema-proposal"
    assert report.investigation is not None
    if failure_type == "candidate":
        assert receipt.mutation_state == "not_started"
        assert receipt.failure_code == "SchemaRecoveryCandidateError"
        assert receipt.details["failure_stage"] == "before_target_mutation"
        assert receipt.details["context"] == context
    else:
        assert receipt.mutation_state == "not_reported"
        assert receipt.failure_code == "OSError"
        assert receipt.details["failure_stage"] is None
        assert receipt.details["failure_message"] == "no staging space"
        assert any("실제 상태" in request for request in report.next_requests)


def test_schema_recovery_report_preserves_profile_evidence(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from hmda_reliability.reliability_ai.execution import service

    material = null_spike_review_material
    request = MagicMock(spec=ApprovedSchemaRecoveryRequest)
    request.approval = MagicMock(approval_id="schema-approval")
    request.proposal = MagicMock(proposal_id="schema-proposal")
    result = MagicMock(
        validation_passed=True,
        mutation_state="already_restored",
        reconciliation_action="resume_verification",
        approved_before_state="before",
        actual_state="after",
    )
    evidence = {
        "profile_snapshot": {"snapshot_id": "profile-evidence"},
        "executed_actions": ["rerun_profile_snapshot"],
    }
    result.model_dump.return_value = evidence
    monkeypatch.setattr(service, "execute_approved_schema_recovery", lambda _: result)
    report = execute_delegated_task(
        TaskEnvelope(
            task_id="schema-evidence",
            requester="human",
            recipient="supervisor",
            goal="recover schema",
            allowed_actions=("execute_approved_schema_recovery",),
        ),
        AgenticReviewInput(
            incident=material.detection.incident,
            evidence=[material.detection.evidence],
            draft=material.draft,
            project_revision="profile-evidence-regression",
        ),
        settings=_settings(),
        provider=OpenAICompatibleAdapter(_settings(), transport=ScriptedTransport([])),
        approved_schema_recovery_request=request,
        artifact_root=tmp_path,
    )
    assert report.status == "completed"
    assert report.execution_receipts[0].details == evidence


def test_backfill_database_error_preserves_unknown_state_and_approval(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from hmda_reliability.reliability_ai.execution import service

    material = null_spike_review_material
    request = MagicMock(spec=ApprovedBackfillRequest)
    request.approval = MagicMock(approval_id="backfill-approval")
    request.proposal = MagicMock(proposal_id="backfill-proposal")

    def fail_recovery(*args: object) -> None:
        raise duckdb.IOException("final identity read failed")

    monkeypatch.setattr(service, "execute_approved_backfill", fail_recovery)
    report = execute_delegated_task(
        TaskEnvelope(
            task_id="backfill-io-failure",
            requester="human",
            recipient="human",
            goal="recover partition",
            allowed_actions=("execute_approved_backfill",),
        ),
        AgenticReviewInput(
            incident=material.detection.incident,
            evidence=[material.detection.evidence],
            draft=material.draft,
            project_revision="io-failure-regression",
        ),
        settings=_settings(),
        provider=OpenAICompatibleAdapter(_settings(), transport=ScriptedTransport([])),
        connection=object(),
        approved_backfill_request=request,
        artifact_root=tmp_path,
    )
    assert report.status == "failed"
    assert report.investigation is not None
    receipt = report.execution_receipts[0]
    assert receipt.mutation_state == "not_reported"
    assert receipt.approval_id == "backfill-approval"
    assert receipt.proposal_id == "backfill-proposal"
    assert receipt.failure_code == "IOException"
    assert any("실제 상태" in request for request in report.next_requests)
