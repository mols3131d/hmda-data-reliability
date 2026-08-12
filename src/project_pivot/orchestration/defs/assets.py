"""Data Operations API를 Dagster materialization으로 투영하는 asset."""

from dagster import AssetExecutionContext, MaterializeResult, MetadataValue, asset

from project_pivot.data_operations import (
    load_raw_data,
    promote_dbt_artifacts,
    run_dbt_build,
)
from project_pivot.orchestration.defs.resource import DataOperationsResource


@asset(group_name="bronze", kinds={"duckdb", "python"})
def raw_hmda_loans(
    context: AssetExecutionContext,
    data_operations: DataOperationsResource,
) -> MaterializeResult[None]:
    """HMDA raw partition을 적재하고 관찰 가능한 load metadata를 기록한다.

    동일 partition 재실행은 ``load_raw_data()``의 멱등 적재 contract를 따른다.
    """

    result = load_raw_data(data_operations.to_request())
    context.log.info(
        "raw HMDA loans 적재 완료",
        extra={"hmda_loans_row_count": result.hmda_loans_row_count},
    )
    return MaterializeResult(
        metadata={
            "database_path": MetadataValue.path(str(result.database_path)),
            "source_root": MetadataValue.path(str(result.source_root)),
            "source_file_count": MetadataValue.int(result.source_file_count),
            "source_year": MetadataValue.int(result.source_year),
            "hmda_loans_row_count": MetadataValue.int(result.hmda_loans_row_count),
        }
    )


@asset(deps=[raw_hmda_loans], group_name="silver_gold", kinds={"dbt"})
def dbt_loan_analytics(
    context: AssetExecutionContext,
    data_operations: DataOperationsResource,
) -> MaterializeResult[None]:
    """설정에 따라 dbt build를 실행하고 materialization 상태를 기록한다.

    ``run_dbt_build=False``이면 실행을 건너뛰며 ``skipped=True``와
    ``succeeded=False``를 기록한다. 실행 시 successful candidate artifact를
    shared current projection으로 승격한다.
    """

    request = data_operations.to_request()
    if not request.run_dbt_build:
        context.log.info("dbt build 건너뜀")
        return MaterializeResult(
            metadata={
                "succeeded": MetadataValue.bool(False),
                "skipped": MetadataValue.bool(True),
                "reason": MetadataValue.text("run_dbt_build=false"),
            }
        )
    result = run_dbt_build(request)
    # run_dbt_build()는 candidate를 run-scoped로 남기므로 이 asset이
    # successful run의 shared current projection 승격을 명시적으로 소유한다.
    promote_dbt_artifacts(result, request)
    context.log.info("dbt build 완료", extra={"return_code": result.return_code})
    return MaterializeResult(
        metadata={
            "succeeded": MetadataValue.bool(result.succeeded),
            "skipped": MetadataValue.bool(False),
            "return_code": MetadataValue.int(result.return_code),
            "manifest_path": MetadataValue.path(str(result.manifest_path)),
            "run_results_path": MetadataValue.path(str(result.run_results_path)),
        }
    )
