"""MVP pipeline run result model."""

from pydantic import BaseModel, ConfigDict

from project_pivot.pipeline.dbt_result import DbtBuildResult
from project_pivot.pipeline.lifecycle_result import MvpLifecycleResult
from project_pivot.pipeline.raw_result import RawLoadResult


class MvpPipelineRunResult(BaseModel):
    """MVP pipeline 전체 실행 결과."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: str
    raw_load: RawLoadResult
    dbt_build: DbtBuildResult | None
    lifecycle: MvpLifecycleResult
