"""Evaluation report 생성 테스트."""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from subprocess import CompletedProcess
from typing import cast

import duckdb
import pytest

import project_pivot.reliability.evaluation.volume_drop as volume_drop
import project_pivot.reliability.recovery.executor as recovery_executor
from project_pivot.data_operations import (
    DataOperationRequest,
    DbtBuildResult,
    promote_dbt_artifacts,
    run_dbt_build,
)
from project_pivot.data_operations.errors import DataOperationError
from project_pivot.data_platform.artifacts import artifact_projection_id
from project_pivot.data_platform.duckdb import DuckDBConnectionManager
from project_pivot.hmda_data.errors import HMDAStalePartitionError
from project_pivot.reliability import (
    Approval,
    ApprovalStatus,
    EvaluationCaseResult,
    ProfileSnapshot,
    build_evaluation_report,
    build_recovery_evaluation_case,
    evaluate_volume_drop_vertical_slice,
    render_evaluation_report_markdown,
    write_evaluation_report,
)
from project_pivot.reliability.errors import ProfileSnapshotError
from project_pivot.reliability.profiling import ProfileSnapshotRequest


@pytest.mark.unit
def test_evaluation_report_calculates_case_success_rates() -> None:
    """normal/incident case 성공률을 계산한다."""
    report = build_evaluation_report(
        [
            EvaluationCaseResult(
                case_name="normal_partition",
                expected_incident_types=[],
                detected_incident_types=[],
            ),
            EvaluationCaseResult(
                case_name="row_count_drop",
                expected_incident_types=["volume_drop"],
                detected_incident_types=["volume_drop"],
                required_actions=["prepare_partition_backfill"],
                remediation_actions=[
                    "validate_source_partition",
                    "prepare_partition_backfill",
                ],
                evidence_refs=["ev_volume_drop"],
            ),
            EvaluationCaseResult(
                case_name="null_spike",
                expected_incident_types=["null_spike"],
                detected_incident_types=[],
                required_actions=["add_dbt_not_null_test"],
                remediation_actions=[],
            ),
        ],
        generated_at=datetime(2026, 6, 10, 0, 0, tzinfo=UTC),
    )

    assert report.total_cases == 3
    assert report.detection_passed_cases == 2
    assert report.action_passed_cases == 2
    assert report.detection_success_rate == 2 / 3
    assert report.action_success_rate == 2 / 3


@pytest.mark.component
def test_write_evaluation_report_creates_markdown(tmp_path: Path) -> None:
    """evaluation_report.md에 case별 기대/실제 결과를 표시한다."""
    output_path = tmp_path / "evaluation_report.md"
    report = build_evaluation_report(
        [
            EvaluationCaseResult(
                case_name="schema_drift",
                expected_incident_types=["schema_drift"],
                detected_incident_types=["schema_drift"],
                required_actions=["validate_schema_hash"],
                remediation_actions=["validate_schema_hash"],
                evidence_refs=["ev_schema_drift"],
            )
        ],
        generated_at=datetime(2026, 6, 10, 0, 0, tzinfo=UTC),
    )

    written_path = write_evaluation_report(report, output_path)
    content = written_path.read_text(encoding="utf-8")

    assert written_path == output_path
    assert content == render_evaluation_report_markdown(report)
    assert "# Pipeline Evaluation Report" in content
    assert (
        "| schema_drift | schema_drift | schema_drift | PASS | PASS | "
        "- | - | - | ev_schema_drift | - |"
    ) in content


@pytest.mark.integration
def test_volume_drop_vertical_slice_is_deterministic_and_replay_safe(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Clean/volume-drop flow는 content recovery와 replay evidence를 재현한다."""

    source_path = tmp_path / "year_2025.csv"
    rows = [f"2025,1,1,{300000 + index},{100 + index},CA,06001" for index in range(10)]
    source_path.write_text(
        "\n".join(
            [
                "activity_year,loan_purpose,action_taken,loan_amount,income,state_code,county_code",
                *rows,
            ]
        ),
        encoding="utf-8",
    )
    target = tmp_path / "dbt" / "target"
    target.mkdir(parents=True)
    (target / "manifest.json").write_text(
        '{"sources":{"source.project_pivot.raw.hmda_loans":{"name":"hmda_loans","schema":"raw","resource_type":"source","depends_on":{"nodes":[]}}},"nodes":{}}',
        encoding="utf-8",
    )
    (target / "run_results.json").write_text("{}", encoding="utf-8")
    request = DataOperationRequest(
        database_path=tmp_path / "target.duckdb",
        source_root=tmp_path,
        dbt_manifest_path=target / "manifest.json",
        dbt_run_results_path=target / "run_results.json",
        dbt_run_target_path=target / "runs",
        observed_at=datetime(2026, 6, 10, 0, 0, tzinfo=UTC),
    )
    initial_projection_id = artifact_projection_id(
        request.dbt_manifest_path,
        request.dbt_run_results_path,
    )

    def run_dbt_stub(*args: object, **kwargs: object) -> CompletedProcess[str]:
        raw_command = args[0]
        assert isinstance(raw_command, list)
        command = [str(part) for part in raw_command]
        target_path = Path(command[command.index("--target-path") + 1])
        target_path.mkdir(parents=True, exist_ok=True)
        environment = kwargs.get("env")
        assert isinstance(environment, dict)
        duckdb_path = environment.get("PROJECT_PIVOT_DUCKDB_PATH")
        assert isinstance(duckdb_path, str | Path)
        database_path = Path(duckdb_path)
        run_kind = "candidate" if database_path.name == "candidate.duckdb" else "target"
        with DuckDBConnectionManager(database_path) as connection:
            row_count = connection.execute(
                "SELECT count(*) FROM raw.hmda_loans WHERE activity_year = 2025"
            ).fetchone()
        assert row_count == (10,)
        (target_path / "manifest.json").write_text(
            f'{{"metadata":{{"run":"{run_kind}"}},"nodes":{{}},"sources":{{}}}}',
            encoding="utf-8",
        )
        (target_path / "run_results.json").write_text(
            f'{{"metadata":{{"run":"{run_kind}"}},"results":[]}}',
            encoding="utf-8",
        )
        return CompletedProcess[str](command, 0, "", "")

    monkeypatch.setattr(subprocess, "run", run_dbt_stub)

    def approve(proposal):
        assert request.observed_at is not None
        return Approval(
            approval_id="approval_volume_drop",
            incident_id=proposal.incident_id,
            status=ApprovalStatus.APPROVED,
            requested_by="data-platform",
            requested_at=datetime(2026, 6, 10, 0, 0, tzinfo=UTC),
            approved_by="data-owner",
            approved_at=datetime(2026, 6, 10, 0, 0, tzinfo=UTC),
            requested_actions=list(proposal.target_actions),
            recovery_proposal=proposal,
        )

    def validate_candidate(candidate_request: DataOperationRequest) -> str:
        projection_before_run = artifact_projection_id(
            request.dbt_manifest_path,
            request.dbt_run_results_path,
        )
        result = run_dbt_build(candidate_request)
        assert (
            artifact_projection_id(
                request.dbt_manifest_path,
                request.dbt_run_results_path,
            )
            == projection_before_run
        )
        return result.projection_id

    def validate_target(target_request: DataOperationRequest) -> str:
        result = run_dbt_build(target_request)
        promote_dbt_artifacts(result, target_request)
        return artifact_projection_id(
            target_request.dbt_manifest_path,
            target_request.dbt_run_results_path,
        )

    first = evaluate_volume_drop_vertical_slice(
        request=request,
        source_paths=(source_path,),
        workspace=tmp_path / "run-1",
        approve=approve,
        validate_candidate=validate_candidate,
        validate_target=validate_target,
        sample_fraction=0.1,
    )
    second = evaluate_volume_drop_vertical_slice(
        request=request.model_copy(
            update={"database_path": tmp_path / "target-2.duckdb"}
        ),
        source_paths=(source_path,),
        workspace=tmp_path / "run-2",
        approve=approve,
        validate_candidate=validate_candidate,
        validate_target=validate_target,
        sample_fraction=0.1,
    )

    assert first.fixture_identity == second.fixture_identity
    assert first.expected_recovery_identity == second.expected_recovery_identity
    assert first.clean_case.detected_incident_types == []
    assert first.volume_drop_case.detected_incident_types == ["volume_drop"]
    assert first.post_recovery_case.detected_incident_types == []
    assert first.recovery is not None
    assert first.replay is not None
    assert first.recovery.validation_passed
    assert first.replay.reconciliation_action == "resume_verification"
    assert first.candidate_dbt_projection_id != initial_projection_id
    assert first.target_dbt_projection_id is not None
    assert first.candidate_dbt_projection_id == second.candidate_dbt_projection_id
    assert first.target_dbt_projection_id == second.target_dbt_projection_id
    assert (
        artifact_projection_id(
            request.dbt_manifest_path,
            request.dbt_run_results_path,
        )
        == second.target_dbt_projection_id
    )

    def fail_candidate(_request: DataOperationRequest) -> str:
        raise DataOperationError(
            "candidate dbt failed",
            context={
                "run_target_path": str(tmp_path / "candidate-failed-run"),
                "return_code": 1,
            },
        )

    failed_candidate = evaluate_volume_drop_vertical_slice(
        request=request.model_copy(
            update={"database_path": tmp_path / "target-3.duckdb"}
        ),
        source_paths=(source_path,),
        workspace=tmp_path / "run-3",
        approve=approve,
        validate_candidate=fail_candidate,
        validate_target=validate_target,
        sample_fraction=0.1,
    )

    assert failed_candidate.recovery is None
    assert failed_candidate.post_recovery_case.failure_stage == (
        "before_target_mutation"
    )
    assert "failed-run:" in " ".join(failed_candidate.post_recovery_case.evidence_refs)

    prior_projection_id = artifact_projection_id(
        request.dbt_manifest_path,
        request.dbt_run_results_path,
    )

    def fail_after_promotion(target_request: DataOperationRequest) -> str:
        result = run_dbt_build(target_request)
        result.manifest_path.write_text(
            '{"metadata":{"run":"post-promotion"}}',
            encoding="utf-8",
        )
        result.run_results_path.write_text(
            '{"metadata":{"run":"post-promotion"}}',
            encoding="utf-8",
        )
        result = result.model_copy(
            update={
                "projection_id": artifact_projection_id(
                    result.manifest_path,
                    result.run_results_path,
                )
            }
        )
        promote_dbt_artifacts(result, target_request)
        raise RuntimeError("post-promotion read failed")

    with pytest.raises(RuntimeError, match="post-promotion"):
        evaluate_volume_drop_vertical_slice(
            request=request.model_copy(
                update={"database_path": tmp_path / "target-4.duckdb"}
            ),
            source_paths=(source_path,),
            workspace=tmp_path / "run-4",
            approve=approve,
            validate_candidate=validate_candidate,
            validate_target=fail_after_promotion,
            sample_fraction=0.1,
        )

    assert (
        artifact_projection_id(
            request.dbt_manifest_path,
            request.dbt_run_results_path,
        )
        != prior_projection_id
    )


@pytest.mark.integration
def test_volume_drop_vertical_slice_returns_pre_mutation_safety_cases(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Recovery gate failure를 evaluation evidence로 반환한다."""

    def evaluate(
        request: DataOperationRequest,
        source_path: Path,
        approve,
    ):
        return evaluate_volume_drop_vertical_slice(
            request=request,
            source_paths=(source_path,),
            workspace=request.database_path.with_suffix(""),
            approve=approve,
            validate_candidate=lambda _request: "sha256:candidate",
            validate_target=lambda _request: "sha256:target",
            sample_fraction=0.1,
        )

    invalid_source, invalid_request = _volume_drop_fixture(tmp_path / "invalid")

    def approve_then_invalidate(proposal):
        invalid_source.write_text(
            invalid_source.read_text(encoding="utf-8").replace(",100,CA", ",101,CA"),
            encoding="utf-8",
        )
        return _approved(proposal)

    invalid_candidate = evaluate(
        invalid_request,
        invalid_source,
        approve_then_invalidate,
    )

    incomplete_source, incomplete_request = _volume_drop_fixture(
        tmp_path / "incomplete"
    )

    def approve_incomplete(proposal):
        return _approved(proposal).model_copy(
            update={"requested_actions": ("overwrite_partition",)}
        )

    incomplete_approval = evaluate(
        incomplete_request,
        incomplete_source,
        approve_incomplete,
    )

    diverged_source, diverged_request = _volume_drop_fixture(tmp_path / "diverged")

    def approve_then_diverge(proposal):
        with DuckDBConnectionManager(diverged_request.database_path) as connection:
            connection.execute("UPDATE raw.hmda_loans SET income = income + 1")
        return _approved(proposal)

    diverged_target = evaluate(
        diverged_request,
        diverged_source,
        approve_then_diverge,
    )

    stale_source, stale_request = _volume_drop_fixture(tmp_path / "stale")
    original_load = cast(
        Callable[..., int],
        recovery_executor.load_hmda_loans_partition,
    )
    load_count = 0

    def raise_stale_on_target_load(*args: object, **kwargs: object) -> int:
        nonlocal load_count
        load_count += 1
        if load_count == 2:
            raise HMDAStalePartitionError("stale")
        return original_load(*args, **kwargs)

    monkeypatch.setattr(
        recovery_executor,
        "load_hmda_loans_partition",
        raise_stale_on_target_load,
    )
    stale_target = evaluate(stale_request, stale_source, _approved)

    for result, case_name in (
        (invalid_candidate, "invalid_candidate"),
        (incomplete_approval, "incomplete_approval"),
        (diverged_target, "diverged_target"),
        (stale_target, "stale_target"),
    ):
        assert result.recovery is None
        assert result.replay is None
        assert result.post_recovery_case.case_name == case_name
        assert result.post_recovery_case.failure_stage == "before_target_mutation"
        assert not result.post_recovery_case.target_mutated
        assert result.post_recovery_case.artifact_projection_ids

    assert diverged_target.post_recovery_case.reconciliation_action == (
        "request_new_validation_and_approval"
    )
    assert stale_target.post_recovery_case.reconciliation_action == (
        "request_new_validation_and_approval"
    )


@pytest.mark.integration
def test_replay_profile_failure_preserves_completed_recovery_evidence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """첫 recovery 뒤 replay failure는 이미 완료된 mutation을 숨기지 않는다."""

    source_path, request = _volume_drop_fixture(tmp_path / "fixture")
    original_snapshot = recovery_executor.create_profile_snapshot
    snapshot_count = 0

    def fail_replay_snapshot(
        connection: duckdb.DuckDBPyConnection,
        profile_request: ProfileSnapshotRequest,
    ) -> ProfileSnapshot:
        nonlocal snapshot_count
        snapshot_count += 1
        if snapshot_count == 2:
            raise ProfileSnapshotError("replay profile failed")
        return original_snapshot(connection, profile_request)

    monkeypatch.setattr(
        recovery_executor,
        "create_profile_snapshot",
        fail_replay_snapshot,
    )

    result = evaluate_volume_drop_vertical_slice(
        request=request,
        source_paths=(source_path,),
        workspace=tmp_path / "run",
        approve=_approved,
        validate_candidate=lambda _request: "sha256:candidate",
        validate_target=lambda _request: "sha256:target",
        sample_fraction=0.1,
    )

    assert result.recovery is not None
    assert result.recovery.mutation_state == "partition_changed"
    assert result.replay is None
    assert result.post_recovery_case.failure_stage == "after_partition_mutation"
    assert result.post_recovery_case.target_mutated
    assert result.post_recovery_case.reconciliation_action == "resume_verification"


@pytest.mark.integration
def test_replay_diverged_target_requests_new_validation_and_approval(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """첫 recovery 뒤 diverged replay는 새 validation과 approval을 요구한다."""

    source_path, request = _volume_drop_fixture(tmp_path / "fixture")
    original_recovery = volume_drop.execute_approved_backfill
    recovery_count = 0

    def diverge_after_first_recovery(connection, recovery_request):
        nonlocal recovery_count
        recovery_count += 1
        recovery = original_recovery(connection, recovery_request)
        if recovery_count == 1:
            connection.execute("UPDATE raw.hmda_loans SET income = income + 1")
        return recovery

    monkeypatch.setattr(
        volume_drop,
        "execute_approved_backfill",
        diverge_after_first_recovery,
    )

    result = evaluate_volume_drop_vertical_slice(
        request=request,
        source_paths=(source_path,),
        workspace=tmp_path / "run",
        approve=_approved,
        validate_candidate=lambda _request: "sha256:candidate",
        validate_target=lambda _request: "sha256:target",
        sample_fraction=0.1,
    )

    assert result.recovery is not None
    assert result.recovery.mutation_state == "partition_changed"
    assert result.replay is None
    assert result.post_recovery_case.failure_stage == "after_partition_mutation"
    assert result.post_recovery_case.target_mutated
    assert result.post_recovery_case.reconciliation_action == (
        "request_new_validation_and_approval"
    )


@pytest.mark.integration
def test_volume_drop_vertical_slice_preserves_source_file_scope(
    tmp_path: Path,
) -> None:
    """File-scoped recovery는 다른 source file을 synthetic input에 섞지 않는다."""

    selected = tmp_path / "selected_2025.csv"
    other = tmp_path / "other_2025.txt"
    header = (
        "activity_year,loan_purpose,action_taken,loan_amount,income,"
        "state_code,county_code"
    )
    selected.write_text(
        "\n".join([header, *[f"2025,1,1,{index},100,CA,06001" for index in range(10)]]),
        encoding="utf-8",
    )
    other.write_text(
        "not,a,valid,hmda,source",
        encoding="utf-8",
    )
    target = tmp_path / "dbt" / "target"
    target.mkdir(parents=True)
    (target / "manifest.json").write_text('{"sources":{},"nodes":{}}', encoding="utf-8")
    (target / "run_results.json").write_text("{}", encoding="utf-8")
    request = DataOperationRequest(
        database_path=tmp_path / "target.duckdb",
        source_root=tmp_path,
        source_file=selected.name,
        dbt_manifest_path=target / "manifest.json",
        dbt_run_results_path=target / "run_results.json",
        observed_at=datetime(2026, 6, 10, 0, 0, tzinfo=UTC),
    )

    def approve(proposal):
        assert request.observed_at is not None
        return Approval(
            approval_id="approval_scoped",
            incident_id=proposal.incident_id,
            status=ApprovalStatus.APPROVED,
            requested_by="data-platform",
            requested_at=request.observed_at,
            approved_by="data-owner",
            approved_at=request.observed_at,
            requested_actions=list(proposal.target_actions),
            recovery_proposal=proposal,
        )

    result = evaluate_volume_drop_vertical_slice(
        request=request,
        source_paths=(selected, other),
        workspace=tmp_path / "run",
        approve=approve,
        validate_candidate=lambda _request: "sha256:candidate",
        validate_target=lambda _request: "sha256:target",
        sample_fraction=0.2,
    )

    assert result.fixture_identity.row_count == 10
    assert result.expected_recovery_identity.row_count == 10
    assert result.recovery is not None
    assert result.recovery.validation_passed
    failed_recovery = result.recovery.model_copy(update={"validation_passed": False})
    failed_case = build_recovery_evaluation_case(
        case_name="failed_content_validation",
        expected_incident_types=["volume_drop"],
        detected_incident_types=["volume_drop"],
        recovery=failed_recovery,
    )
    assert not failed_case.action_passed


@pytest.mark.integration
def test_volume_drop_vertical_slice_records_target_dbt_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Partition mutation 뒤 target dbt failure는 safety case evidence로 반환한다."""

    source_path = tmp_path / "year_2025.csv"
    source_path.write_text(
        "\n".join(
            [
                "activity_year,loan_purpose,action_taken,loan_amount,income,state_code,county_code",
                *[f"2025,1,1,{index},100,CA,06001" for index in range(10)],
            ]
        ),
        encoding="utf-8",
    )
    target = tmp_path / "dbt" / "target"
    target.mkdir(parents=True)
    (target / "manifest.json").write_text('{"sources":{},"nodes":{}}', encoding="utf-8")
    (target / "run_results.json").write_text("{}", encoding="utf-8")
    request = DataOperationRequest(
        database_path=tmp_path / "target.duckdb",
        dbt_manifest_path=target / "manifest.json",
        dbt_run_results_path=target / "run_results.json",
        observed_at=datetime(2026, 6, 10, 0, 0, tzinfo=UTC),
    )

    def approve(proposal):
        assert request.observed_at is not None
        return Approval(
            approval_id="approval_target_failure",
            incident_id=proposal.incident_id,
            status=ApprovalStatus.APPROVED,
            requested_by="data-platform",
            requested_at=request.observed_at,
            approved_by="data-owner",
            approved_at=request.observed_at,
            requested_actions=list(proposal.target_actions),
            recovery_proposal=proposal,
        )

    def fail_target_validation(_request: DataOperationRequest) -> str:
        raise DataOperationError(
            "dbt failed",
            context={
                "run_target_path": str(tmp_path / "failed-run"),
                "return_code": 1,
            },
        )

    lock_calls: list[tuple[Path, bool]] = []
    original_lock = volume_drop.artifact_projection_lock

    def track_prior_projection_lock(directory: Path, *, exclusive: bool):
        lock_calls.append((directory, exclusive))
        return original_lock(directory, exclusive=exclusive)

    monkeypatch.setattr(
        volume_drop,
        "artifact_projection_lock",
        track_prior_projection_lock,
    )

    result = evaluate_volume_drop_vertical_slice(
        request=request,
        source_paths=(source_path,),
        workspace=tmp_path / "run",
        approve=approve,
        validate_candidate=lambda _request: "sha256:candidate",
        validate_target=fail_target_validation,
    )

    assert result.recovery is not None
    assert result.recovery.mutation_state == "partition_changed"
    assert result.target_dbt_projection_id is None
    assert result.target_dbt_failure == "dbt failed"
    assert result.target_dbt_failure_context == {
        "run_target_path": str(tmp_path / "failed-run"),
        "return_code": 1,
    }
    assert result.post_recovery_case.failure_stage == "after_partition_mutation"
    assert result.post_recovery_case.target_mutated
    assert result.post_recovery_case.reconciliation_action == "resume_verification"
    assert result.post_recovery_case.artifact_projection_ids == [
        artifact_projection_id(
            request.dbt_manifest_path,
            request.dbt_run_results_path,
        )
    ]
    assert (
        f"failed-run:{tmp_path / 'failed-run'}"
        in result.post_recovery_case.evidence_refs
    )
    assert (request.dbt_manifest_path.parent, False) in lock_calls


@pytest.mark.integration
def test_post_promotion_data_operation_failure_reports_actual_current_projection(
    tmp_path: Path,
) -> None:
    """Promotion 뒤 domain failure는 prior가 아닌 actual current evidence를 남긴다."""

    source_path, request = _volume_drop_fixture(tmp_path / "fixture")
    prior_projection_id = artifact_projection_id(
        request.dbt_manifest_path,
        request.dbt_run_results_path,
    )
    promoted_projection_id: str | None = None

    def fail_after_promotion(target_request: DataOperationRequest) -> str:
        nonlocal promoted_projection_id
        run_target = tmp_path / "promoted-run"
        run_target.mkdir()
        run_manifest = run_target / "manifest.json"
        run_results = run_target / "run_results.json"
        run_manifest.write_text("promoted-manifest", encoding="utf-8")
        run_results.write_text("promoted-results", encoding="utf-8")
        promoted_projection_id = artifact_projection_id(
            run_manifest,
            run_results,
        )
        promote_dbt_artifacts(
            DbtBuildResult(
                command=["dbt", "build"],
                return_code=0,
                manifest_path=run_manifest,
                run_results_path=run_results,
                projection_id=promoted_projection_id,
                succeeded=True,
            ),
            target_request,
        )
        raise DataOperationError(
            "post-promotion observation failed",
            context={"run_target_path": str(run_target)},
        )

    result = evaluate_volume_drop_vertical_slice(
        request=request,
        source_paths=(source_path,),
        workspace=tmp_path / "run",
        approve=_approved,
        validate_candidate=lambda _request: "sha256:candidate",
        validate_target=fail_after_promotion,
        sample_fraction=0.1,
    )

    assert promoted_projection_id is not None
    assert result.post_recovery_case.artifact_projection_ids == [promoted_projection_id]
    assert prior_projection_id not in result.post_recovery_case.artifact_projection_ids
    assert result.post_recovery_case.reconciliation_action == "resume_verification"


@pytest.mark.unit
def test_recovery_safety_cases_preserve_mutation_and_artifact_evidence() -> None:
    """Pre/post mutation failure를 artifact projection과 함께 구분한다."""

    pre_mutation = build_recovery_evaluation_case(
        case_name="stale_target",
        expected_incident_types=["volume_drop"],
        detected_incident_types=["volume_drop"],
        failure_stage="before_target_mutation",
        evidence_refs=["stale-target"],
        artifact_projection_ids=["sha256:last-known-good"],
    )
    post_mutation = build_recovery_evaluation_case(
        case_name="recovery_dbt_failure",
        expected_incident_types=["volume_drop"],
        detected_incident_types=["volume_drop"],
        failure_stage="after_partition_mutation",
        evidence_refs=["dbt-failure"],
        artifact_projection_ids=[
            "sha256:last-known-good",
            "sha256:failed-run",
        ],
    )

    assert not pre_mutation.target_mutated
    assert not pre_mutation.action_passed
    assert pre_mutation.failure_stage == "before_target_mutation"
    assert post_mutation.target_mutated
    assert not post_mutation.action_passed
    assert post_mutation.artifact_projection_ids == [
        "sha256:last-known-good",
        "sha256:failed-run",
    ]


def _volume_drop_fixture(tmp_path: Path) -> tuple[Path, DataOperationRequest]:
    source_path = tmp_path / "year_2025.csv"
    source_path.parent.mkdir(parents=True)
    source_path.write_text(
        "\n".join(
            [
                "activity_year,loan_purpose,action_taken,loan_amount,income,state_code,county_code",
                *[f"2025,1,1,{index},100,CA,06001" for index in range(10)],
            ]
        ),
        encoding="utf-8",
    )
    target = tmp_path / "dbt" / "target"
    target.mkdir(parents=True)
    (target / "manifest.json").write_text('{"sources":{},"nodes":{}}', encoding="utf-8")
    (target / "run_results.json").write_text("{}", encoding="utf-8")
    return source_path, DataOperationRequest(
        database_path=tmp_path / "target.duckdb",
        source_root=tmp_path,
        dbt_manifest_path=target / "manifest.json",
        dbt_run_results_path=target / "run_results.json",
        observed_at=datetime(2026, 6, 10, 0, 0, tzinfo=UTC),
    )


def _approved(proposal) -> Approval:
    approved_at = datetime(2026, 6, 10, 0, 0, tzinfo=UTC)
    return Approval(
        approval_id="approval_volume_drop",
        incident_id=proposal.incident_id,
        status=ApprovalStatus.APPROVED,
        requested_by="data-platform",
        requested_at=approved_at,
        approved_by="data-owner",
        approved_at=approved_at,
        requested_actions=proposal.target_actions,
        recovery_proposal=proposal,
    )
