"""Dagster pipeline materialization 통합 테스트."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from dagster import materialize

from project_pivot.orchestration.defs.assets import (
    dbt_loan_analytics,
    incident_lifecycle,
    raw_hmda_loans,
)
from project_pivot.orchestration.defs.resource import DataOperationsResource

pytestmark = pytest.mark.integration

_ASSETS = [raw_hmda_loans, dbt_loan_analytics, incident_lifecycle]


def test_pipeline_materialization_creates_lifecycle_report(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """실제 단계 로직을 Dagster asset 순서로 실행한다."""

    monkeypatch.chdir(tmp_path)
    resource, report_path = _prepare_pipeline(tmp_path)

    result = materialize(_ASSETS, resources={"data_operations": resource})

    assert result.success
    raw = result.asset_materializations_for_node("raw_hmda_loans")[0]
    dbt = result.asset_materializations_for_node("dbt_loan_analytics")[0]
    lifecycle = result.asset_materializations_for_node("incident_lifecycle")[0]
    assert raw.metadata["hmda_loans_row_count"].value == 4
    assert dbt.metadata["skipped"].value is True
    assert lifecycle.metadata["detected_incident_types"].value == ["volume_drop"]
    assert lifecycle.metadata["affected_assets"].value == [
        "stg_hmda_loans",
        "mart_hmda_loan_outcomes",
    ]
    assert lifecycle.metadata["detection_success_rate"].value == 1.0
    assert report_path.exists()


def test_pipeline_materialization_validates_backfill(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Dagster 경로에서 partition backfill 검증 결과를 기록한다."""

    monkeypatch.chdir(tmp_path)
    resource, _ = _prepare_pipeline(tmp_path, run_backfill=True)

    result = materialize(_ASSETS, resources={"data_operations": resource})

    assert result.success
    lifecycle = result.asset_materializations_for_node("incident_lifecycle")[0]
    assert lifecycle.metadata["backfill_validation_passed"].value is True


def _prepare_pipeline(
    tmp_path: Path,
    *,
    run_backfill: bool = False,
) -> tuple[DataOperationsResource, Path]:
    source_root = tmp_path / "raw"
    source_root.mkdir()
    _write_hmda_csv(source_root)
    _write_dbt_artifacts(tmp_path)
    report_path = tmp_path / "pipeline_report.md"
    resource = DataOperationsResource(
        database_path=str(tmp_path / "project_pivot.duckdb"),
        source_root=str(source_root),
        source_year=2025,
        report_path=str(report_path),
        run_dbt_build=False,
        run_backfill=run_backfill,
    )
    return resource, report_path


def _write_hmda_csv(source_root: Path) -> None:
    (source_root / "year_2025.csv").write_text(
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


def _write_dbt_artifacts(tmp_path: Path) -> None:
    target = tmp_path / "dbt" / "target"
    target.mkdir(parents=True)
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
    (target / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (target / "run_results.json").write_text("{}", encoding="utf-8")
