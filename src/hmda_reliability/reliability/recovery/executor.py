"""Execute externally approved recovery and verify exact partition content identity."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

import duckdb
from pydantic import ValidationError

from project_pivot.data_platform.sql import quote_string_literal
from project_pivot.hmda_data import (
    PartitionContentIdentity,
    load_hmda_loans_partition,
    partition_content_identity,
    partition_max_ingested_at,
)
from project_pivot.hmda_data.errors import HMDADataLoadError, HMDAStalePartitionError
from project_pivot.logger import get_logger
from project_pivot.reliability.contracts import (
    Approval,
    FreshnessMeasurementStatus,
    FreshnessObservation,
    FreshnessRecoveryBinding,
    ProfileSnapshot,
    RecoveryProposal,
    can_execute_risky_action,
)
from project_pivot.reliability.errors import (
    ApprovalGateError,
    BackfillValidationError,
    ProfileSnapshotError,
)
from project_pivot.reliability.profiling import create_profile_snapshot
from project_pivot.reliability.recovery.request import ApprovedBackfillRequest
from project_pivot.reliability.recovery.result import BackfillValidationResult

_LOGGER = get_logger(__name__)
_REQUIRED_APPROVAL_ACTIONS = frozenset(
    {"overwrite_partition", "rerun_profile_snapshot"}
)


class ApprovalBackfillValidator:
    """Enforce exact approval scope before candidate access or target mutation."""

    def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
        self._connection = connection

    def execute(self, request: ApprovedBackfillRequest) -> BackfillValidationResult:
        """Recover approved before-state or verify the exact after-state on replay."""

        # Approval scope is validated before the candidate source is read.
        approval, proposal = _ensure_approved(request)
        try:
            with TemporaryDirectory() as temporary_directory:
                staged_source_path = _stage_approved_candidate_source(
                    request,
                    Path(temporary_directory),
                )
                current_identity = partition_content_identity(
                    self._connection,
                    table_name=request.table_name,
                    source_year=request.source_year,
                    source_file=request.source_file,
                )
                binding = proposal.freshness_binding
                if binding is None:
                    mutation_state, reconciliation_action, executed_actions = (
                        _reconcile_content_state(current_identity, proposal)
                    )
                else:
                    current_freshness_at = partition_max_ingested_at(
                        self._connection,
                        table_name=request.table_name,
                        source_year=request.source_year,
                        source_file=request.source_file,
                    )
                    mutation_state, reconciliation_action, executed_actions = (
                        _reconcile_freshness_state(
                            current_identity=current_identity,
                            current_freshness_at=current_freshness_at,
                            observed_at=request.profile_request.observed_at,
                            proposal=proposal,
                            binding=binding,
                        )
                    )
                if reconciliation_action == "overwrite_partition":
                    _LOGGER.info(
                        "recovery partition overwrite attempt",
                        extra={
                            "incident_id": approval.incident_id,
                            "approval_id": approval.approval_id,
                            "source_year": request.source_year,
                            "table_name": request.table_name,
                        },
                    )
                    # Keep compare-and-replace inside the loader's mutation transaction.
                    row_count = _replace_approved_partition(
                        connection=self._connection,
                        staged_source_path=staged_source_path,
                        request=request,
                        proposal=proposal,
                        binding=binding,
                    )
                else:
                    row_count = current_identity.row_count
                snapshot = create_profile_snapshot(
                    self._connection,
                    request.profile_request,
                )
        except ProfileSnapshotError as exc:
            actual_identity = partition_content_identity(
                self._connection,
                table_name=request.table_name,
                source_year=request.source_year,
                source_file=request.source_file,
            )
            actual_freshness_at = (
                partition_max_ingested_at(
                    self._connection,
                    table_name=request.table_name,
                    source_year=request.source_year,
                    source_file=request.source_file,
                )
                if proposal.freshness_binding is not None
                else None
            )
            msg = (
                "partition commit 후 profile validation에 실패했습니다: "
                f"incident_id={request.approval.incident_id}, "
                f"source_year={request.source_year}"
            )
            diverged = actual_identity != proposal.expected_after_identity or (
                proposal.freshness_binding is not None
                and actual_freshness_at
                != proposal.freshness_binding.expected_after_freshness_at
            )
            raise BackfillValidationError(
                msg,
                mutation_state=(
                    "diverged_after_profile_failure" if diverged else mutation_state
                ),
                reconciliation_action=(
                    "request_new_validation_and_approval"
                    if diverged
                    else "resume_verification"
                ),
                context={
                    "actual_identity": actual_identity.model_dump(mode="json"),
                    "expected_after_identity": (
                        proposal.expected_after_identity.model_dump(mode="json")
                    ),
                    "execution_mutation_state": mutation_state,
                    "profile_error": str(exc),
                    "actual_freshness_at": (
                        actual_freshness_at.isoformat()
                        if actual_freshness_at is not None
                        else None
                    ),
                    "expected_after_freshness_at": (
                        proposal.freshness_binding.expected_after_freshness_at.isoformat()
                        if proposal.freshness_binding is not None
                        else None
                    ),
                },
            ) from exc
        except HMDAStalePartitionError as exc:
            raise ApprovalGateError(
                "recovery target이 승인 후 변경되어 "
                "새 validation과 approval이 필요합니다."
            ) from exc
        except (HMDADataLoadError, OSError, duckdb.Error) as exc:
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
        approved_before_freshness = (
            proposal.freshness_binding.approved_before
            if proposal.freshness_binding is not None
            else None
        )
        expected_after_freshness_at = (
            proposal.freshness_binding.expected_after_freshness_at
            if proposal.freshness_binding is not None
            else None
        )
        actual_freshness = (
            _snapshot_freshness_observation(snapshot)
            if proposal.freshness_binding is not None
            else None
        )
        freshness_validation_passed = (
            _freshness_matches_binding(actual_freshness, proposal.freshness_binding)
            if actual_freshness is not None and proposal.freshness_binding is not None
            else None
        )

        return BackfillValidationResult(
            approval_id=approval.approval_id,
            incident_id=approval.incident_id,
            partition=str(request.source_year),
            row_count=row_count,
            profile_snapshot=snapshot,
            approved_before_identity=proposal.approved_before_identity,
            expected_after_identity=proposal.expected_after_identity,
            actual_identity=actual_identity,
            mutation_state=mutation_state,
            reconciliation_action=reconciliation_action,
            validation_passed=(actual_identity == proposal.expected_after_identity),
            approved_before_freshness=approved_before_freshness,
            expected_after_freshness_at=expected_after_freshness_at,
            actual_freshness=actual_freshness,
            freshness_validation_passed=freshness_validation_passed,
            executed_actions=executed_actions,
        )


def execute_approved_backfill(
    connection: duckdb.DuckDBPyConnection,
    request: ApprovedBackfillRequest,
) -> BackfillValidationResult:
    """Apply the recovery gate and return identity-based validation evidence."""

    return ApprovalBackfillValidator(connection).execute(request)


def _ensure_approved(
    request: ApprovedBackfillRequest,
) -> tuple[Approval, RecoveryProposal]:
    try:
        approval = Approval.model_validate(request.approval.model_dump(warnings=False))
        proposal = RecoveryProposal.model_validate(
            request.proposal.model_dump(warnings=False)
        )
    except ValidationError as exc:
        raise ApprovalGateError(
            "backfill approval 또는 recovery proposal contract가 유효하지 않습니다."
        ) from exc
    if not can_execute_risky_action(approval):
        msg = (
            "승인되지 않은 backfill 요청입니다: "
            f"approval_id={approval.approval_id}, "
            f"status={approval.status}"
        )
        raise ApprovalGateError(msg)
    if approval.recovery_proposal != proposal:
        raise ApprovalGateError(
            "backfill approval의 recovery proposal이 일치하지 않습니다."
        )
    if approval.incident_id != proposal.incident_id:
        raise ApprovalGateError(
            "backfill approval의 incident가 proposal과 일치하지 않습니다."
        )
    missing_actions = _REQUIRED_APPROVAL_ACTIONS.difference(approval.requested_actions)
    if missing_actions:
        joined_actions = ", ".join(sorted(missing_actions))
        msg = f"backfill 승인에 필요한 action이 없습니다: {joined_actions}"
        raise ApprovalGateError(msg)
    proposal_missing_actions = _REQUIRED_APPROVAL_ACTIONS.difference(
        proposal.target_actions
    )
    if proposal_missing_actions:
        joined_actions = ", ".join(sorted(proposal_missing_actions))
        raise ApprovalGateError(
            f"recovery proposal에 필요한 action이 없습니다: {joined_actions}"
        )
    return approval, proposal


def _stage_approved_candidate_source(
    request: ApprovedBackfillRequest,
    temporary_directory: Path,
) -> Path:
    """Materialize the approved candidate into temporary Parquet before mutation."""

    source_connection = duckdb.connect(":memory:")
    staged_source_path = temporary_directory / "approved-candidate.parquet"
    binding = request.proposal.freshness_binding
    try:
        load_hmda_loans_partition(
            source_connection,
            request.source_paths,
            request.source_year,
            source_file=request.source_file,
            table_name=request.table_name,
            preserve_source_metadata=binding is not None,
        )
        source_identity = partition_content_identity(
            source_connection,
            table_name=request.table_name,
            source_year=request.source_year,
            source_file=request.source_file,
        )
        if source_identity != request.proposal.candidate_identity:
            raise ApprovalGateError(
                "recovery source가 승인된 candidate content와 일치하지 않습니다."
            )
        if binding is not None:
            candidate_freshness_at = partition_max_ingested_at(
                source_connection,
                table_name=request.table_name,
                source_year=request.source_year,
                source_file=request.source_file,
            )
            candidate_observation = _freshness_observation(
                freshness_at=candidate_freshness_at,
                observed_at=request.profile_request.observed_at,
            )
            if candidate_freshness_at != binding.expected_after_freshness_at:
                raise ApprovalGateError(
                    "candidate freshness가 승인된 expected timestamp와 다릅니다."
                )
            if not _freshness_is_acceptable(
                candidate_observation,
                binding.max_age_minutes,
            ):
                raise ApprovalGateError(
                    "candidate freshness가 max age를 충족하지 않아 새 validation이 "
                    "필요합니다."
                )
        staged_source_literal = quote_string_literal(staged_source_path.as_posix())
        source_connection.execute(
            f"COPY {request.table_name} TO {staged_source_literal} (FORMAT PARQUET)"
        )
    finally:
        source_connection.close()
    return staged_source_path


def _replace_approved_partition(
    *,
    connection: duckdb.DuckDBPyConnection,
    staged_source_path: Path,
    request: ApprovedBackfillRequest,
    proposal: RecoveryProposal,
    binding: FreshnessRecoveryBinding | None,
) -> int:
    if binding is None:
        return load_hmda_loans_partition(
            connection,
            [staged_source_path],
            request.source_year,
            source_file=request.source_file,
            table_name=request.table_name,
            expected_identity=proposal.approved_before_identity,
            preserve_source_metadata=True,
        )
    expected_freshness_at = binding.approved_before.freshness_at
    if expected_freshness_at is None:
        raise ApprovalGateError("approved before freshness measurement가 없습니다.")
    return load_hmda_loans_partition(
        connection,
        [staged_source_path],
        request.source_year,
        source_file=request.source_file,
        table_name=request.table_name,
        expected_identity=proposal.approved_before_identity,
        expected_max_ingested_at=expected_freshness_at,
        preserve_source_metadata=True,
    )


def _reconcile_content_state(
    current_identity: PartitionContentIdentity,
    proposal: RecoveryProposal,
) -> tuple[str, str, list[str]]:
    if current_identity == proposal.expected_after_identity:
        return "already_recovered", "resume_verification", ["rerun_profile_snapshot"]
    if current_identity == proposal.approved_before_identity:
        return (
            "partition_changed",
            "overwrite_partition",
            ["overwrite_partition", "rerun_profile_snapshot"],
        )
    raise ApprovalGateError(
        "recovery target이 approved before/after state와 다른 diverged state입니다."
    )


def _reconcile_freshness_state(
    *,
    current_identity: PartitionContentIdentity,
    current_freshness_at: datetime | None,
    observed_at: datetime,
    proposal: RecoveryProposal,
    binding: FreshnessRecoveryBinding,
) -> tuple[str, str, list[str]]:
    current_observation = _freshness_observation(
        freshness_at=current_freshness_at,
        observed_at=observed_at,
    )
    if (
        current_identity == proposal.expected_after_identity
        and current_observation.freshness_at == binding.expected_after_freshness_at
    ):
        if not _freshness_is_acceptable(current_observation, binding.max_age_minutes):
            raise ApprovalGateError(
                "replay freshness가 만료되어 새 validation과 approval이 필요합니다."
            )
        return "already_recovered", "resume_verification", ["rerun_profile_snapshot"]
    if (
        current_identity == proposal.approved_before_identity
        and current_observation.freshness_at == binding.approved_before.freshness_at
    ):
        return (
            "partition_changed",
            "overwrite_partition",
            ["overwrite_partition", "rerun_profile_snapshot"],
        )
    raise ApprovalGateError(
        "freshness recovery target이 approved compound state와 달라 새 validation과 "
        "approval이 필요합니다."
    )


def _freshness_observation(
    *,
    freshness_at: datetime | None,
    observed_at: datetime,
) -> FreshnessObservation:
    try:
        return FreshnessObservation(
            freshness_status=(
                FreshnessMeasurementStatus.MEASURED
                if freshness_at is not None
                else FreshnessMeasurementStatus.UNAVAILABLE
            ),
            freshness_at=freshness_at,
            observed_at=observed_at,
        )
    except ValidationError as exc:
        raise ApprovalGateError("freshness observation이 유효하지 않습니다.") from exc


def _snapshot_freshness_observation(
    snapshot: ProfileSnapshot,
) -> FreshnessObservation:
    return FreshnessObservation(
        freshness_status=snapshot.freshness_status,
        freshness_at=snapshot.freshness_at,
        observed_at=snapshot.observed_at,
    )


def _freshness_is_acceptable(
    observation: FreshnessObservation,
    max_age_minutes: float,
) -> bool:
    if (
        observation.freshness_status is FreshnessMeasurementStatus.UNAVAILABLE
        or observation.freshness_at is None
    ):
        return False
    return observation.observed_at - observation.freshness_at < timedelta(
        minutes=max_age_minutes
    )


def _freshness_matches_binding(
    observation: FreshnessObservation,
    binding: FreshnessRecoveryBinding,
) -> bool:
    return (
        observation.freshness_at == binding.expected_after_freshness_at
        and _freshness_is_acceptable(observation, binding.max_age_minutes)
    )
