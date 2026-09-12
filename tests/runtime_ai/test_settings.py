"""Explicit, bounded provider configuration contract tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from hmda_reliability.runtime_ai import settings as settings_module

pytestmark = pytest.mark.unit


def _valid_values() -> dict[str, object]:
    """검증 통과가 보장되는 최소 유효 설정 필드 사전."""
    return {
        "base_url": "http://localhost:11434/v1",
        "api_key": "local-test-key",
        "model": "test-model",
    }


def test_settings_require_explicit_identity_and_use_bounded_defaults() -> None:
    """설정이 필수 식별자를 요구하고 상한이 있는 안전한 기본값을 사용하는지 검증한다."""
    settings_type = settings_module.RuntimeAISettings

    settings = settings_type.model_validate(_valid_values())

    assert str(settings.base_url) == "http://localhost:11434/v1"
    assert settings.api_key.get_secret_value() == "local-test-key"
    assert settings.model == "test-model"
    assert settings.timeout_seconds == 30
    assert settings.max_retries == 1
    assert settings.temperature == 0
    assert settings.max_output_tokens == 1024
    assert settings.max_output_bytes == 32_768


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("base_url", ""),
        ("base_url", "not-a-url"),
        ("base_url", "http://user:secret@localhost:11434/v1"),
        ("base_url", "https://alice:pass123@example.com/v1"),
        ("base_url", "http://localhost:11434/v1?api_key=secret-token"),
        ("base_url", "https://example.com/v1?token=xyz"),
        ("base_url", "http://localhost:11434/v1?secret=xyz"),
        ("base_url", "https://example.com/v1?access_token=secret-value"),
        ("base_url", "https://example.com/v1?client_secret=secret-value"),
        ("base_url", "http://localhost:11434/v1?mode=eval"),
        ("base_url", "https://example.com/v1#token"),
        ("base_url", "http://localhost:11434/v1#secret"),
        ("api_key", "   "),
        ("model", "   "),
        ("timeout_seconds", 0),
        ("max_retries", -1),
        ("max_retries", 6),
        ("temperature", 0.1),
        ("max_output_tokens", 0),
        ("max_output_bytes", 0),
    ],
)
def test_settings_reject_invalid_or_unbounded_values(
    field: str,
    value: object,
) -> None:
    """URL 자격 증명, 쿼리, 프래그먼트, 공백 키 및 범위 초과 설정을 거부한다."""
    values = _valid_values()
    values[field] = value

    with pytest.raises(ValidationError):
        settings_module.RuntimeAISettings.model_validate(values)


def test_sanitized_configuration_excludes_credentials() -> None:
    """정제된 설정 딕셔너리에서 api_key 및 자격 증명이 배제되는지 검증한다."""
    settings = settings_module.RuntimeAISettings.model_validate(_valid_values())

    sanitized = settings.sanitized_configuration()

    assert sanitized == {
        "base_url": "http://localhost:11434/v1",
        "model": "test-model",
        "timeout_seconds": 30.0,
        "max_retries": 1,
        "temperature": 0.0,
        "max_output_tokens": 1024,
        "max_output_bytes": 32_768,
    }
    assert "api_key" not in sanitized
    assert "credential" not in sanitized
    assert "local-test-key" not in repr(sanitized)


def test_sanitized_configuration_preserves_ipv6_authority() -> None:
    """정제 시 IPv6 호스트 리터럴의 넷록(netloc)이 손실되지 않고 보존되는지 검증한다."""
    values = _valid_values()
    values["base_url"] = "http://[::1]:11434/v1"
    settings = settings_module.RuntimeAISettings.model_validate(values)

    sanitized = settings.sanitized_configuration()

    assert sanitized["base_url"] == "http://[::1]:11434/v1"


def test_public_settings_do_not_read_provider_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """환경 변수가 주어져도 읽지 않고 누락 필드에 대해 ValidationError를 낸다."""
    monkeypatch.setenv("HMDA_AGENTIC_REVIEW_BASE_URL", "http://example.test/v1")
    monkeypatch.setenv("HMDA_AGENTIC_REVIEW_API_KEY", "environment-secret")
    monkeypatch.setenv("HMDA_AGENTIC_REVIEW_MODEL", "environment-model")

    with pytest.raises(ValidationError):
        settings_module.RuntimeAISettings.model_validate({})
