"""Impact analysis 결과 모델."""

from pydantic import BaseModel, ConfigDict

from project_pivot.reliability.contracts import Incident, LineageEvidence


class ImpactAnalysisResult(BaseModel):
    """LineageEvidence와 affected assets가 반영된 incident."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    incident: Incident
    lineage_evidence: LineageEvidence
