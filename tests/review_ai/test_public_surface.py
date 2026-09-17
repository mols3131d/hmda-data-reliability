"""Public Review AI and Runtime AI surface smoke tests."""

from __future__ import annotations

import pytest

from hmda_reliability import reliability, review_ai, runtime_ai

pytestmark = pytest.mark.unit


def test_review_ai_exports_only_consumer_surface() -> None:
    assert set(review_ai.__all__) == {
        "AgenticReviewInput",
        "AgenticReviewOutput",
        "AgenticReviewResult",
        "AgenticReviewUtilityContribution",
        "BoundedReviewContext",
        "HumanDecision",
        "HumanUtilityEvaluation",
        "PromptIdentity",
        "RUBRIC_V1",
        "UtilityControl",
        "UtilityComparisonEvidence",
        "UtilityProofBundle",
        "UtilityProofCase",
        "build_bounded_review_context",
        "compare_utility_evaluations",
        "review_null_spike",
        "validate_quality_basis",
    }


def test_runtime_ai_exports_only_explicit_settings() -> None:
    assert runtime_ai.__all__ == ["RuntimeAISettings"]


def test_reliability_does_not_reexport_ai_surfaces() -> None:
    for name in (
        "AgenticReviewInput",
        "AgenticReviewResult",
        "OpenAICompatibleAdapter",
        "review_null_spike",
    ):
        assert not hasattr(reliability, name)
        assert name not in reliability.__all__
