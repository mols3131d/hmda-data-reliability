"""외부 승인된 테이블 스키마 복구 실행 및 검증 모듈."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import duckdb
from pydantic import ValidationError

from hmda_reliability.data_platform.duckdb import (
    DuckDBConnectionManager,
    DuckDBMutationLockError,
    database_mutation_lock,
)
from hmda_reliability.data_platform.sql import qualify_table_name, quote_string_literal
from hmda_reliability.logger import get_logger
from hmda_reliability.reliability.errors import (
    ApprovalGateError,
    ProfileSnapshotError,
    SchemaRecoveryValidationError,
    TableStateIdentityError,
)
from hmda_reliability.reliability.profiling import (
    create_profile_snapshot,
    create_table_state_identity,
)
from hmda_reliability.reliability.recovery.schema_candidate import (
    stage_approved_schema_recovery_candidate,
)
from hmda_reliability.reliability.recovery.schema_request import (
    ApprovedSchemaRecoveryRequest,
)
from hmda_reliability.reliability.recovery.schema_result import (
    SchemaRecoveryValidationResult,
)

_LOGGER = get_logger(__name__)


def execute_approved_schema_recovery(
    request: ApprovedSchemaRecoveryRequest,
) -> SchemaRecoveryValidationResult:
    """승인된 정확한 테이블 상태를 복구하거나 재현(replay) 시 검증을 재개한다."""

    validated_request = _ensure_approved_schema_recovery(request)
    proposal = validated_request.proposal
    with TemporaryDirectory() as temporary_directory:
        staged_candidate = stage_approved_schema_recovery_candidate(
            candidate_database_path=validated_request.candidate_database_path,
            approved_candidate_state=proposal.candidate_state,
            staging_directory=Path(temporary_directory),
        )
        try:
            with (
                database_mutation_lock(validated_request.target_database_path),
                DuckDBConnectionManager(
                    validated_request.target_database_path
                ) as connection,
            ):
                current_state = create_table_state_identity(
                    connection,
                    proposal.table_name,
                )
                if current_state == proposal.expected_after_state:
                    profile_snapshot = create_profile_snapshot(
                        connection,
                        validated_request.profile_request,
                    )
                    return SchemaRecoveryValidationResult(
                        approval_id=validated_request.approval.approval_id,
                        incident_id=validated_request.approval.incident_id,
                        table_name=proposal.table_name,
                        profile_snapshot=profile_snapshot,
                        approved_before_state=proposal.approved_before_state,
                        expected_after_state=proposal.expected_after_state,
                        actual_state=current_state,
                        mutation_state="already_restored",
                        reconciliation_action="resume_verification",
                        validation_passed=True,
                        executed_actions=("rerun_profile_snapshot",),
                    )
                if current_state != proposal.approved_before_state:
                    raise SchemaRecoveryValidationError(
                        "schema recovery target이 approved before/after state와 "
                        "다른 diverged state입니다.",
                        failure_stage="before_target_mutation",
                        reconciliation_action=("request_new_validation_and_approval"),
                        context={
                            "current_state": current_state.model_dump(mode="json"),
                            "approved_before_state": (
                                proposal.approved_before_state.model_dump(mode="json")
                            ),
                            "expected_after_state": (
                                proposal.expected_after_state.model_dump(mode="json")
                            ),
                        },
                    )
                return _replace_table(
                    connection,
                    validated_request,
                    staged_candidate.artifact_path,
                )
        except SchemaRecoveryValidationError:
            raise
        except DuckDBMutationLockError as exc:
            raise SchemaRecoveryValidationError(
                "schema recovery target mutation lock을 획득할 수 없습니다.",
                failure_stage="before_target_mutation",
                reconciliation_action="retry_same_approval",
                context={
                    "target_database_path": str(validated_request.target_database_path)
                },
            ) from exc
        except (duckdb.Error, ProfileSnapshotError, TableStateIdentityError) as exc:
            raise SchemaRecoveryValidationError(
                "schema recovery target state를 검증할 수 없습니다.",
                failure_stage="before_target_mutation",
                reconciliation_action="request_new_validation_and_approval",
                context={"table_name": proposal.table_name},
            ) from exc


def _ensure_approved_schema_recovery(
    request: ApprovedSchemaRecoveryRequest,
) -> ApprovedSchemaRecoveryRequest:
    try:
        return ApprovedSchemaRecoveryRequest.model_validate(
            request.model_dump(warnings=False)
        )
    except ValidationError as exc:
        raise ApprovalGateError(
            "schema recovery approval 또는 proposal contract가 일치하지 않습니다."
        ) from exc


def _replace_table(
    connection: duckdb.DuckDBPyConnection,
    request: ApprovedSchemaRecoveryRequest,
    staged_artifact_path: Path,
) -> SchemaRecoveryValidationResult:
    proposal = request.proposal
    transaction_started = False
    try:
        connection.execute("BEGIN TRANSACTION")
        transaction_started = True
        connection.execute(
            f"CREATE OR REPLACE TABLE {qualify_table_name(proposal.table_name)} AS "
            f"SELECT * FROM read_parquet("
            f"{quote_string_literal(staged_artifact_path.as_posix())})"
        )
        actual_state = create_table_state_identity(connection, proposal.table_name)
        if actual_state != proposal.expected_after_state:
            raise SchemaRecoveryValidationError(
                "schema recovery replacement state가 expected after state와 다릅니다.",
                failure_stage="in_target_transaction",
                mutation_state="rolled_back",
                reconciliation_action="retry_same_approval",
                context={
                    "actual_state": actual_state.model_dump(mode="json"),
                    "expected_after_state": proposal.expected_after_state.model_dump(
                        mode="json"
                    ),
                },
            )
        profile_snapshot = create_profile_snapshot(connection, request.profile_request)
        connection.execute("COMMIT")
        transaction_started = False
        _LOGGER.info(
            "schema recovery table 교체 완료",
            extra={
                "table_name": proposal.table_name,
                "approval_id": request.approval.approval_id,
                "incident_id": request.approval.incident_id,
            },
        )
    except SchemaRecoveryValidationError:
        if transaction_started:
            connection.execute("ROLLBACK")
        raise
    except (duckdb.Error, ProfileSnapshotError, TableStateIdentityError) as exc:
        if transaction_started:
            connection.execute("ROLLBACK")
        raise SchemaRecoveryValidationError(
            "schema recovery transaction을 완료할 수 없습니다.",
            failure_stage="in_target_transaction",
            mutation_state="rolled_back",
            reconciliation_action="retry_same_approval",
            context={"table_name": proposal.table_name},
        ) from exc
    return SchemaRecoveryValidationResult(
        approval_id=request.approval.approval_id,
        incident_id=request.approval.incident_id,
        table_name=proposal.table_name,
        profile_snapshot=profile_snapshot,
        approved_before_state=proposal.approved_before_state,
        expected_after_state=proposal.expected_after_state,
        actual_state=actual_state,
        mutation_state="table_replaced",
        reconciliation_action="replace_table",
        validation_passed=True,
        executed_actions=("replace_table", "rerun_profile_snapshot"),
    )
