"""데이터 작업의 incident lifecycle 결과 모델."""

from pydantic import BaseModel, ConfigDict, Field

from project_pivot.hmda_data import PartitionContentIdentity


class LifecycleResult(BaseModel):
    """Read-only incident 분석을 caller가 소비할 수 있는 형태로 요약한다.

    Detection이 없으면 action 목록은 비어 있고 recovery proposal input에 필요한
    ``target_content_identity``와 ``dbt_projection_id``도 ``None``이다.
    Recovery나 evaluation 실행 결과는 이 model의 책임이 아니다.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    metadata_row_count: int = Field(ge=0)
    baseline_row_count: int = Field(ge=0)
    current_row_count: int = Field(ge=0)
    detected_incident_ids: list[str] = Field(default_factory=list)
    detected_incident_types: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    affected_assets: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    backfill_actions: list[str] = Field(default_factory=list)
    validation_actions: list[str] = Field(default_factory=list)
    target_content_identity: PartitionContentIdentity | None = None
    dbt_projection_id: str | None = None
