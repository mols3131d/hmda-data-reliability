"""dbt build result model."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict


class DbtBuildResult(BaseModel):
    """dbt build process result."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    command: list[str]
    return_code: int
    manifest_path: Path
    run_results_path: Path
    succeeded: bool
