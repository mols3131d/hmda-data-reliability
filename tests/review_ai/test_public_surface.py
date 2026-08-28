"""Public Review AI and Runtime AI surface smoke tests."""

from __future__ import annotations

import pytest

from hmda_reliability import reliability, review_ai, runtime_ai

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "name",
    [
        "AgenticInvocationEvidence",
        "AgenticReviewInput",
        "AgenticReviewOutput",
        "AgenticReviewResult",
        "AgenticReviewValidation",
        "InvocationEvidenceStore",
        "PromptIdentity",
        "render_review_prompt",
        "review_null_spike",
        "validate_agentic_review",
    ],
)
def test_review_ai_explicitly_exports_review_surface(name: str) -> None:
    assert hasattr(review_ai, name)
    assert name in review_ai.__all__


@pytest.mark.parametrize(
    "name",
    [
        "OpenAICompatibleAdapter",
        "RuntimeAISettings",
        "ProviderResponse",
        "ProviderUnavailableError",
        "RenderedPrompt",
    ],
)
def test_runtime_ai_explicitly_exports_runtime_surface(name: str) -> None:
    assert hasattr(runtime_ai, name)
    assert name in runtime_ai.__all__


def test_reliability_does_not_reexport_ai_surfaces() -> None:
    for name in (
        "AgenticReviewInput",
        "AgenticReviewResult",
        "OpenAICompatibleAdapter",
        "review_null_spike",
    ):
        assert not hasattr(reliability, name)
        assert name not in reliability.__all__
