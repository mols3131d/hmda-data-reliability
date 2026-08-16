"""Schema recovery table-wide approval contract tests."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

import project_pivot.reliability as reliability
from project_pivot.hmda_data import PartitionContentIdentity
from project_pivot.reliability import (
    ApprovalStatus,
    FreshnessMeasurementStatus,
    ProfileSnapshot,
    TableStateIdentity,
)

pytestmark = pytest.mark.unit


def _schema_contract_api() -> tuple[type[Any], type[Any], type[Any], type[Any]]:
    proposal_type = getattr(reliability, "SchemaRecoveryProposal", None)
    approval_type = getattr(reliability, "SchemaRecoveryApproval", None)
    request_type = getattr(reliability, "ApprovedSchemaRecoveryRequest", None)
    result_type = getattr(reliability, "SchemaRecoveryValidationResult", None)
    assert proposal_type is not None, "SchemaRecoveryProposal API가 필요합니다."
    assert approval_type is not None, "SchemaRecoveryApproval API가 필요합니다."
    assert request_type is not None, "ApprovedSchemaRecoveryRequest API가 필요합니다."
    assert result_type is not None, "SchemaRecoveryValidationResult API가 필요합니다."
    return proposal_type, approval_type, request_type, result_type


def test_schema_recovery_proposal_separates_observation_from_table_mutation() -> None:
    """Incident partition은 evidence이고 mutation scope는 exact table state다."""

    proposal_type, _, _, _ = _schema_contract_api()

    proposal = _proposal(proposal_type)

    assert proposal.observation_partition == "2025"
    assert proposal.table_name == "raw.hmda_loans"
    assert not hasattr(proposal, "source_year")

    with pytest.raises(ValidationError):
        proposal_type(
            **_proposal_values(),
            source_year=2025,
        )


def test_schema_recovery_proposal_rejects_partition_identity() -> None:
    """Partition identity는 table-wide approval state를 대신할 수 없다."""

    proposal_type, _, _, _ = _schema_contract_api()
    partition_identity = PartitionContentIdentity(
        table_name="raw.hmda_loans",
        source_year=2025,
        row_count=1,
        digest="sha256-v1:partition",
    )

    with pytest.raises(ValidationError):
        proposal_type(
            **{
                **_proposal_values(),
                "candidate_state": partition_identity,
                "approved_before_state": partition_identity,
                "expected_after_state": partition_identity,
            }
        )


@pytest.mark.parametrize(
    "case",
    ["missing-replace-table", "candidate-after-mismatch"],
    ids=("missing-replace-table", "candidate-after-mismatch"),
)
def test_schema_recovery_proposal_requires_exact_state_and_actions(
    case: str,
) -> None:
    """Candidate/after state와 required table action은 exact해야 한다."""

    proposal_type, _, _, _ = _schema_contract_api()
    updates = (
        {"target_actions": ("rerun_profile_snapshot",)}
        if case == "missing-replace-table"
        else {"candidate_state": _state("candidate-changed")}
    )

    with pytest.raises(ValidationError):
        proposal_type(**{**_proposal_values(), **updates})


def test_schema_recovery_approval_and_request_bind_exact_proposal() -> None:
    """Approval action과 execution request는 exact proposal을 재사용한다."""

    proposal_type, approval_type, request_type, _ = _schema_contract_api()
    proposal = _proposal(proposal_type)
    approved_at = datetime(2026, 8, 16, 0, 0, tzinfo=UTC)
    approval = approval_type(
        approval_id="approval_schema_drift_2025",
        incident_id=proposal.incident_id,
        status=ApprovalStatus.APPROVED,
        requested_by="data-platform",
        requested_at=approved_at,
        approved_by="data-owner",
        approved_at=approved_at,
        requested_actions=proposal.target_actions,
        recovery_proposal=proposal,
    )

    request = request_type(
        approval=approval,
        proposal=proposal,
        target_database_path=Path("target.duckdb"),
        candidate_database_path=Path("candidate.duckdb"),
        profile_request=_profile_request(),
    )

    assert request.proposal == approval.recovery_proposal
    with pytest.raises(ValidationError):
        request_type(
            approval=approval,
            proposal=proposal.model_copy(update={"dbt_projection_id": "dbt:other"}),
            target_database_path=Path("target.duckdb"),
            candidate_database_path=Path("candidate.duckdb"),
            profile_request=_profile_request(),
        )


def test_schema_recovery_approval_rejects_missing_replace_table_action() -> None:
    """Approval은 proposal의 complete table mutation action을 줄일 수 없다."""

    proposal_type, approval_type, _, _ = _schema_contract_api()
    proposal = _proposal(proposal_type)
    approved_at = datetime(2026, 8, 16, 0, 0, tzinfo=UTC)

    with pytest.raises(ValidationError):
        approval_type(
            approval_id="approval_schema_drift_2025",
            incident_id=proposal.incident_id,
            status=ApprovalStatus.APPROVED,
            requested_by="data-platform",
            requested_at=approved_at,
            approved_by="data-owner",
            approved_at=approved_at,
            requested_actions=("rerun_profile_snapshot",),
            recovery_proposal=proposal,
        )


def test_schema_recovery_result_rejects_false_exact_validation() -> None:
    """Actual table state가 expected after와 다르면 success result가 아니다."""

    _, _, _, result_type = _schema_contract_api()
    expected = _state("expected")

    with pytest.raises(ValidationError):
        result_type(
            approval_id="approval_schema_drift_2025",
            incident_id="inc_schema_drift_2025",
            table_name="raw.hmda_loans",
            profile_snapshot=_profile_snapshot(),
            approved_before_state=_state("before"),
            expected_after_state=expected,
            actual_state=_state("different"),
            mutation_state="table_replaced",
            reconciliation_action="replace_table",
            validation_passed=True,
            executed_actions=("replace_table", "rerun_profile_snapshot"),
        )


def test_schema_recovery_result_preserves_exact_table_validation() -> None:
    """Valid result는 expected table state와 aligned profile evidence를 보존한다."""

    _, _, _, result_type = _schema_contract_api()
    expected = _state("expected")

    result = result_type(
        approval_id="approval_schema_drift_2025",
        incident_id="inc_schema_drift_2025",
        table_name="raw.hmda_loans",
        profile_snapshot=_profile_snapshot(),
        approved_before_state=_state("before"),
        expected_after_state=expected,
        actual_state=expected,
        mutation_state="table_replaced",
        reconciliation_action="replace_table",
        validation_passed=True,
        executed_actions=("replace_table", "rerun_profile_snapshot"),
    )

    assert result.actual_state == expected
    assert result.profile_snapshot.partition == "2025"


def _proposal(proposal_type: type[Any]) -> Any:
    return proposal_type(**_proposal_values())


def _proposal_values() -> dict[str, object]:
    expected = _state("expected")
    return {
        "proposal_id": "schema_recovery_2025",
        "incident_id": "inc_schema_drift_2025",
        "observation_partition": "2025",
        "table_name": "raw.hmda_loans",
        "candidate_state": expected,
        "approved_before_state": _state("before"),
        "expected_after_state": expected,
        "validation_evidence_refs": ("candidate-state", "candidate-dbt"),
        "dbt_projection_id": "dbt:candidate",
        "target_actions": ("replace_table", "rerun_profile_snapshot"),
    }


def _state(digest: str) -> TableStateIdentity:
    return TableStateIdentity(
        table_name="raw.hmda_loans",
        schema_hash="sha256:schema",
        row_count=1,
        partition_identities=(
            PartitionContentIdentity(
                table_name="raw.hmda_loans",
                source_year=2025,
                row_count=1,
                digest=f"sha256-v1:{digest}",
            ),
        ),
    )


def _profile_snapshot() -> ProfileSnapshot:
    observed_at = datetime(2026, 8, 16, 0, 0, tzinfo=UTC)
    return ProfileSnapshot(
        snapshot_id="profile_raw_hmda_loans_2025",
        asset_name="raw.hmda_loans",
        partition="2025",
        observed_at=observed_at,
        row_count=1,
        schema_hash="sha256:schema",
        freshness_at=observed_at,
        freshness_status=FreshnessMeasurementStatus.MEASURED,
    )


def _profile_request() -> reliability.ProfileSnapshotRequest:
    observed_at = datetime(2026, 8, 16, 0, 0, tzinfo=UTC)
    return reliability.ProfileSnapshotRequest(
        asset_name="raw.hmda_loans",
        table_name="raw.hmda_loans",
        partition_column="source_year",
        partition=2025,
        profile_columns=("loan_amount",),
        observed_at=observed_at,
    )
