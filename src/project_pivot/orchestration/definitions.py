"""Dagster가 발견하는 data plane ``Definitions`` entry point.

``defs``에는 Bronze→dbt asset graph와 ``pipeline_job``, ``data_operations``
resource만 등록한다. Reliability lifecycle과 승인된 recovery/evaluation은
이 graph에 포함하지 않는다.
"""

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
