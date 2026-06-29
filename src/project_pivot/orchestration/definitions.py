"""Dagster repository definitions."""

from dagster import Definitions, define_asset_job

from project_pivot.orchestration.defs.assets import (
    dbt_loan_analytics,
    mvp_incident_lifecycle,
    raw_hmda_loans,
)
from project_pivot.orchestration.defs.resource import MvpPipelineDagsterResource

mvp_pipeline_job = define_asset_job(
    "mvp_pipeline_job",
    selection=[raw_hmda_loans, dbt_loan_analytics, mvp_incident_lifecycle],
)

defs = Definitions(
    assets=[raw_hmda_loans, dbt_loan_analytics, mvp_incident_lifecycle],
    jobs=[mvp_pipeline_job],
    resources={"pipeline": MvpPipelineDagsterResource()},
)
