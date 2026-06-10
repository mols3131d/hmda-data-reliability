"""Evaluation case result 모델."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EvaluationCaseResult(BaseModel):
    """Synthetic case의 기대/실제 incident 및 action 결과."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    case_name: str
    expected_incident_types: list[str] = Field(default_factory=list)
    detected_incident_types: list[str] = Field(default_factory=list)
    required_actions: list[str] = Field(default_factory=list)
    remediation_actions: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)

    @field_validator("case_name")
    @classmethod
    def _validate_case_name(cls, value: str) -> str:
        if not value.strip():
            msg = "case_name은 비어 있을 수 없습니다."
            raise ValueError(msg)
        return value

    @property
    def detection_passed(self) -> bool:
        if not self.expected_incident_types:
            return not self.detected_incident_types
        return set(self.expected_incident_types).issubset(self.detected_incident_types)

    @property
    def action_passed(self) -> bool:
        return set(self.required_actions).issubset(self.remediation_actions)
