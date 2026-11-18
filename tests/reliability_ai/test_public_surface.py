"""Public Reliability AI and Runtime AI surface smoke tests."""

from __future__ import annotations

from importlib.util import find_spec

import pytest

from hmda_reliability import reliability, reliability_ai, runtime_ai

pytestmark = pytest.mark.unit


def test_reliability_ai_exports_only_consumer_surface() -> None:
    expected_exports = {
        "ActionProposal",
        "AgenticReviewInput",
        "BoundedReviewContext",
        "DEFAULT_INVESTIGATION_TOOLS",
        "ExecutionReceipt",
        "InvestigationFinding",
        "InvestigationHypothesis",
        "InvestigationInput",
        "InvestigationResult",
        "InvestigationTurnRecord",
        "InvestigationUncertainty",
        "NullSpikeFacts",
        "ReliabilityAISettings",
        "ReportEnvelope",
        "TaskEnvelope",
        "ToolCallRecord",
        "ToolRegistry",
        "build_bounded_review_context",
        "context",
        "contracts",
        "evidence",
        "execute_delegated_task",
        "execution",
        "investigate_incident",
        "investigation",
        "settings",
    }
    assert set(reliability_ai.__all__) == expected_exports


def test_removed_review_ai_is_not_available() -> None:
    assert find_spec("hmda_reliability.review_ai") is None


def test_runtime_ai_exports_only_explicit_settings() -> None:
    assert runtime_ai.__all__ == ["RuntimeAISettings"]


def test_reliability_does_not_reexport_ai_surfaces() -> None:
    for name in (
        "AgenticReviewInput",
        "InvestigationResult",
        "OpenAICompatibleAdapter",
        "investigate_incident",
        "execute_delegated_task",
    ):
        assert not hasattr(reliability, name)
        assert name not in reliability.__all__
