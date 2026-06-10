"""Dagster definitions 테스트."""

from project_pivot.orchestration.dagster.definitions import defs


def test_dagster_definitions_expose_mvp_assets_and_job() -> None:
    """MVP asset과 job이 Dagster definitions에 등록되는지 검증한다."""

    asset_graph = defs.resolve_asset_graph()
    asset_keys = {
        key.to_user_string()
        for key in asset_graph.get_all_asset_keys()
    }
    job = defs.resolve_job_def("mvp_pipeline_job")

    assert asset_keys == {
        "raw_taxi_data",
        "dbt_analytics",
        "mvp_incident_lifecycle",
    }
    assert job.name == "mvp_pipeline_job"
