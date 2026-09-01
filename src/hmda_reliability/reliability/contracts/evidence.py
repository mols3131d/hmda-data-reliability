"""증거(Evidence) 계약 모델 정의 모듈."""

from datetime import datetime
from enum import StrEnum

from pydantic import Field

from hmda_reliability.reliability.contracts.base import ReliabilityContract


class EvidenceSource(StrEnum):
    PROFILE = "profile"
    TABLE_METADATA = "table_metadata"
    DBT_ARTIFACT = "dbt_artifact"
    CATALOG = "catalog"
    ORCHESTRATION = "orchestration"


class Evidence(ReliabilityContract):
    """신뢰성 판단 및 검증에 사용되는 불변의 증거 계약 모델."""

    evidence_id: str
    source: EvidenceSource
    asset_name: str
    partition: str
    observed_at: datetime
    summary: str
    payload: dict[str, object] = Field(default_factory=dict)
