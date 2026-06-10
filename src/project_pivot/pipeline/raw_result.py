"""Raw load result model."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class RawLoadResult(BaseModel):
    """raw source load result."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    database_path: Path
    source_root: Path
    source_file_count: int = Field(ge=0)
    taxi_zones_row_count: int = Field(ge=0)
    yellow_tripdata_row_count: int = Field(ge=0)
