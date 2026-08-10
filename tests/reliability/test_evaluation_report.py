"""Evaluation report 생성 테스트."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

import project_pivot.reliability.evaluation.volume_drop as volume_drop
from project_pivot.data_operations import DataOperationRequest
from project_pivot.data_platform.artifacts import artifact_projection_id
from project_pivot.reliability import (
    Approval,
    ApprovalStatus,
    EvaluationCaseResult,
    build_evaluation_report,
    build_recovery_evaluation_case,
    evaluate_volume_drop_vertical_slice,
    render_evaluation_report_markdown,
    write_evaluation_report,
)


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
        observed_at=datetime(2026, 6, 10, 0, 0, tzinfo=UTC),
    )

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

    first = evaluate_volume_drop_vertical_slice(
        request=request,
        source_paths=(source_path,),
        workspace=tmp_path / "run-1",
        approve=approve,
        validate_candidate=lambda _request: "sha256:candidate",
        validate_target=lambda _request: "sha256:target",
        sample_fraction=0.1,
    )
    second = evaluate_volume_drop_vertical_slice(
        request=request.model_copy(
            update={"database_path": tmp_path / "target-2.duckdb"}
        ),
        source_paths=(source_path,),
        workspace=tmp_path / "run-2",
        approve=approve,
        validate_candidate=lambda _request: "sha256:candidate",
        validate_target=lambda _request: "sha256:target",
        sample_fraction=0.1,
    )

    assert first.fixture_identity == second.fixture_identity
    assert first.expected_recovery_identity == second.expected_recovery_identity
    assert first.clean_case.detected_incident_types == []
    assert first.volume_drop_case.detected_incident_types == ["volume_drop"]
    assert first.post_recovery_case.detected_incident_types == []
    assert first.recovery.validation_passed
    assert first.replay.reconciliation_action == "resume_verification"


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

    def fail_target_validation(_request: DataOperationRequest) -> str:
        raise RuntimeError("dbt failed")

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
        raise RuntimeError("dbt failed")

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

    assert result.recovery.mutation_state == "partition_changed"
    assert result.target_dbt_projection_id is None
    assert result.target_dbt_failure == "dbt failed"
    assert result.post_recovery_case.failure_stage == "after_partition_mutation"
    assert result.post_recovery_case.target_mutated
    assert result.post_recovery_case.artifact_projection_ids == [
        artifact_projection_id(
            request.dbt_manifest_path,
            request.dbt_run_results_path,
        )
    ]
    assert (request.dbt_manifest_path.parent, False) in lock_calls


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
