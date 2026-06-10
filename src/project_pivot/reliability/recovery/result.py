"""Backfill validation 결과 모델."""

from pydantic import BaseModel, ConfigDict, Field

from project_pivot.reliability.contracts import ProfileSnapshot


class BackfillValidationResult(BaseModel):
    """승인된 backfill 실행과 profile validation 결과."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    approval_id: str
    incident_id: str
    partition: str
    row_count: int = Field(ge=0)
    profile_snapshot: ProfileSnapshot
    validation_passed: bool
    executed_actions: list[str] = Field(default_factory=list)
