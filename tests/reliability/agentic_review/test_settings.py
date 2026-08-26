"""Explicit, bounded provider configuration contract tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from hmda_reliability.reliability.agentic_review import settings as settings_module

pytestmark = pytest.mark.unit


def _valid_values() -> dict[str, object]:
    return {
        "base_url": "http://localhost:11434/v1",
        "api_key": "local-test-key",
        "model": "test-model",
    }


def test_settings_require_explicit_identity_and_use_bounded_defaults() -> None:
    settings_type = settings_module.AgenticReviewSettings

    settings = settings_type.model_validate(_valid_values())

    assert str(settings.base_url) == "http://localhost:11434/v1"
    assert settings.api_key.get_secret_value() == "local-test-key"
    assert settings.model == "test-model"
    assert settings.timeout_seconds == 30
    assert settings.max_retries == 1
    assert settings.temperature == 0
    assert settings.max_output_tokens == 1024
    assert settings.max_prompt_bytes == 65_536
    assert settings.max_output_bytes == 32_768


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("base_url", ""),
        ("base_url", "not-a-url"),
        ("api_key", "   "),
        ("model", "   "),
        ("timeout_seconds", 0),
        ("max_retries", -1),
        ("max_retries", 6),
        ("temperature", 0.1),
        ("max_output_tokens", 0),
        ("max_prompt_bytes", 0),
        ("max_output_bytes", 0),
    ],
)
def test_settings_reject_invalid_or_unbounded_values(
    field: str,
    value: object,
) -> None:
    values = _valid_values()
    values[field] = value

    with pytest.raises(ValidationError):
        settings_module.AgenticReviewSettings.model_validate(values)


def test_sanitized_configuration_excludes_credentials() -> None:
    settings = settings_module.AgenticReviewSettings.model_validate(_valid_values())

    sanitized = settings.sanitized_configuration()

    assert sanitized == {
        "base_url": "http://localhost:11434/v1",
        "model": "test-model",
        "timeout_seconds": 30.0,
        "max_retries": 1,
        "temperature": 0.0,
        "max_output_tokens": 1024,
        "max_prompt_bytes": 65_536,
        "max_output_bytes": 32_768,
    }
    assert "api_key" not in sanitized
    assert "credential" not in sanitized
    assert "local-test-key" not in repr(sanitized)


def test_public_settings_do_not_read_provider_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HMDA_AGENTIC_REVIEW_BASE_URL", "http://example.test/v1")
    monkeypatch.setenv("HMDA_AGENTIC_REVIEW_API_KEY", "environment-secret")
    monkeypatch.setenv("HMDA_AGENTIC_REVIEW_MODEL", "environment-model")

    with pytest.raises(ValidationError):
        settings_module.AgenticReviewSettings.model_validate({})
