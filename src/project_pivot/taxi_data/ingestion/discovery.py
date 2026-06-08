"""Taxi 원천 파일 발견."""

from __future__ import annotations

import re
from pathlib import Path

from project_pivot.taxi_data.errors import TaxiDataLoadError
from project_pivot.taxi_data.ingestion.common import LOGGER


def discover_yellow_tripdata_files(
    raw_dir: str | Path, *, year: int = 2024
) -> list[Path]:
    """지정 연도의 옐로우 택시 월별 Parquet 원천 파일을 정렬해 찾는다."""

    directory = Path(raw_dir)
    if not directory.is_dir():
        msg = f"옐로우 택시 원천 디렉터리를 찾을 수 없습니다: {raw_dir}"
        raise TaxiDataLoadError(msg)

    filename_pattern = re.compile(rf"^yellow_tripdata_{year}-(0[1-9]|1[0-2])\.parquet$")
    paths = sorted(
        path for path in directory.iterdir() if filename_pattern.match(path.name)
    )
    if not paths:
        msg = f"{year}년 옐로우 택시 월별 Parquet 파일을 찾을 수 없습니다: {raw_dir}"
        raise TaxiDataLoadError(msg)
    LOGGER.debug(
        "옐로우 택시 원천 파일 발견",
        extra={"raw_dir": str(raw_dir), "year": year, "file_count": len(paths)},
    )
    return paths
