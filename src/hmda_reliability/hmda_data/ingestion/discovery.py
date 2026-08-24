"""HMDA raw directory에서 loadable source set을 결정한다."""

from __future__ import annotations

from pathlib import Path

from hmda_reliability.hmda_data.errors import HMDADataLoadError
from hmda_reliability.hmda_data.ingestion._common import _LOGGER

_SUPPORTED_HMDA_EXTENSIONS = frozenset({".csv", ".parquet"})


def discover_hmda_files(raw_dir: str | Path) -> list[Path]:
    """지원 파일을 deterministic filename order로 반환한다.

    Unsupported regular files는 진단 로그만 남기고 제외한다. Directory가 없거나
    지원 파일이 하나도 없으면 ``HMDADataLoadError``를 발생시킨다.
    """

    directory = Path(raw_dir)
    if not directory.is_dir():
        msg = f"HMDA 원천 디렉터리를 찾을 수 없습니다: {raw_dir}"
        raise HMDADataLoadError(msg, context={"raw_dir": str(raw_dir)})

    supported_paths: list[Path] = []
    ignored_paths: list[str] = []

    # 동일 directory에서 ingestion input order가 재현 가능하도록 파일명으로 고정한다.
    for path in sorted(directory.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() in _SUPPORTED_HMDA_EXTENSIONS:
            supported_paths.append(path)
        else:
            ignored_paths.append(path.name)

    # 지원 파일이 하나라도 있으면 unrelated files는 ingestion을 막지 않는다.
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
