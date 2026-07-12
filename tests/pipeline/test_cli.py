"""Pipeline pipeline CLI 테스트."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

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


def test_pipeline_cli_returns_error_for_invalid_request() -> None:
    """잘못된 CLI 입력은 stack trace 없이 실패 코드로 반환한다."""

    assert (
        pipeline_cli.main(
            [
                "run",
                "--simulate-row-count-ratio",
                "0",
            ]
        )
        == 1
    )


def test_pipeline_cli_returns_error_when_output_write_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """결과 파일 쓰기 오류를 CLI 실패 코드로 변환한다."""

    monkeypatch.setattr(
        pipeline_cli,
        "run_pipeline",
        lambda _request: Mock(model_dump_json=Mock(return_value="{}")),
    )
    output_path = tmp_path / "output-directory"
    output_path.mkdir()

    assert pipeline_cli.main(["run", "--output", str(output_path)]) == 1
