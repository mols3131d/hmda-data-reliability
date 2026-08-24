"""프로젝트 공통 로깅 헬퍼."""

from __future__ import annotations

import logging

DEFAULT_LOG_FORMAT = "%(levelname)s %(message)s"


def get_logger(name: str) -> logging.Logger:
    """모듈 이름에 맞는 로거를 반환한다."""

    return logging.getLogger(name)


def configure_logging(level: int = logging.INFO) -> None:
    """CLI 진입점의 기본 로깅을 설정한다."""

    logging.basicConfig(level=level, format=DEFAULT_LOG_FORMAT)
