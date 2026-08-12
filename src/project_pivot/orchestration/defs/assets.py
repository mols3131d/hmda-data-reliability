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
    """HMDA raw partition을 적재하고 materialization metadata를 기록한다.

    같은 partition의 재실행은 ``load_raw_data()``의 멱등 적재 contract를 따른다.
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
    """dbt build 실행 또는 명시적 skip 결과를 materialization으로 기록한다.

    ``run_dbt_build=False``이면 ``skipped=True``, ``succeeded=False``를 기록한다.
    실행이 성공하면 candidate artifact를 shared current projection으로 승격한다.
    """

    request = data_operations.to_request()
    if not request.run_dbt_build:
        return MaterializeResult(
            metadata={
                "succeeded": MetadataValue.bool(False),
                "skipped": MetadataValue.bool(True),
                "reason": MetadataValue.text("run_dbt_build=false"),
            }
        )
    result = run_dbt_build(request)
    # run_dbt_build()는 current를 바꾸지 않는다. 성공한 candidate만 current로
    # 승격하도록 build 다음에 promotion을 둔다.
    promote_dbt_artifacts(result, request)
    return MaterializeResult(
        metadata={
            "succeeded": MetadataValue.bool(result.succeeded),
            "skipped": MetadataValue.bool(False),
            "return_code": MetadataValue.int(result.return_code),
            "manifest_path": MetadataValue.path(str(result.manifest_path)),
            "run_results_path": MetadataValue.path(str(result.run_results_path)),
            "projection_id": MetadataValue.text(result.projection_id),
        }
    )
