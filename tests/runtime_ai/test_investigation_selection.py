from unittest.mock import Mock

import pytest

from hmda_reliability.runtime_ai.selection import (
    CodexSettings,
    cli_provider_settings,
    resolve_investigation_provider,
)
from hmda_reliability.runtime_ai.settings import RuntimeAISettings

pytestmark = pytest.mark.unit


def test_key_alone_never_selects_a_compatible_endpoint():
    settings = cli_provider_settings(None, None, None, None, {"OPENAI_API_KEY": "demo"})
    assert isinstance(settings, CodexSettings)
    assert settings.model == "gpt-6-luna"
    assert resolve_investigation_provider(None, None)[0].model == "gpt-6-luna"
    assert "base_url" not in settings.sanitized_configuration()


def test_explicit_ollama_ignores_an_unrelated_cloud_key_and_endpoint():
    settings = cli_provider_settings(
        "ollama",
        None,
        None,
        None,
        {"OPENAI_BASE_URL": "https://example.org/v1", "OPENAI_API_KEY": "other"},
    )
    assert isinstance(settings, RuntimeAISettings)
    assert str(settings.base_url) == "http://localhost:11434/v1"
    assert settings.api_key.get_secret_value() == "local"
    assert settings.model == "qwen3.5:4b-8k-local"


def test_explicitly_supplied_codex_and_compatible_url_conflict():
    with pytest.raises(ValueError, match="base-url"):
        cli_provider_settings("codex", None, "http://localhost:11434/v1", None, {})


def test_api_preserves_explicit_provider_even_when_settings_are_supplied():
    settings = cli_provider_settings(
        None,
        "model-x",
        None,
        None,
        {"OPENAI_BASE_URL": "https://example.org/v1", "OPENAI_API_KEY": "demo"},
    )
    adapter = Mock()
    assert resolve_investigation_provider(settings, adapter) == (settings, adapter)


def test_only_injected_adapter_supplies_its_actual_model_and_record_limits():
    from hmda_reliability.runtime_ai.codex import CodexAdapter

    settings = CodexSettings(model="explicit", max_output_bytes=128)
    adapter = CodexAdapter(settings)
    assert resolve_investigation_provider(None, adapter) == (settings, adapter)
