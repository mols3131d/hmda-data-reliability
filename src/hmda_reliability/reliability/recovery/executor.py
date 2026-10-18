"""외부 승인된 복구를 실행하고 파티션 내용 식별자를 검증한다."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import NamedTuple

import duckdb
from pydantic import ValidationError

from hmda_reliability.data_platform.duckdb import (
    DuckDBMutationLockError,
    current_database_path,
    database_mutation_lock,
)
from hmda_reliability.data_platform.sql import quote_string_literal
from hmda_reliability.hmda_data import (
    PartitionContentIdentity,
    load_hmda_loans_partition,
    partition_content_identity,
    partition_max_ingested_at,
)
from hmda_reliability.hmda_data.errors import HMDADataLoadError, HMDAStalePartitionError
from hmda_reliability.logger import get_logger
from hmda_reliability.reliability.contracts import (
    FreshnessMeasurementStatus,
    FreshnessObservation,
    FreshnessRecoveryBinding,
    ProfileSnapshot,
    RecoveryProposal,
    can_execute_risky_action,
)
from hmda_reliability.reliability.errors import (
    ApprovalGateError,
    BackfillValidationError,
    ProfileSnapshotError,
)
from hmda_reliability.reliability.profiling import create_profile_snapshot
from hmda_reliability.reliability.recovery.profile_scope import (
    ensure_recovery_profile_population,
)
from hmda_reliability.reliability.recovery.request import ApprovedBackfillRequest
from hmda_reliability.reliability.recovery.result import BackfillValidationResult

_LOGGER = get_logger(__name__)
_REQUIRED_APPROVAL_ACTIONS = frozenset(
    {"overwrite_partition", "rerun_profile_snapshot"}
)


class ReconciliationDecision(NamedTuple):
    """파티션 복구 대상 상태 조정 결과 (상태명, 수행할 조치, 실행할 전체 액션 목록)."""

    mutation_state: str
    reconciliation_action: str
    executed_actions: list[str]


class ApprovalBackfillValidator:
    """후보 소스 접근 및 대상 변이 전에 승인 범위를 엄격히 검증한다.

    검증 및 복구 불변식:
    1. 사전 승인 검증: 대상 DB 또는 후보 Parquet 소스를 조작하기 전에
       `Approval`과 `RecoveryProposal` 계약 일치성 및 권한을 먼저 확인한다.
    2. 격리된 스테이징: 후보 소스는 임시 디렉토리의 Parquet으로 먼저 구체화 및
       내용 식별자 검증을 거친 후에만 대상 DB에 반영된다.
    3. 원자적 교체 및 조정: 파티션 상태가 이미 복구된 상태(`already_recovered`)인 경우
       덮어쓰기 없이 프로파일 검증만 재개하며, `approved_before_identity`와 일치하는
       경우에만 `overwrite_partition`을 원자적으로 수행한다.
    4. 프로파일 실패 시 상태 보존: 파티션 커밋 후 프로파일 스냅샷 계산 실패 시
       `BackfillValidationError`에 분기(`diverged`) 정보를 명시적으로 반환한다.
    """

    def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
        self._connection = connection

    def _reconcile_state(
        self,
        *,
        request: ApprovedBackfillRequest,
        proposal: RecoveryProposal,
        current_identity: PartitionContentIdentity,
    ) -> ReconciliationDecision:
        """Proposal 바인딩 종류(content vs freshness)에 따라 목표 상태를 조정한다."""
        if proposal.freshness_binding is None:
            return _reconcile_content_state(current_identity, proposal)

        current_freshness_at = partition_max_ingested_at(
            self._connection,
            table_name=request.table_name,
            source_year=request.source_year,
            source_file=request.source_file,
        )
        return _reconcile_freshness_state(
            current_identity=current_identity,
            current_freshness_at=current_freshness_at,
            observed_at=request.profile_request.observed_at,
            proposal=proposal,
            binding=proposal.freshness_binding,
        )

    def execute(self, request: ApprovedBackfillRequest) -> BackfillValidationResult:
        """승인된 이전 상태로 복구하거나 재현(replay) 시 정확한 상태를 검증한다."""

        # Approval scope is validated before the candidate source is read.
        request = _ensure_approved(request)
        completed_result: BackfillValidationResult | None = None
        try:
            with database_mutation_lock(current_database_path(self._connection)):
                completed_result = self._execute_locked(request)
            return completed_result
        except DuckDBMutationLockError as exc:
            if completed_result is not None:
                raise BackfillValidationError(
                    "backfill 완료 후 target mutation lock 해제에 실패했습니다.",
                    mutation_state=completed_result.mutation_state,
                    reconciliation_action="resume_verification",
                    context=completed_result.model_dump(mode="json"),
                ) from exc
            raise BackfillValidationError(
                "backfill target mutation lock을 획득할 수 없습니다."
            ) from exc

    def _execute_locked(
        self, request: ApprovedBackfillRequest
    ) -> BackfillValidationResult:
        approval, proposal = request.approval, request.proposal
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
                ensure_recovery_profile_population(
                    self._connection, request.profile_request
                )
                mutation_state, reconciliation_action, executed_actions = (
                    self._reconcile_state(
                        request=request,
                        proposal=proposal,
                        current_identity=current_identity,
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
                        binding=proposal.freshness_binding,
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
    """복구 게이트를 적용하고 내용 식별자 기반의 검증 증거를 반환한다."""

    return ApprovalBackfillValidator(connection).execute(request)


def _ensure_approved(
    request: ApprovedBackfillRequest,
) -> ApprovedBackfillRequest:
    try:
        request = ApprovedBackfillRequest.model_validate(
            request.model_dump(warnings=False)
        )
    except ValidationError as exc:
        raise ApprovalGateError(
            "backfill approval, recovery proposal 또는 profile request contract가 "
            "유효하지 않습니다."
        ) from exc
    approval, proposal = request.approval, request.proposal
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
    if (
        request.table_name != proposal.table_name
        or request.source_year != proposal.source_year
        or request.source_file != proposal.source_file
    ):
        raise ApprovalGateError(
            "backfill request의 target scope가 승인된 proposal과 일치하지 않습니다."
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
    return request


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
        ensure_recovery_profile_population(source_connection, request.profile_request)
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
) -> ReconciliationDecision:
    if current_identity == proposal.expected_after_identity:
        return ReconciliationDecision(
            mutation_state="already_recovered",
            reconciliation_action="resume_verification",
            executed_actions=["rerun_profile_snapshot"],
        )
    if current_identity == proposal.approved_before_identity:
        return ReconciliationDecision(
            mutation_state="partition_changed",
            reconciliation_action="overwrite_partition",
            executed_actions=["overwrite_partition", "rerun_profile_snapshot"],
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
) -> ReconciliationDecision:
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
        return ReconciliationDecision(
            mutation_state="already_recovered",
            reconciliation_action="resume_verification",
            executed_actions=["rerun_profile_snapshot"],
        )
    if (
        current_identity == proposal.approved_before_identity
        and current_observation.freshness_at == binding.approved_before.freshness_at
    ):
        return ReconciliationDecision(
            mutation_state="partition_changed",
            reconciliation_action="overwrite_partition",
            executed_actions=["overwrite_partition", "rerun_profile_snapshot"],
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
