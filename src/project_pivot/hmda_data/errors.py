"""HMDA 데이터 파운데이션 예외."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class HMDADataFoundationError(Exception):
    """HMDA 데이터 파운데이션 기본 예외."""

    def __init__(
        self,
        message: str,
        *,
        context: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.context = dict(context or {})


class HMDADataLoadError(HMDADataFoundationError):
    """HMDA 원천 데이터 적재에 실패했다."""


class HMDAStalePartitionError(HMDADataLoadError):
    """HMDA target partition이 caller의 expected state와 다르다."""


class HMDADataValidationError(HMDADataFoundationError):
    """HMDA 원천 데이터 검증에 실패했다."""


class SyntheticCaseError(HMDADataFoundationError):
    """HMDA 합성 결함 데이터 생성에 실패했다."""
