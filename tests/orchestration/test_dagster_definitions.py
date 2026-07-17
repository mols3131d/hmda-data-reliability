"""Dagster definitions 테스트."""

import importlib
from pathlib import Path

import pytest
from dagster import AssetKey, materialize
from pytest import MonkeyPatch

from project_pivot import data_operations
from project_pivot.data_operations import (
    DataOperationRequest,
    DbtBuildResult,
    LifecycleResult,
    RawLoadResult,
)
from project_pivot.orchestration.definitions import defs
from project_pivot.orchestration.defs import assets as dagster_assets
from project_pivot.orchestration.defs.assets import (
    dbt_loan_analytics,
    incident_lifecycle,
    raw_hmda_loans,
)
from project_pivot.orchestration.defs.resource import DataOperationsResource

pytestmark = pytest.mark.integration


def test_dagster_definitions_expose_medallion_assets_and_job() -> None:
    """Pipeline asset, group, dependency가 Dagster definitions에 등록되는지 검증한다."""

    asset_graph = defs.resolve_asset_graph()
    asset_keys = {
        key.to_user_string()
        for key in asset_graph.get_all_asset_keys()
    }
    job = defs.resolve_job_def("pipeline_job")

    assert asset_keys == {
        "raw_hmda_loans",
        "dbt_loan_analytics",
        "incident_lifecycle",
    }
    assert job.name == "pipeline_job"

    raw_node = asset_graph.get(AssetKey("raw_hmda_loans"))
    dbt_node = asset_graph.get(AssetKey("dbt_loan_analytics"))
    lifecycle_node = asset_graph.get(AssetKey("incident_lifecycle"))

    assert raw_node.group_name == "bronze"
    assert dbt_node.group_name == "silver_gold"
    assert lifecycle_node.group_name == "control"
    assert raw_node.parent_keys == set()
    assert dbt_node.parent_keys == {AssetKey("raw_hmda_loans")}
    assert lifecycle_node.parent_keys == {AssetKey("dbt_loan_analytics")}


def test_dagster_is_only_full_pipeline_orchestrator() -> None:
    """독립 runner와 CLI를 공개하지 않는다."""

    assert not hasattr(data_operations, "run_pipeline")
    assert not hasattr(data_operations, "PipelineRunResult")
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("project_pivot.data_operations.cli")


def test_dagster_materialization_records_metadata(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Pipeline asset materialization metadata가 Dagster event에 기록되는지 검증한다."""

    def load_raw_data_stub(_request: DataOperationRequest) -> RawLoadResult:
        return RawLoadResult(
            database_path=tmp_path / "project_pivot.duckdb",
            source_root=tmp_path / "raw",
            source_file_count=2,
            source_year=2025,
            hmda_loans_row_count=4,
        )

    def run_dbt_build_stub(_request: DataOperationRequest) -> DbtBuildResult:
        return DbtBuildResult(
            command=["dbt", "build"],
            return_code=0,
            manifest_path=tmp_path / "manifest.json",
            run_results_path=tmp_path / "run_results.json",
            succeeded=True,
        )

    def run_incident_lifecycle_stub(
        _request: DataOperationRequest,
    ) -> LifecycleResult:
        return LifecycleResult(
            metadata_row_count=4,
            baseline_row_count=4,
            current_row_count=1,
            detected_incident_types=["volume_drop"],
            evidence_refs=["ev_volume_drop"],
            affected_assets=["stg_hmda_loans"],
            recommended_actions=["validate_source_partition"],
            backfill_actions=["prepare_partition_backfill"],
            validation_actions=["rerun_profile_snapshot"],
            backfill_validation_passed=None,
            evaluation_report_path=tmp_path / "report.md",
            detection_success_rate=1.0,
            action_success_rate=1.0,
        )

    monkeypatch.setattr(dagster_assets, "load_raw_data", load_raw_data_stub)
    monkeypatch.setattr(dagster_assets, "run_dbt_build", run_dbt_build_stub)
    monkeypatch.setattr(
        dagster_assets,
        "run_incident_lifecycle",
        run_incident_lifecycle_stub,
    )

    result = materialize(
        [raw_hmda_loans, dbt_loan_analytics, incident_lifecycle],
        resources={"data_operations": DataOperationsResource()},
    )

    assert result.success
    raw_materialization = result.asset_materializations_for_node("raw_hmda_loans")[0]
    dbt_materialization = result.asset_materializations_for_node(
        "dbt_loan_analytics"
    )[0]
    lifecycle_materialization = result.asset_materializations_for_node(
        "incident_lifecycle"
    )[0]

    assert "hmda_loans_row_count" in raw_materialization.metadata
    assert "source_year" in raw_materialization.metadata
    assert "manifest_path" in dbt_materialization.metadata
    assert "detected_incident_types" in lifecycle_materialization.metadata
    assert "evaluation_report_path" in lifecycle_materialization.metadata


def test_skipped_dbt_build_records_boolean_metadata(
    monkeypatch: MonkeyPatch,
) -> None:
    """건너뛴 dbt build를 실행 성공으로 표시하지 않는다."""

    resource = DataOperationsResource(run_dbt_build=False)
    monkeypatch.setattr(
        dagster_assets,
        "load_raw_data",
        lambda _request: RawLoadResult(
            database_path=Path("project_pivot.duckdb"),
            source_root=Path("raw"),
            source_file_count=1,
            source_year=2025,
            hmda_loans_row_count=1,
        ),
    )
    result = materialize(
        [raw_hmda_loans, dbt_loan_analytics],
        resources={"data_operations": resource},
    )
    materialization = result.asset_materializations_for_node("dbt_loan_analytics")[0]

    assert materialization.metadata["skipped"].value is True
    assert materialization.metadata["succeeded"].value is False
