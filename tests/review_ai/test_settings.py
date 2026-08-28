"""Review-owned prompt preflight configuration tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from hmda_reliability.review_ai.settings import ReviewAISettings

pytestmark = pytest.mark.unit


def test_review_settings_own_the_prompt_byte_limit() -> None:
    settings = ReviewAISettings()

    assert settings.max_prompt_bytes == 65_536
    assert settings.sanitized_configuration() == {"max_prompt_bytes": 65_536}


@pytest.mark.parametrize("max_prompt_bytes", [0, 1_048_577])
def test_review_settings_reject_invalid_prompt_byte_limits(
    max_prompt_bytes: int,
) -> None:
    with pytest.raises(ValidationError):
        ReviewAISettings(max_prompt_bytes=max_prompt_bytes)
