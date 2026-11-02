"""논리적 호출 evidence 계약 모듈."""

from __future__ import annotations

import urllib.parse
from typing import Literal

from pydantic import Field, field_validator

from hmda_reliability.reliability.contracts.base import ReliabilityContract


class SanitizedAgenticReviewConfiguration(ReliabilityContract):
    """자격 증명이 제거된 영속화 가능한 provider 설정 계약."""

    base_url: str = Field(min_length=1, max_length=2048)
    model: str = Field(min_length=1, max_length=512)
    timeout_seconds: float = Field(gt=0, le=300)
    connect_timeout_seconds: float | None = Field(default=None, gt=0, le=300)
    read_timeout_seconds: float | None = Field(default=None, gt=0, le=3600)
    max_retries: int = Field(ge=0, le=5)
    temperature: Literal[0]
    max_output_tokens: int = Field(gt=0, le=32_768)
    max_prompt_bytes: int = Field(gt=0, le=1_048_576)
    max_output_bytes: int = Field(gt=0, le=1_048_576)

    @field_validator("base_url")
    @classmethod
    def _validate_base_url(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            msg = "base_url must be non-empty"
            raise ValueError(msg)
        parsed = urllib.parse.urlsplit(normalized)
        if parsed.username is not None or parsed.password is not None:
            msg = "sanitized base_url must not contain credentials"
            raise ValueError(msg)
        if parsed.query:
            msg = "sanitized base_url must not contain query parameters"
            raise ValueError(msg)
        if parsed.fragment:
            msg = "sanitized base_url must not contain URL fragments"
            raise ValueError(msg)
        return normalized
