"""Profile contract models."""

from datetime import datetime

from pydantic import Field, model_validator

from project_pivot.reliability.contracts.base import ReliabilityContract


class ProfileSnapshot(ReliabilityContract):
    snapshot_id: str
    asset_name: str
    partition: str
    observed_at: datetime
    row_count: int = Field(ge=0)
    null_rates: dict[str, float] = Field(default_factory=dict)
    schema_hash: str
    freshness_at: datetime
    metric_values: dict[str, float] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_null_rates(self) -> "ProfileSnapshot":
        invalid_columns = [
            column
            for column, null_rate in self.null_rates.items()
            if null_rate < 0 or null_rate > 1
        ]
        if invalid_columns:
            joined_columns = ", ".join(sorted(invalid_columns))
            raise ValueError(f"null_rates must be between 0 and 1: {joined_columns}")
        return self
