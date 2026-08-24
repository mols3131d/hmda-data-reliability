"""Base reliability contract."""

from pydantic import BaseModel, ConfigDict


class ReliabilityContract(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False, extra="forbid", frozen=True)
