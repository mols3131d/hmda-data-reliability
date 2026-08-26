"""Public reliability agentic-review surface smoke tests."""

from __future__ import annotations

import pytest

from hmda_reliability import reliability
from hmda_reliability.reliability import agentic_review

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "name",
    [
        "AgenticInvocationEvidence",
        "AgenticReviewInput",
        "AgenticReviewOutput",
        "AgenticReviewResult",
        "AgenticReviewSettings",
        "AgenticReviewValidation",
        "InvocationEvidenceStore",
        "OpenAICompatibleAdapter",
        "PromptIdentity",
        "render_review_prompt",
        "review_null_spike",
        "validate_agentic_review",
    ],
)
def test_reliability_explicitly_exports_agentic_review_surface(name: str) -> None:
    assert getattr(reliability, name) is getattr(agentic_review, name)
    assert name in reliability.__all__
