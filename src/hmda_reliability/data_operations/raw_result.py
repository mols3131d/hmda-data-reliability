"""원천 데이터 적재 결과 모델 정의 모듈."""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class RawLoadResult(BaseModel):
    """HMDA 원천 파티션 데이터 적재 완료 결과 모델.

    `load_raw_data()` 실행 후 적재 파일 수, 연도 및 최종 row 수를
    불변(frozen) 모델로 caller에게 제공한다.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    database_path: Path
    source_root: Path
    source_file_count: int = Field(ge=0)
    source_year: int = Field(ge=2000, le=2100)
    source_file: str | None = None
    hmda_loans_row_count: int = Field(ge=0)
