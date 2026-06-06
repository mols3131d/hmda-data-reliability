"""Base reliability contract."""

from pydantic import BaseModel, ConfigDict


class ReliabilityContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
