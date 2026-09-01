"""dbt build 결과 모델 정의 모듈."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict


class DbtBuildResult(BaseModel):
    """dbt build 성공 후 존재와 identity가 확인된 candidate artifact pair를 식별한다.

    Artifact path는 shared current projection이 아니라 run-scoped candidate를
    가리킨다.
    ``projection_id``는 이후 promotion 전에 같은 artifact pair인지 재확인하는
    identity다.
    Downstream validation과 promotion 여부 판단은 caller의 책임이다.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    command: list[str]
    return_code: int
    manifest_path: Path
    run_results_path: Path
    projection_id: str
    succeeded: bool
