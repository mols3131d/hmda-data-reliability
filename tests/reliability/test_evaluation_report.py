"""Evaluation report 생성 테스트."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from project_pivot.reliability import (
    EvaluationCaseResult,
    build_evaluation_report,
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
    assert "| schema_drift | schema_drift | schema_drift | PASS | PASS |" in content
