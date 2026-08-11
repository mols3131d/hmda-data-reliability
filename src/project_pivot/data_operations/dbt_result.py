"""dbt build result model."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict


class DbtBuildResult(BaseModel):
    """한 dbt run에서 검증된 candidate artifact pair를 식별한다.

    Artifact path는 shared current projection이 아니라 run-scoped candidate를 가리킨다.
    ``projection_id``는 이후 promotion 전에 같은 artifact pair인지 재확인하는 identity다.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    command: list[str]
    return_code: int
    manifest_path: Path
    run_results_path: Path
    projection_id: str
    succeeded: bool
