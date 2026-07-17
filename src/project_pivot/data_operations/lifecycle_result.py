"""데이터 작업의 incident lifecycle 결과 모델."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class LifecycleResult(BaseModel):
    """evidence부터 evaluation까지의 incident lifecycle 요약."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    metadata_row_count: int = Field(ge=0)
    baseline_row_count: int = Field(ge=0)
    current_row_count: int = Field(ge=0)
    detected_incident_types: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    affected_assets: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    backfill_actions: list[str] = Field(default_factory=list)
    validation_actions: list[str] = Field(default_factory=list)
    backfill_validation_passed: bool | None = None
    evaluation_report_path: Path
    detection_success_rate: float = Field(ge=0, le=1)
    action_success_rate: float = Field(ge=0, le=1)
