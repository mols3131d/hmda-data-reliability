"""Raw load result model."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class RawLoadResult(BaseModel):
    """raw source load result."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    database_path: Path
    source_root: Path
    source_file_count: int = Field(ge=0)
    source_year: int = Field(ge=2000, le=2100)
    source_file: str | None = None
    hmda_loans_row_count: int = Field(ge=0)
