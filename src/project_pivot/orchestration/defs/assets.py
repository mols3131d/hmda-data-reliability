"""Dagster assets for MVP pipeline."""

from dagster import AssetExecutionContext, MaterializeResult, MetadataValue, asset

from project_pivot.orchestration.defs.resource import MvpPipelineDagsterResource
from project_pivot.pipeline import load_raw_data, run_dbt_build, run_incident_lifecycle


@asset(group_name="bronze", kinds={"duckdb", "python"})
def raw_taxi_data(
    context: AssetExecutionContext,
    pipeline: MvpPipelineDagsterResource,
) -> MaterializeResult[None]:
    """원천 파일을 raw DuckDB table로 적재한다."""

    result = load_raw_data(pipeline.to_request())
    context.log.info(
        "raw taxi data 적재 완료",
        extra={"yellow_tripdata_row_count": result.yellow_tripdata_row_count},
    )
    return MaterializeResult(
        metadata={
            "database_path": MetadataValue.path(str(result.database_path)),
            "source_root": MetadataValue.path(str(result.source_root)),
            "source_file_count": MetadataValue.int(result.source_file_count),
            "taxi_zones_row_count": MetadataValue.int(result.taxi_zones_row_count),
            "yellow_tripdata_row_count": MetadataValue.int(
                result.yellow_tripdata_row_count
            ),
        }
    )


@asset(deps=[raw_taxi_data], group_name="silver_gold", kinds={"dbt"})
def dbt_analytics(
    context: AssetExecutionContext,
    pipeline: MvpPipelineDagsterResource,
) -> MaterializeResult[None]:
    """dbt staging/mart 모델과 테스트를 실행한다."""

    request = pipeline.to_request()
    if not request.run_dbt_build:
        context.log.info("dbt build 건너뜀")
        return MaterializeResult(
            metadata={
                "succeeded": MetadataValue.text("true"),
                "skipped": MetadataValue.text("true"),
                "reason": MetadataValue.text("run_dbt_build=false"),
            }
        )
    result = run_dbt_build(request)
    context.log.info("dbt build 완료", extra={"return_code": result.return_code})
    return MaterializeResult(
        metadata={
            "succeeded": MetadataValue.text(str(result.succeeded).lower()),
            "skipped": MetadataValue.text("false"),
            "return_code": MetadataValue.int(result.return_code),
            "manifest_path": MetadataValue.path(str(result.manifest_path)),
            "run_results_path": MetadataValue.path(str(result.run_results_path)),
        }
    )


@asset(deps=[dbt_analytics], group_name="control", kinds={"python"})
def mvp_incident_lifecycle(
    context: AssetExecutionContext,
    pipeline: MvpPipelineDagsterResource,
) -> MaterializeResult[None]:
    """evidence부터 evaluation까지 incident lifecycle을 실행한다."""

    result = run_incident_lifecycle(pipeline.to_request())
    context.log.info(
        "mvp incident lifecycle 완료",
        extra={
            "detected_incident_types": result.detected_incident_types,
        },
    )
    return MaterializeResult(
        metadata={
            "metadata_row_count": MetadataValue.int(result.metadata_row_count),
            "baseline_row_count": MetadataValue.int(result.baseline_row_count),
            "current_row_count": MetadataValue.int(result.current_row_count),
            "detected_incident_types": MetadataValue.json(
                result.detected_incident_types
            ),
            "evidence_refs": MetadataValue.json(result.evidence_refs),
            "affected_assets": MetadataValue.json(result.affected_assets),
            "recommended_actions": MetadataValue.json(result.recommended_actions),
            "backfill_actions": MetadataValue.json(result.backfill_actions),
            "validation_actions": MetadataValue.json(result.validation_actions),
            "evaluation_report_path": MetadataValue.path(
                str(result.evaluation_report_path)
            ),
            "detection_success_rate": MetadataValue.float(
                result.detection_success_rate
            ),
            "action_success_rate": MetadataValue.float(result.action_success_rate),
        }
    )
