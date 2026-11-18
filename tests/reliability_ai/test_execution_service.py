"""Tests for delegated execution, recovery guards, and reporting."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock

import duckdb
import pytest

from hmda_reliability.data_platform.duckdb import DuckDBConnectionManager
from hmda_reliability.hmda_data import (
    load_hmda_loans_partition,
    partition_content_identity,
)
from hmda_reliability.reliability import (
    Approval,
    ApprovalStatus,
    ApprovedBackfillRequest,
    ApprovedSchemaRecoveryRequest,
    BackfillValidationResult,
    ProfileSnapshotRequest,
    RecoveryProposal,
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
            return TransportResponse(
                content='{"findings":[],"hypotheses":[],"uncertainties":[]}'
            )
        return self.responses.pop(0)


def _bound_request(
    material: NullSpikeReviewMaterial, *, schema: bool = False
) -> MagicMock:
    incident = material.detection.incident
    request = MagicMock(
        spec=ApprovedSchemaRecoveryRequest if schema else ApprovedBackfillRequest
    )
    request.approval = MagicMock(
        approval_id="schema-approval" if schema else "backfill-approval",
        incident_id=incident.incident_id,
    )
    request.proposal = MagicMock(
        proposal_id="schema-proposal" if schema else "backfill-proposal",
        incident_id=incident.incident_id,
        incident_type=incident.incident_type,
        table_name=incident.asset_name,
        source_year=int(incident.partition),
        observation_partition=incident.partition,
    )
    request.table_name = incident.asset_name
    request.source_year = int(incident.partition)
    request.profile_request = MagicMock(
        asset_name=incident.asset_name,
        table_name=incident.asset_name,
        partition=incident.partition,
    )
    return request


@pytest.mark.parametrize(
    "conflict", ["incident", "target", "partition", "both", "snapshot"]
)
def test_delegated_task_rejects_conflicting_inputs_before_investigation(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    conflict: str,
) -> None:
    from hmda_reliability.reliability_ai.execution import service

    material = null_spike_review_material
    request = _bound_request(material)
    if conflict == "incident":
        request.proposal.incident_id = "other-incident"
    elif conflict == "target":
        request.proposal.table_name = "raw.other"
    elif conflict == "partition":
        request.proposal.source_year = 2024
    investigate = MagicMock()
    recover = MagicMock()
    monkeypatch.setattr(service, "investigate_incident", investigate)
    monkeypatch.setattr(service, "execute_approved_backfill", recover)
    report = execute_delegated_task(
        TaskEnvelope(
            task_id="conflict",
            requester="human",
            recipient="human",
            goal="recover",
            allowed_actions=("execute_approved_backfill",),
            snapshot_refs=("other-snapshot",) if conflict == "snapshot" else (),
        ),
        AgenticReviewInput(
            incident=material.detection.incident,
            evidence=[material.detection.evidence],
            draft=material.draft,
            project_revision="binding-regression",
        ),
        settings=_settings(),
        connection=object(),
        approved_backfill_request=request,
        approved_schema_recovery_request=(
            _bound_request(material, schema=True) if conflict == "both" else None
        ),
        artifact_root=tmp_path,
    )
    assert report.status == "blocked"
    assert report.investigation is None
    assert report.blocked_or_unknown
    assert not report.execution_receipts
    investigate.assert_not_called()
    recover.assert_not_called()


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
        [
            TransportResponse(
                content='{"findings":[],"hypotheses":[],"uncertainties":[]}'
            )
        ]
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
    mock_request = _bound_request(material)
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
    report = execute_delegated_task(
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
    assert report.status == "failed"
    assert report.investigation is not None
    assert report.investigation.failure_code == "tool_not_allowed"
    assert report.execution_receipts == ()


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
        approved_backfill_request=_bound_request(material),
    )
    assert report.status == "failed"
    assert report.investigation is not None
    assert report.investigation.failure_code == "provider_connection_error"
    assert report.blocked_or_unknown
    assert not report.execution_receipts
    recover.assert_not_called()


@pytest.mark.parametrize(
    ("mutation_state", "reconciliation_action", "expected_status"),
    [
        (None, "resume_verification", "failed"),
        ("partition_changed", "resume_verification", "partial"),
        (
            "diverged_after_profile_failure",
            "request_new_validation_and_approval",
            "partial",
        ),
    ],
)
def test_post_mutation_failure_preserves_reconciliation_evidence(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation_state: str | None,
    reconciliation_action: str,
    expected_status: str,
) -> None:
    from hmda_reliability.reliability_ai.execution import service

    material = null_spike_review_material
    request = _bound_request(material)
    request.approval.approval_id = "approved"
    request.proposal.proposal_id = "proposal"

    def fail_recovery(*args: object) -> None:
        raise BackfillValidationError(
            "verification failed after commit",
            mutation_state=mutation_state,
            reconciliation_action=reconciliation_action,
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
    assert receipt.reconciliation_action == reconciliation_action
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
    request = _bound_request(material, schema=True)

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
    request = _bound_request(material, schema=True)
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
    request = _bound_request(material, schema=True)
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
    request = _bound_request(material)

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


@pytest.mark.integration
def test_delegated_task_reports_real_backfill_and_domain_approval_block(
    null_spike_review_material: NullSpikeReviewMaterial, tmp_path: Path
) -> None:
    material = null_spike_review_material
    incident = material.detection.incident
    source = tmp_path / "year_2025.csv"
    source.write_text(
        "activity_year,loan_purpose,action_taken,loan_amount,income,state_code,county_code\n"
        "2025,1,1,100000,120,CA,06001\n",
        encoding="utf-8",
    )
    with DuckDBConnectionManager() as candidate:
        load_hmda_loans_partition(candidate, [source], 2025)
        expected = partition_content_identity(candidate, source_year=2025)
    with DuckDBConnectionManager() as connection:
        before = partition_content_identity(connection, source_year=2025)
        proposal = RecoveryProposal(
            proposal_id="real-backfill",
            incident_id=incident.incident_id,
            incident_type="null_spike",
            table_name=incident.asset_name,
            source_year=2025,
            candidate_identity=expected,
            approved_before_identity=before,
            expected_after_identity=expected,
            validation_evidence_refs=("candidate-content", "candidate-dbt"),
            dbt_projection_id="dbt:candidate",
            target_actions=("overwrite_partition", "rerun_profile_snapshot"),
        )
        observed_at = datetime(2026, 11, 7, tzinfo=UTC)
        approval = Approval(
            approval_id="real-approval",
            incident_id=incident.incident_id,
            status=ApprovalStatus.APPROVED,
            requested_by="operator",
            requested_at=observed_at,
            approved_by="data-owner",
            approved_at=observed_at,
            requested_actions=proposal.target_actions,
            recovery_proposal=proposal,
        )
        request = ApprovedBackfillRequest(
            approval=approval,
            proposal=proposal,
            source_paths=(source,),
            source_year=2025,
            profile_request=ProfileSnapshotRequest(
                asset_name=incident.asset_name,
                table_name=incident.asset_name,
                partition_column="source_year",
                partition=2025,
                profile_columns=("income",),
                observed_at=observed_at,
            ),
        )
        task = TaskEnvelope(
            task_id="real-domain",
            requester="operator",
            recipient="human",
            goal="recover approved incident",
            allowed_actions=("execute_approved_backfill",),
            snapshot_refs=(material.detection.evidence.evidence_id,),
        )
        review_input = AgenticReviewInput(
            incident=incident,
            evidence=[material.detection.evidence],
            draft=material.draft,
            project_revision="real-domain-binding",
        )
        for approved, expected_status in ((False, "blocked"), (True, "completed")):
            active_request = (
                request
                if approved
                else request.model_copy(
                    update={
                        "approval": approval.model_copy(
                            update={"status": ApprovalStatus.PENDING}
                        )
                    }
                )
            )
            report = execute_delegated_task(
                task,
                review_input,
                settings=_settings(),
                provider=OpenAICompatibleAdapter(
                    _settings(), transport=ScriptedTransport([])
                ),
                connection=connection,
                approved_backfill_request=active_request,
                artifact_root=tmp_path,
            )
            assert report.status == expected_status
            assert report.task == task
            assert report.evidence_refs == tuple(incident.evidence_refs)
            actual = partition_content_identity(connection, source_year=2025)
            assert actual == (expected if approved else before)
            if approved:
                receipt = report.execution_receipts[0]
                assert receipt.success and receipt.revalidated
                assert receipt.details["actual_identity"] == expected.model_dump(
                    mode="json"
                )
                assert receipt.approval_id == approval.approval_id
            else:
                assert not report.execution_receipts

        connection.close()
        failed = execute_delegated_task(
            task,
            review_input,
            settings=_settings(),
            provider=OpenAICompatibleAdapter(
                _settings(), transport=ScriptedTransport([])
            ),
            connection=connection,
            approved_backfill_request=request,
            artifact_root=tmp_path,
        )
        assert failed.status == "failed"
        assert failed.task == task
        assert failed.evidence_refs == tuple(incident.evidence_refs)
        receipt = failed.execution_receipts[0]
        assert not receipt.success
        assert receipt.mutation_state == "not_reported"
        assert receipt.failure_code == "BackfillValidationError"
        assert receipt.approval_id == approval.approval_id
        assert receipt.proposal_id == proposal.proposal_id
