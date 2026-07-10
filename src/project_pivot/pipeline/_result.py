"""Pipeline pipeline run result model."""

from pydantic import BaseModel, ConfigDict

from project_pivot.pipeline._dbt_result import DbtBuildResult
from project_pivot.pipeline._lifecycle_result import LifecycleResult
from project_pivot.pipeline._raw_result import RawLoadResult


class PipelineRunResult(BaseModel):
    """Pipeline pipeline 전체 실행 결과."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: str
    raw_load: RawLoadResult
    dbt_build: DbtBuildResult | None
    lifecycle: LifecycleResult
