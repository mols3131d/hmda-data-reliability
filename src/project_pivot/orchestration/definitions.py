"""Dagster repository definitions."""

from dagster import Definitions, define_asset_job

from project_pivot.orchestration.defs.assets import (
    dbt_loan_analytics,
    raw_hmda_loans,
)
from project_pivot.orchestration.defs.resource import DataOperationsResource

pipeline_job = define_asset_job(
    "pipeline_job",
    selection=[raw_hmda_loans, dbt_loan_analytics],
)

defs = Definitions(
    assets=[raw_hmda_loans, dbt_loan_analytics],
    jobs=[pipeline_job],
    resources={"data_operations": DataOperationsResource()},
)
