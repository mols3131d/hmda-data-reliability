"""승인된 backfill 실행 요청 모델."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from hmda_reliability.hmda_data.ingestion import HMDA_LOANS_TABLE
from hmda_reliability.reliability.contracts import Approval, RecoveryProposal
from hmda_reliability.reliability.profiling import ProfileSnapshotRequest


class ApprovedBackfillRequest(BaseModel):
    """Approval gate 이후 partition overwrite와 validation 입력."""

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    approval: Approval
    proposal: RecoveryProposal
    source_paths: tuple[Path, ...] = Field(min_length=1)
    source_year: int = Field(ge=2000, le=2100)
    source_file: str | None = None
    profile_request: ProfileSnapshotRequest
    table_name: str = HMDA_LOANS_TABLE

    @field_validator("source_paths", mode="before")
    @classmethod
    def _coerce_source_paths(cls, value: object) -> tuple[Path, ...]:
        if isinstance(value, str | Path):
            return (Path(value),)
        if not isinstance(value, list | tuple):
            msg = "source_paths는 path 목록이어야 합니다."
            raise ValueError(msg)
        paths: list[Path] = []
        for path in value:
            if not isinstance(path, str | Path):
                msg = "source_paths의 각 값은 path여야 합니다."
                raise ValueError(msg)
            paths.append(Path(path))
        return tuple(paths)

    @field_validator("table_name", "source_file")
    @classmethod
    def _validate_optional_text(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            msg = "값은 비어 있을 수 없습니다."
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def _validate_profile_partition(self) -> ApprovedBackfillRequest:
        if str(self.profile_request.partition) != str(self.source_year):
            msg = "profile_request.partition은 source_year와 같아야 합니다."
            raise ValueError(msg)
        if self.profile_request.table_name != self.table_name:
            msg = "profile_request.table_name은 table_name과 같아야 합니다."
            raise ValueError(msg)
        return self


def approved_backfill_request(
    *,
    approval: Approval,
    proposal: RecoveryProposal,
    source_paths: tuple[Path, ...],
    source_year: int,
    profile_request: ProfileSnapshotRequest,
    table_name: str = HMDA_LOANS_TABLE,
    source_file: str | None = None,
) -> ApprovedBackfillRequest:
    """명시 인자로 approved backfill 요청을 만든다."""

    return ApprovedBackfillRequest(
        approval=approval,
        proposal=proposal,
        source_paths=source_paths,
        source_year=source_year,
        source_file=source_file,
        profile_request=profile_request,
        table_name=table_name,
    )
