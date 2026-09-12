"""명시적인 provider 중립 AI 런타임 설정 모듈."""

from __future__ import annotations

import urllib.parse
from typing import Literal

from pydantic import AnyHttpUrl, Field, SecretStr, field_validator

from hmda_reliability.runtime_ai.contracts import RuntimeAIContract


def _sanitize_base_url(url: str) -> str:
    """사용자 정보 또는 쿼리 파라미터가 제거된 정규화된 기본 URL을 반환한다.

    IPv6 호스트 리터럴(`[::1]:11434`)의 넷록(netloc)을 보존하며,
    쿼리 스트링과 프래그먼트를 배제한 `(scheme, netloc, path)` 튜플로 재조합한다.
    """
    parsed = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))


class RuntimeAISettings(RuntimeAIContract):
    """호출자가 명시적으로 제공하는 provider 런타임 설정.

    환경 변수를 암묵적으로 읽지 않으며, 호출자가 명시적으로 전달해야 한다.
    제공자 기본 엔드포인트(`base_url`), 자격 증명(`api_key`), 모델명(`model`) 외에
    타임아웃, 최대 재시도 횟수, 토큰 및 바이트 한도에 대해 안전한 기본값을 갖는다.
    """

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
        """자격 증명(`api_key`)이 안전하게 배제된 제한된 provider 설정을 반환한다.

        로깅, 감사, 메트릭에 안전하게 포함할 수 있도록 `api_key`를 제외하고
        정규화된 `base_url`과 숫자 제약만을 담은 사전 객체를 반환한다.
        """
        return {
            "base_url": _sanitize_base_url(str(self.base_url)),
            "model": self.model,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "temperature": self.temperature,
            "max_output_tokens": self.max_output_tokens,
            "max_output_bytes": self.max_output_bytes,
        }
