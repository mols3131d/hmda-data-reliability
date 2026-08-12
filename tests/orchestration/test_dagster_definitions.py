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
    RawLoadResult,
)
from project_pivot.data_platform.artifacts import artifact_projection_id
from project_pivot.orchestration.definitions import defs
from project_pivot.orchestration.defs import assets as dagster_assets
from project_pivot.orchestration.defs.assets import (
    dbt_loan_analytics,
    raw_hmda_loans,
)
from project_pivot.orchestration.defs.resource import DataOperationsResource

pytestmark = pytest.mark.integration


def test_resource_uses_environment_backed_request_defaults(
    monkeypatch: MonkeyPatch,
) -> None:
    """기본 resource는 Data Operations runtime settings를 소비한다."""

    monkeypatch.setenv("PROJECT_PIVOT_DUCKDB_PATH", "scratch/environment.duckdb")
    monkeypatch.setenv("PROJECT_PIVOT_SOURCE_ROOT", "scratch/environment-hmda")
    monkeypatch.setenv("PROJECT_PIVOT_SOURCE_YEAR", "2024")

    request = DataOperationsResource().to_request()

    assert request.database_path == Path("scratch/environment.duckdb")
    assert request.source_root == Path("scratch/environment-hmda")
    assert request.source_year == 2024


def test_resource_config_overrides_environment_backed_defaults(
    monkeypatch: MonkeyPatch,
) -> None:
    """명시적인 Dagster resource config가 같은 runtime setting을 우선한다."""

    monkeypatch.setenv("PROJECT_PIVOT_DUCKDB_PATH", "scratch/environment.duckdb")

    request = DataOperationsResource(
        database_path="scratch/configured.duckdb"
    ).to_request()

    assert request.database_path == Path("scratch/configured.duckdb")


def test_resource_config_overrides_invalid_environment_value(
    monkeypatch: MonkeyPatch,
) -> None:
    """명시 config는 같은 field의 invalid environment 값보다 우선한다."""

    monkeypatch.setenv("PROJECT_PIVOT_SOURCE_YEAR", "next")

    request = DataOperationsResource(source_year=2025).to_request()

    assert request.source_year == 2025


def test_resource_revalidates_explicit_configuration() -> None:
    """명시적인 Dagster config도 Data Operations request validation을 따른다."""

    with pytest.raises(ValueError, match="source_year"):
        DataOperationsResource(source_year=1999).to_request()

    with pytest.raises(ValueError, match="source_file"):
        DataOperationsResource(source_file="").to_request()


@pytest.mark.parametrize("field", ["database_path", "source_root"])
def test_resource_rejects_empty_path_configuration(field: str) -> None:
    """명시적인 빈 path config는 environment/default로 fallback하지 않는다."""

    with pytest.raises(ValueError, match=field):
        DataOperationsResource(**{field: ""}).to_request()


def test_dagster_definitions_expose_medallion_assets_and_job() -> None:
    """Pipeline asset, group, dependency가 Dagster definitions에 등록되는지 검증한다."""

    asset_graph = defs.resolve_asset_graph()
    asset_keys = {key.to_user_string() for key in asset_graph.get_all_asset_keys()}
    job = defs.resolve_job_def("pipeline_job")

    assert asset_keys == {
        "raw_hmda_loans",
        "dbt_loan_analytics",
    }
    assert job.name == "pipeline_job"

    raw_node = asset_graph.get(AssetKey("raw_hmda_loans"))
    dbt_node = asset_graph.get(AssetKey("dbt_loan_analytics"))
    assert raw_node.group_name == "bronze"
    assert dbt_node.group_name == "silver_gold"
    assert raw_node.parent_keys == set()
    assert dbt_node.parent_keys == {AssetKey("raw_hmda_loans")}


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
        manifest_path = tmp_path / "manifest.json"
        run_results_path = tmp_path / "run_results.json"
        manifest_path.write_text("{}", encoding="utf-8")
        run_results_path.write_text("{}", encoding="utf-8")
        return DbtBuildResult(
            command=["dbt", "build"],
            return_code=0,
            manifest_path=manifest_path,
            run_results_path=run_results_path,
            projection_id=artifact_projection_id(
                manifest_path,
                run_results_path,
            ),
            succeeded=True,
        )

    monkeypatch.setattr(dagster_assets, "load_raw_data", load_raw_data_stub)
    monkeypatch.setattr(dagster_assets, "run_dbt_build", run_dbt_build_stub)

    result = materialize(
        [raw_hmda_loans, dbt_loan_analytics],
        resources={"data_operations": DataOperationsResource()},
    )

    assert result.success
    raw_materialization = result.asset_materializations_for_node("raw_hmda_loans")[0]
    dbt_materialization = result.asset_materializations_for_node("dbt_loan_analytics")[
        0
    ]
    assert "hmda_loans_row_count" in raw_materialization.metadata
    assert "source_file_count" in raw_materialization.metadata
    assert "source_year" in raw_materialization.metadata
    assert "succeeded" in dbt_materialization.metadata
    assert "manifest_path" in dbt_materialization.metadata
    assert dbt_materialization.metadata["projection_id"].value == artifact_projection_id(
        tmp_path / "manifest.json",
        tmp_path / "run_results.json",
    )


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
