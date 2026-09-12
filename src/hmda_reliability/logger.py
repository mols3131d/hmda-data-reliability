"""프로젝트 공통 로깅 헬퍼.

CLI 스크립트 및 도메인 모듈에서 사용할 표준 로거 인스턴스 취득과
루트 로거 설정을 담당한다.
"""

from __future__ import annotations

import logging

DEFAULT_LOG_FORMAT = "%(levelname)s %(message)s"


def get_logger(name: str) -> logging.Logger:
    """모듈 이름에 맞는 로거를 반환한다.

    표준 라이브러리 `logging.getLogger`의 위임 함수로, 동일한 `name`에 대해
    항상 동일한 `logging.Logger` 싱글톤 인스턴스를 반환한다.

    Args:
        name: 로거 네임스페이스 식별자 (보통 `__name__` 전달).

    Returns:
        지정된 이름으로 바인딩된 `logging.Logger` 인스턴스.
    """

    return logging.getLogger(name)


def configure_logging(level: int = logging.INFO) -> None:
    """CLI 진입점의 기본 로깅을 설정한다.

    루트 로거에 표준 포맷(`DEFAULT_LOG_FORMAT`)과 지정된 로그 레벨을 적용한다.
    `logging.basicConfig` 특성상 이미 루트 로거에 핸들러가 구성되어 있다면
    추가 호출 시 기존 핸들러 설정을 덮어쓰지 않는다(멱등적 진입 보장).

    Args:
        level: 루트 로거에 설정할 로깅 레벨 (기본값: `logging.INFO`).
    """

    logging.basicConfig(level=level, format=DEFAULT_LOG_FORMAT)
