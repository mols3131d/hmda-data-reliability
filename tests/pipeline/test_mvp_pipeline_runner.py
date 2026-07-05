"""MVP pipeline runner 테스트."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from project_pivot.pipeline import MvpPipelineRunRequest, run_mvp_pipeline

pytestmark = pytest.mark.integration


def test_run_mvp_pipeline_without_dbt_build_creates_lifecycle_report(
    tmp_path: Path,
) -> None:
    """fixture artifact로 runner contract를 검증한다."""

    source_root = tmp_path / "raw"
    source_root.mkdir()
    hmda_path = _write_hmda_csv(source_root)
    manifest_path = _write_manifest(tmp_path)
    run_results_path = _write_run_results(tmp_path)
    report_path = tmp_path / "pipeline_report.md"

    result = run_mvp_pipeline(
        MvpPipelineRunRequest(
            database_path=tmp_path / "project_pivot.duckdb",
            source_root=source_root,
            source_year=2025,
            dbt_manifest_path=manifest_path,
            dbt_run_results_path=run_results_path,
            report_path=report_path,
            run_dbt_build=False,
        )
    )

    assert hmda_path.exists()
    assert result.status == "completed"
    assert result.raw_load.hmda_loans_row_count == 4
    assert result.dbt_build is None
    assert result.lifecycle.detected_incident_types == ["volume_drop"]
    assert result.lifecycle.affected_assets == [
        "stg_hmda_loans",
        "mart_hmda_loan_outcomes",
    ]
    assert result.lifecycle.detection_success_rate == 1.0
    assert report_path.exists()


def test_run_mvp_pipeline_with_backfill_validates_hmda_partition(
    tmp_path: Path,
) -> None:
    """HMDA source_year partition backfill 경로를 검증한다."""

    source_root = tmp_path / "raw"
    source_root.mkdir()
    _write_hmda_csv(source_root)
    manifest_path = _write_manifest(tmp_path)
    run_results_path = _write_run_results(tmp_path)

    result = run_mvp_pipeline(
        MvpPipelineRunRequest(
            database_path=tmp_path / "project_pivot.duckdb",
            source_root=source_root,
            source_year=2025,
            dbt_manifest_path=manifest_path,
            dbt_run_results_path=run_results_path,
            report_path=tmp_path / "pipeline_report.md",
            run_backfill=True,
            run_dbt_build=False,
        )
    )

    assert result.status == "completed"
    assert result.lifecycle.backfill_validation_passed is True


def _write_hmda_csv(source_root: Path) -> Path:
    path = source_root / "year_2025.csv"
    path.write_text(
        "\n".join(
            [
                "activity_year,loan_purpose,action_taken,loan_amount,income,state_code,county_code",
                "2025,1,1,350000,120,CA,06001",
                "2025,1,2,450000,130,CA,06001",
                "2025,31,3,420000,95,NY,36061",
                "2025,31,7,380000,95,NY,36061",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _write_manifest(tmp_path: Path) -> Path:
    manifest_path = tmp_path / "manifest.json"
    manifest = {
        "sources": {
            "source.project_pivot.raw.hmda_loans": {
                "name": "hmda_loans",
                "schema": "raw",
                "resource_type": "source",
                "depends_on": {"nodes": []},
            }
        },
        "nodes": {
            "model.project_pivot.stg_hmda_loans": {
                "name": "stg_hmda_loans",
                "resource_type": "model",
                "depends_on": {
                    "nodes": ["source.project_pivot.raw.hmda_loans"]
                },
            },
            "model.project_pivot.mart_hmda_loan_outcomes": {
                "name": "mart_hmda_loan_outcomes",
                "resource_type": "model",
                "depends_on": {
                    "nodes": ["model.project_pivot.stg_hmda_loans"]
                },
            },
        },
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


def _write_run_results(tmp_path: Path) -> Path:
    run_results_path = tmp_path / "run_results.json"
    run_results_path.write_text("{}", encoding="utf-8")
    return run_results_path
