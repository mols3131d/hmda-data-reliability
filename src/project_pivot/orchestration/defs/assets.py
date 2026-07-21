"""데이터 작업을 실행하는 Dagster asset."""

from dagster import AssetExecutionContext, MaterializeResult, MetadataValue, asset

from project_pivot.data_operations import load_raw_data, run_dbt_build
from project_pivot.orchestration.defs.resource import DataOperationsResource


@asset(group_name="bronze", kinds={"duckdb", "python"})
def raw_hmda_loans(
    context: AssetExecutionContext,
    data_operations: DataOperationsResource,
) -> MaterializeResult[None]:
    """원천 파일을 raw DuckDB table로 적재한다."""

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
    """dbt staging/mart 모델과 테스트를 실행한다."""

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
