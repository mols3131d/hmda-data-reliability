"""Pipeline pipeline CLI 테스트."""

from __future__ import annotations

from pathlib import Path

import pytest

from project_pivot.pipeline import (
    LifecycleResult,
    PipelineRunResult,
    RawLoadResult,
)
from project_pivot.pipeline import cli as pipeline_cli

pytestmark = pytest.mark.component


def test_pipeline_cli_run_writes_result_json(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """CLI가 pipeline 결과를 지정한 JSON 파일에 저장하는지 검증한다."""

    output_path = tmp_path / "result.json"
    report_path = tmp_path / "report.md"

    def fake_run_pipeline(_request: object) -> PipelineRunResult:
        return PipelineRunResult(
            status="completed",
            raw_load=RawLoadResult(
                database_path=Path("data/project_pivot.duckdb"),
                source_root=Path("data/raw/hmda"),
                source_file_count=1,
                source_year=2025,
                hmda_loans_row_count=4,
            ),
            dbt_build=None,
            lifecycle=LifecycleResult(
                metadata_row_count=4,
                baseline_row_count=4,
                current_row_count=1,
                detected_incident_types=["volume_drop"],
                evidence_refs=["ev_1"],
                affected_assets=["mart_hmda_loan_outcomes"],
                recommended_actions=["prepare_partition_backfill"],
                backfill_actions=["prepare_partition_backfill"],
                validation_actions=["rerun_profile_snapshot"],
                evaluation_report_path=report_path,
                detection_success_rate=1.0,
                action_success_rate=1.0,
            ),
        )

    monkeypatch.setattr(pipeline_cli, "run_pipeline", fake_run_pipeline)

    exit_code = pipeline_cli.main(
        [
            "run",
            "--output",
            str(output_path),
            "--report-path",
            str(report_path),
        ]
    )

    assert exit_code == 0
    assert output_path.exists()
    assert '"status": "completed"' in output_path.read_text(encoding="utf-8")
    assert '"detected_incident_types": [' in output_path.read_text(encoding="utf-8")
