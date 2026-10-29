"""Public Review AI and Runtime AI surface smoke tests."""

from __future__ import annotations

from importlib.util import find_spec
from pathlib import Path

import pytest

from hmda_reliability import reliability, review_ai, runtime_ai
from hmda_reliability.review_ai import service
from hmda_reliability.runtime_ai.settings import RuntimeAISettings

from .conftest import NullSpikeReviewMaterial
from .test_staged_service import TEXTS, TextProvider, response

pytestmark = pytest.mark.unit


def test_review_ai_exports_only_consumer_surface() -> None:
    assert set(review_ai.__all__) == {
        "AgenticReviewInput",
        "BoundedReviewContext",
        "HumanDecision",
        "ReviewValueAssessment",
        "RUBRIC_V1",
        "StageAnswer",
        "StagedExecutionSettings",
        "StagedReviewOutput",
        "StagedReviewResult",
        "ReviewValueComparisonEvidence",
        "build_bounded_review_context",
        "compare_review_value",
        "review_null_spike",
        "review_null_spike_staged",
    }


@pytest.mark.parametrize(
    "module",
    ["legacy", "prompt.legacy", "diagnostics", "validator", "evaluation.langfuse"],
)
def test_removed_review_implementations_are_not_available(module: str) -> None:
    assert find_spec(f"hmda_reliability.review_ai.{module}") is None


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


@pytest.mark.parametrize("entrypoint", [review_ai, service], ids=["package", "service"])
def test_general_review_entrypoints_collect_current_text_without_a_prompt_version(
    entrypoint,
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
) -> None:
    material = null_spike_review_material
    provider = TextProvider([response(text) for text in TEXTS])
    result = entrypoint.review_null_spike(
        incident=material.detection.incident,
        evidence=[material.detection.evidence],
        draft=material.draft,
        project_revision="current-entrypoint",
        settings=RuntimeAISettings(
            base_url="http://localhost:11434/v1",
            api_key="test",
            model="test",
            max_retries=0,
        ),
        provider=provider,
        artifact_root=tmp_path,
    )
    assert result.status == "completed"
    assert result.output is not None and result.output_path.is_file()
    assert [stage.text for stage in result.output.stages] == list(TEXTS)
    assert len(provider.calls) == 3
    for index, messages in enumerate(provider.calls):
        assert [
            message.content for message in messages if message.role == "assistant"
        ] == list(TEXTS[:index])
