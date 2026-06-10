"""Evaluation report 모델."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from project_pivot.reliability.evaluation.case_result import EvaluationCaseResult


class EvaluationReport(BaseModel):
    """Synthetic case 평가 요약."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    generated_at: datetime
    total_cases: int = Field(ge=0)
    detection_passed_cases: int = Field(ge=0)
    action_passed_cases: int = Field(ge=0)
    detection_success_rate: float = Field(ge=0, le=1)
    action_success_rate: float = Field(ge=0, le=1)
    cases: list[EvaluationCaseResult] = Field(default_factory=list)
