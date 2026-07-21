"""Dagster pipeline materialization 통합 테스트."""

from __future__ import annotations

from pathlib import Path

import pytest
from dagster import materialize

from project_pivot.orchestration.defs.assets import (
    dbt_loan_analytics,
    raw_hmda_loans,
)
from project_pivot.orchestration.defs.resource import DataOperationsResource

pytestmark = pytest.mark.integration

_ASSETS = [raw_hmda_loans, dbt_loan_analytics]


def test_pipeline_materialization_runs_data_plane_assets(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """실제 단계 로직을 Dagster asset 순서로 실행한다."""

    monkeypatch.chdir(tmp_path)
    resource = _prepare_pipeline(tmp_path)

    result = materialize(_ASSETS, resources={"data_operations": resource})

    assert result.success
    raw = result.asset_materializations_for_node("raw_hmda_loans")[0]
    dbt = result.asset_materializations_for_node("dbt_loan_analytics")[0]
    assert raw.metadata["hmda_loans_row_count"].value == 4
    assert dbt.metadata["skipped"].value is True


def _prepare_pipeline(
    tmp_path: Path,
) -> DataOperationsResource:
    source_root = tmp_path / "raw"
    source_root.mkdir()
    _write_hmda_csv(source_root)
    return DataOperationsResource(
        database_path=str(tmp_path / "project_pivot.duckdb"),
        source_root=str(source_root),
        source_year=2025,
        run_dbt_build=False,
    )


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
