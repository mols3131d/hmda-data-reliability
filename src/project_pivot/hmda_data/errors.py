"""HMDA source-to-Bronze와 합성 입력 생성에서 노출하는 domain exceptions."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class HMDADataFoundationError(Exception):
    """HMDA data domain exception의 공통 base."""

    def __init__(
        self,
        message: str,
        *,
        context: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.context = dict(context or {})


class HMDADataLoadError(HMDADataFoundationError):
    """원천 발견·읽기 또는 Bronze 적재를 완료할 수 없을 때 발생한다."""


class HMDAStalePartitionError(HMDADataLoadError):
    """Expected-state 파티션 교체가 stale identity로 거부될 때 발생한다."""


class HMDADataValidationError(HMDADataFoundationError):
    """원천 또는 EDA input의 column/type/cardinality validation 실패를 나타낸다."""


class SyntheticCaseError(HMDADataFoundationError):
    """합성 결함 입력·parameter·출력 생성 contract를 만족하지 못할 때 발생한다."""
