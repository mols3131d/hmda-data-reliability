"""Detection 결과 모델."""

from pydantic import BaseModel, ConfigDict, model_validator

from project_pivot.reliability.contracts import Evidence, Incident


class DetectionResult(BaseModel):
    """Incident와 Evidence 한 쌍의 탐지 결과."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    incident: Incident
    evidence: Evidence

    @model_validator(mode="after")
    def _validate_evidence_ref(self) -> "DetectionResult":
        if self.evidence.evidence_id not in self.incident.evidence_refs:
            msg = "incident.evidence_refs는 evidence.evidence_id를 포함해야 합니다."
            raise ValueError(msg)
        return self
