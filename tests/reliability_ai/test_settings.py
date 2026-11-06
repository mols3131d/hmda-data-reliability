"""Reliability AI configuration tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from hmda_reliability.reliability_ai.settings import ReliabilityAISettings

pytestmark = pytest.mark.unit


def test_reliability_ai_settings_default_limits() -> None:
    settings = ReliabilityAISettings()

    assert settings.max_prompt_bytes == 65_536
    assert settings.max_tool_calls == 5
    assert settings.workflow_budget_seconds == 60.0
    assert settings.sanitized_configuration() == {
        "max_prompt_bytes": 65_536,
        "max_tool_calls": 5,
        "workflow_budget_seconds": 60.0,
    }


@pytest.mark.parametrize("max_prompt_bytes", [0, 1_048_577])
def test_settings_reject_invalid_prompt_byte_limits(
    max_prompt_bytes: int,
) -> None:
    with pytest.raises(ValidationError):
        ReliabilityAISettings(max_prompt_bytes=max_prompt_bytes)
