"""데이터 작업 실행 예외."""

from collections.abc import Mapping
from typing import Any


class DataOperationError(Exception):
    """Caller가 처리할 수 있는 data operation 실패를 표현한다.

    ``context``에는 command, return code, artifact path처럼 message만으로 부족한
    structured diagnostic을 담아 caller가 실패 원인을 식별할 수 있게 한다.
    """

    def __init__(
        self,
        message: str,
        *,
        context: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.context = dict(context or {})
