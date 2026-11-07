"""신뢰성 AI 테스트 픽스처 모듈."""

from __future__ import annotations

from datetime import UTC, datetime
from importlib.resources import files
from typing import NamedTuple
from unittest.mock import MagicMock

import pytest
from langfuse.api.prompts.types.prompt import Prompt_Chat
from langfuse.model import ChatPromptClient

from hmda_reliability.reliability import (
    DetectionRequest,
    DetectionResult,
    FreshnessMeasurementStatus,
    ProfileSnapshot,
    RemediationDraft,
    RemediationDraftRequest,
    create_remediation_draft,
    detect_basic_incidents,
)


class NullSpikeReviewMaterial(NamedTuple):
    detection: DetectionResult
    draft: RemediationDraft


@pytest.fixture(autouse=True)
def native_prompt_client(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    from hmda_reliability.reliability_ai.investigation import service

    resources = files("hmda_reliability.reliability_ai.prompt")
    system = "\n\n".join(
        resources.joinpath(path).read_text(encoding="utf-8")
        for path in (
            "investigation.md",
            "guidance/numeric_fidelity.md",
            "guidance/evidence_review.md",
            "policies/language.md",
            "policies/advisory.md",
        )
    )
    native = ChatPromptClient(
        Prompt_Chat(
            name="hmda-reliability-ai/investigation",
            version=7,
            prompt=[
                {"role": "system", "content": system},
                {"role": "user", "content": "{{canonical_input}}"},
                {"type": "placeholder", "name": "history"},
            ],
            config={},
            labels=["production"],
            tags=[],
        )
    )
    client = MagicMock()
    client.get_prompt.return_value = native
    client.start_observation.return_value.trace_id = "a" * 32
    client.start_observation.return_value.id = "b" * 16
    monkeypatch.setattr(service, "get_client", lambda: client, raising=False)
    return client


@pytest.fixture
def null_spike_review_material() -> NullSpikeReviewMaterial:
    observed_at = datetime(2026, 8, 27, 0, 0, tzinfo=UTC)
    baseline = ProfileSnapshot(
        snapshot_id="profile-baseline-2025",
        asset_name="raw.hmda_loans",
        partition="2025",
        observed_at=observed_at,
        row_count=100,
        null_rates={"income": 0.01},
        schema_hash="sha256:stable",
        freshness_at=None,
        freshness_status=FreshnessMeasurementStatus.UNAVAILABLE,
    )
    current = ProfileSnapshot(
        snapshot_id="profile-current-2025",
        asset_name="raw.hmda_loans",
        partition="2025",
        observed_at=observed_at,
        row_count=100,
        null_rates={"income": 0.21},
        schema_hash="sha256:stable",
        freshness_at=None,
        freshness_status=FreshnessMeasurementStatus.UNAVAILABLE,
    )
    detection = detect_basic_incidents(
        DetectionRequest(baseline=baseline, current=current)
    )[0]
    draft = create_remediation_draft(
        RemediationDraftRequest(
            incident=detection.incident,
            evidence=detection.evidence,
        )
    )
    return NullSpikeReviewMaterial(detection=detection, draft=draft)
