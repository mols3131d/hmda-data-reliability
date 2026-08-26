"""Explicit runtime settings for bounded agentic review."""

from __future__ import annotations

from typing import Literal

from pydantic import AnyHttpUrl, Field, SecretStr, field_validator

from hmda_reliability.reliability.contracts.base import ReliabilityContract


class AgenticReviewSettings(ReliabilityContract):
    """Provider settings supplied explicitly by the caller."""

    base_url: AnyHttpUrl
    api_key: SecretStr
    model: str
    timeout_seconds: float = Field(default=30.0, gt=0, le=300)
    max_retries: int = Field(default=1, ge=0, le=5)
    temperature: Literal[0] = 0
    max_output_tokens: int = Field(default=1024, gt=0, le=32_768)
    max_prompt_bytes: int = Field(default=65_536, gt=0, le=1_048_576)
    max_output_bytes: int = Field(default=32_768, gt=0, le=1_048_576)

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
        """Return the bounded provider configuration without credentials."""

        return {
            "base_url": str(self.base_url),
            "model": self.model,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "temperature": self.temperature,
            "max_output_tokens": self.max_output_tokens,
            "max_prompt_bytes": self.max_prompt_bytes,
            "max_output_bytes": self.max_output_bytes,
        }
