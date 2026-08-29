"""명시적인 provider 중립 AI 런타임 설정 모듈."""

from __future__ import annotations

import urllib.parse
from typing import Literal

from pydantic import AnyHttpUrl, Field, SecretStr, field_validator

from hmda_reliability.runtime_ai.contracts import RuntimeAIContract


def _sanitize_base_url(url: str) -> str:
    """사용자 정보 또는 쿼리 파라미터가 제거된 정규화된 기본 URL을 반환한다."""
    parsed = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


class RuntimeAISettings(RuntimeAIContract):
    """호출자가 명시적으로 제공하는 provider 런타임 설정."""

    base_url: AnyHttpUrl
    api_key: SecretStr
    model: str
    timeout_seconds: float = Field(default=30.0, gt=0, le=300)
    max_retries: int = Field(default=1, ge=0, le=5)
    temperature: Literal[0] = 0
    max_output_tokens: int = Field(default=1024, gt=0, le=32_768)
    max_output_bytes: int = Field(default=32_768, gt=0, le=1_048_576)

    @field_validator("base_url")
    @classmethod
    def _validate_base_url(cls, value: AnyHttpUrl) -> AnyHttpUrl:
        if value.username is not None or value.password is not None:
            msg = "base_url must not contain credentials"
            raise ValueError(msg)
        if value.query:
            msg = "base_url must not contain query parameters"
            raise ValueError(msg)
        if value.fragment:
            msg = "base_url must not contain URL fragments"
            raise ValueError(msg)
        return value

    @field_validator("api_key")
    @classmethod
    def _validate_api_key(cls, value: SecretStr) -> SecretStr:
        if not value.get_secret_value().strip():
            msg = "api_key must be non-empty"
            raise ValueError(msg)
        return value

    @field_validator("model")
    @classmethod
    def _validate_model(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            msg = "model must be non-empty"
            raise ValueError(msg)
        return normalized

    def sanitized_configuration(self) -> dict[str, str | float | int]:
        """자격 증명이 제거된 제한된 provider 설정을 반환한다."""

        return {
            "base_url": _sanitize_base_url(str(self.base_url)),
            "model": self.model,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "temperature": self.temperature,
            "max_output_tokens": self.max_output_tokens,
            "max_output_bytes": self.max_output_bytes,
        }
