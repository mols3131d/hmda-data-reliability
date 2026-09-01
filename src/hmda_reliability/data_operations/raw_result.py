"""원천 데이터 적재 결과 모델 정의 모듈."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class RawLoadResult(BaseModel):
    """원천 소스 적재 결과 모델."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    database_path: Path
    source_root: Path
    source_file_count: int = Field(ge=0)
    source_year: int = Field(ge=2000, le=2100)
    source_file: str | None = None
    hmda_loans_row_count: int = Field(ge=0)
