"""조치 제안 초안(RemediationDraft) 결과 모델 정의 모듈."""

from pydantic import BaseModel, ConfigDict, Field


class RemediationDraft(BaseModel):
    """Evidence 기반 조치 제안 초안."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    incident_id: str
    incident_type: str
    asset_name: str
    partition: str
    rca_summary: str
    evidence_refs: list[str] = Field(min_length=1)
    affected_assets: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(min_length=1)
    dbt_test_suggestions: list[str] = Field(default_factory=list)
    backfill_actions: list[str] = Field(default_factory=list)
    validation_actions: list[str] = Field(default_factory=list)
    requires_approval: bool = True
