"""조치 제안 초안 생성 요청 모델 정의 모듈."""

from pydantic import BaseModel, ConfigDict, Field

from hmda_reliability.reliability.contracts import Evidence, Incident, LineageEvidence


class RemediationDraftRequest(BaseModel):
    """Remediation workflow 입력."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    incident: Incident
    evidence: Evidence
    lineage_evidence: LineageEvidence | None = None
    operator: str = Field(default="data-platform")
