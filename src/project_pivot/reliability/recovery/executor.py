"""승인 기반 partition backfill 실행기."""

from __future__ import annotations

import duckdb

from project_pivot.reliability.contracts import can_execute_risky_action
from project_pivot.reliability.errors import ApprovalGateError, BackfillValidationError
from project_pivot.reliability.profiling import create_profile_snapshot
from project_pivot.reliability.recovery.request import ApprovedBackfillRequest
from project_pivot.reliability.recovery.result import BackfillValidationResult
from project_pivot.taxi_data import load_yellow_tripdata_partition
from project_pivot.taxi_data.errors import TaxiDataLoadError


class ApprovalBackfillValidator:
    """Approval gate 이후 backfill과 profile validation을 수행한다."""

    def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
        self._connection = connection

    def execute(self, request: ApprovedBackfillRequest) -> BackfillValidationResult:
        """승인된 요청만 partition overwrite와 profile validation을 실행한다."""

        _ensure_approved(request)
        try:
            row_count = load_yellow_tripdata_partition(
                self._connection,
                request.parquet_paths,
                request.partition_date,
                table_name=request.table_name,
            )
            snapshot = create_profile_snapshot(
                self._connection,
                request.profile_request,
            )
        except (TaxiDataLoadError, duckdb.Error) as exc:
            msg = (
                "승인된 backfill validation 실행에 실패했습니다: "
                f"incident_id={request.approval.incident_id}, "
                f"partition={request.partition_date.isoformat()}"
            )
            raise BackfillValidationError(msg) from exc

        return BackfillValidationResult(
            approval_id=request.approval.approval_id,
            incident_id=request.approval.incident_id,
            partition=request.partition_date.isoformat(),
            row_count=row_count,
            profile_snapshot=snapshot,
            validation_passed=snapshot.row_count == row_count,
            executed_actions=[
                "overwrite_partition",
                "rerun_profile_snapshot",
            ],
        )


def execute_approved_backfill(
    connection: duckdb.DuckDBPyConnection,
    request: ApprovedBackfillRequest,
) -> BackfillValidationResult:
    """DuckDB connection으로 승인된 backfill validation을 실행한다."""

    return ApprovalBackfillValidator(connection).execute(request)


def _ensure_approved(request: ApprovedBackfillRequest) -> None:
    if can_execute_risky_action(request.approval):
        return
    msg = (
        "승인되지 않은 backfill 요청입니다: "
        f"approval_id={request.approval.approval_id}, "
        f"status={request.approval.status}"
    )
    raise ApprovalGateError(msg)
