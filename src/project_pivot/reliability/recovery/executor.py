"""승인 기반 partition backfill 실행기."""

from __future__ import annotations

import duckdb

from project_pivot.hmda_data import (
    load_hmda_loans_partition,
    partition_content_identity,
)
from project_pivot.hmda_data.errors import HMDADataLoadError, HMDAStalePartitionError
from project_pivot.reliability.contracts import can_execute_risky_action
from project_pivot.reliability.errors import ApprovalGateError, BackfillValidationError
from project_pivot.reliability.profiling import create_profile_snapshot
from project_pivot.reliability.recovery.request import ApprovedBackfillRequest
from project_pivot.reliability.recovery.result import BackfillValidationResult

_REQUIRED_APPROVAL_ACTIONS = frozenset(
    {"overwrite_partition", "rerun_profile_snapshot"}
)


class ApprovalBackfillValidator:
    """Approval gate 이후 backfill과 profile validation을 수행한다."""

    def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
        self._connection = connection

    def execute(self, request: ApprovedBackfillRequest) -> BackfillValidationResult:
        """승인된 요청만 partition overwrite와 profile validation을 실행한다."""

        _ensure_approved(request)
        current_identity = partition_content_identity(
            self._connection,
            table_name=request.table_name,
            source_year=request.source_year,
            source_file=request.source_file,
        )
        if current_identity == request.proposal.expected_after_identity:
            mutation_state = "already_recovered"
            reconciliation_action = "resume_verification"
            executed_actions = ["rerun_profile_snapshot"]
        elif current_identity == request.proposal.approved_before_identity:
            mutation_state = "partition_changed"
            reconciliation_action = "overwrite_partition"
            executed_actions = ["overwrite_partition", "rerun_profile_snapshot"]
        else:
            raise ApprovalGateError(
                "recovery target이 approved before/after state와 다른 "
                "diverged state입니다."
            )
        try:
            if reconciliation_action == "overwrite_partition":
                row_count = load_hmda_loans_partition(
                    self._connection,
                    request.source_paths,
                    request.source_year,
                    source_file=request.source_file,
                    table_name=request.table_name,
                    expected_identity=request.proposal.approved_before_identity,
                )
            else:
                row_count = current_identity.row_count
            snapshot = create_profile_snapshot(
                self._connection,
                request.profile_request,
            )
        except HMDAStalePartitionError as exc:
            raise ApprovalGateError(
                "recovery target이 승인 후 변경되어 "
                "새 validation과 approval이 필요합니다."
            ) from exc
        except (HMDADataLoadError, duckdb.Error) as exc:
            msg = (
                "승인된 backfill validation 실행에 실패했습니다: "
                f"incident_id={request.approval.incident_id}, "
                f"source_year={request.source_year}"
            )
            raise BackfillValidationError(msg) from exc

        actual_identity = partition_content_identity(
            self._connection,
            table_name=request.table_name,
            source_year=request.source_year,
            source_file=request.source_file,
        )

        return BackfillValidationResult(
            approval_id=request.approval.approval_id,
            incident_id=request.approval.incident_id,
            partition=str(request.source_year),
            row_count=row_count,
            profile_snapshot=snapshot,
            approved_before_identity=request.proposal.approved_before_identity,
            expected_after_identity=request.proposal.expected_after_identity,
            actual_identity=actual_identity,
            mutation_state=mutation_state,
            reconciliation_action=reconciliation_action,
            validation_passed=(
                actual_identity == request.proposal.expected_after_identity
            ),
            executed_actions=executed_actions,
        )


def execute_approved_backfill(
    connection: duckdb.DuckDBPyConnection,
    request: ApprovedBackfillRequest,
) -> BackfillValidationResult:
    """DuckDB connection으로 승인된 backfill validation을 실행한다."""

    return ApprovalBackfillValidator(connection).execute(request)


def _ensure_approved(request: ApprovedBackfillRequest) -> None:
    if not can_execute_risky_action(request.approval):
        msg = (
            "승인되지 않은 backfill 요청입니다: "
            f"approval_id={request.approval.approval_id}, "
            f"status={request.approval.status}"
        )
        raise ApprovalGateError(msg)
    if request.approval.recovery_proposal != request.proposal:
        raise ApprovalGateError(
            "backfill approval의 recovery proposal이 일치하지 않습니다."
        )
    if request.approval.incident_id != request.proposal.incident_id:
        raise ApprovalGateError(
            "backfill approval의 incident가 proposal과 일치하지 않습니다."
        )
    missing_actions = _REQUIRED_APPROVAL_ACTIONS.difference(
        request.approval.requested_actions
    )
    if missing_actions:
        joined_actions = ", ".join(sorted(missing_actions))
        msg = f"backfill 승인에 필요한 action이 없습니다: {joined_actions}"
        raise ApprovalGateError(msg)
    proposal_missing_actions = _REQUIRED_APPROVAL_ACTIONS.difference(
        request.proposal.target_actions
    )
    if proposal_missing_actions:
        joined_actions = ", ".join(sorted(proposal_missing_actions))
        raise ApprovalGateError(
            f"recovery proposal에 필요한 action이 없습니다: {joined_actions}"
        )
