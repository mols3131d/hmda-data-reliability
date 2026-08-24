"""Impact analysis 요청 모델."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from hmda_reliability.reliability.contracts import Incident


class ImpactAnalysisRequest(BaseModel):
    """dbt artifact 기반 impact analysis 입력."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid", frozen=True)

    incident: Incident
    dbt_manifest_path: Path
    dbt_run_results_path: Path
