"""Dagster repository definitions."""

from dagster import Definitions, define_asset_job

from project_pivot.orchestration.defs.assets import (
    dbt_loan_analytics,
    incident_lifecycle,
    raw_hmda_loans,
)
from project_pivot.orchestration.defs.resource import DataOperationsResource

pipeline_job = define_asset_job(
    "pipeline_job",
    selection=[raw_hmda_loans, dbt_loan_analytics, incident_lifecycle],
)

defs = Definitions(
    assets=[raw_hmda_loans, dbt_loan_analytics, incident_lifecycle],
    jobs=[pipeline_job],
    resources={"data_operations": DataOperationsResource()},
)
