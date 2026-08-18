"""Evidence contract models."""

from datetime import datetime
from enum import StrEnum

from pydantic import Field

from project_pivot.reliability.contracts.base import ReliabilityContract


class EvidenceSource(StrEnum):
    PROFILE = "profile"
    TABLE_METADATA = "table_metadata"
    DBT_ARTIFACT = "dbt_artifact"
    CATALOG = "catalog"
    ORCHESTRATION = "orchestration"


class Evidence(ReliabilityContract):
    evidence_id: str
    source: EvidenceSource
    asset_name: str
    partition: str
    observed_at: datetime
    summary: str
    payload: dict[str, object] = Field(default_factory=dict)
