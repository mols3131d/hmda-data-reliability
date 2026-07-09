"""HMDA 원천 파일 발견."""

from __future__ import annotations

from pathlib import Path

from project_pivot.hmda_data.errors import HMDADataLoadError
from project_pivot.hmda_data.ingestion._common import _LOGGER

_SUPPORTED_HMDA_EXTENSIONS = frozenset({".csv", ".parquet"})


def discover_hmda_files(raw_dir: str | Path) -> list[Path]:
    """지원하는 HMDA CSV/Parquet 원천 파일을 정렬해 찾는다."""

    directory = Path(raw_dir)
    if not directory.is_dir():
        msg = f"HMDA 원천 디렉터리를 찾을 수 없습니다: {raw_dir}"
        raise HMDADataLoadError(msg, context={"raw_dir": str(raw_dir)})

    supported_paths: list[Path] = []
    ignored_paths: list[str] = []

    for path in sorted(directory.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() in _SUPPORTED_HMDA_EXTENSIONS:
            supported_paths.append(path)
        else:
            ignored_paths.append(path.name)

    if ignored_paths:
        _LOGGER.info(
            "지원하지 않는 HMDA 원천 파일 제외",
            extra={"raw_dir": str(raw_dir), "ignored_files": ignored_paths},
        )
    if not supported_paths:
        msg = f"HMDA CSV 또는 Parquet 파일을 찾을 수 없습니다: {raw_dir}"
        raise HMDADataLoadError(msg, context={"raw_dir": str(raw_dir)})

    _LOGGER.debug(
        "HMDA 원천 파일 발견",
        extra={"raw_dir": str(raw_dir), "file_count": len(supported_paths)},
    )
    return supported_paths
