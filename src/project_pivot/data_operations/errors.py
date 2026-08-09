"""데이터 작업 실행 예외."""

from collections.abc import Mapping
from typing import Any


class DataOperationError(Exception):
    """데이터 작업 실행에 실패했다."""

    def __init__(
        self,
        message: str,
        *,
        context: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.context = dict(context or {})
