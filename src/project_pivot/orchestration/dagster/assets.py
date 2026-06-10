"""Dagster assets for MVP pipeline."""

from dagster import AssetExecutionContext, asset

from project_pivot.orchestration.dagster.resource import MvpPipelineDagsterResource
from project_pivot.pipeline import load_raw_data, run_dbt_build, run_incident_lifecycle


@asset
def raw_taxi_data(
    context: AssetExecutionContext,
    pipeline: MvpPipelineDagsterResource,
) -> dict[str, object]:
    """원천 파일을 raw DuckDB table로 적재한다."""

    result = load_raw_data(pipeline.to_request())
    context.log.info(
        "raw taxi data loaded",
        extra={"yellow_tripdata_row_count": result.yellow_tripdata_row_count},
    )
    return result.model_dump(mode="json")


@asset
def dbt_analytics(
    context: AssetExecutionContext,
    raw_taxi_data: dict[str, object],
    pipeline: MvpPipelineDagsterResource,
) -> dict[str, object]:
    """dbt staging/mart 모델과 테스트를 실행한다."""

    request = pipeline.to_request()
    if not request.run_dbt_build:
        context.log.info("dbt build skipped", extra={"raw_load": raw_taxi_data})
        return {"succeeded": True, "skipped": True}
    result = run_dbt_build(request)
    context.log.info("dbt build completed", extra={"return_code": result.return_code})
    return result.model_dump(mode="json")


@asset
def mvp_incident_lifecycle(
    context: AssetExecutionContext,
    dbt_analytics: dict[str, object],
    pipeline: MvpPipelineDagsterResource,
) -> dict[str, object]:
    """evidence부터 evaluation까지 incident lifecycle을 실행한다."""

    result = run_incident_lifecycle(pipeline.to_request())
    context.log.info(
        "mvp incident lifecycle completed",
        extra={
            "detected_incident_types": result.detected_incident_types,
            "dbt_analytics": dbt_analytics,
        },
    )
    return result.model_dump(mode="json")
