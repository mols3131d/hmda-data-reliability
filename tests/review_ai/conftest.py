"""Deterministic null-spike review fixtures."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, NamedTuple

import pytest
from langfuse.api import Prompt_Chat
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
from hmda_reliability.review_ai.staged.contracts import STAGE_IDS, StageId

NATIVE_INSTRUCTION = (
    "한국어로 작성한다. 일반 텍스트로 답한다. "
    "승인을 부여하거나 실행 권한이 있다고 주장하지 않는다. "
    "식별 정보와 수치를 모두 보존한다."
)
NATIVE_QUESTIONS: dict[StageId, str] = {
    "evidence_review": "제공된 근거와 수치를 검토한다.",
    "draft_critique": "초안의 조치와 검증 계획을 비판적으로 검토한다.",
    "synthesis": "이전 검토를 종합하고 사람에게 남은 판단을 설명한다.",
}


def native_prompt(stage_id: StageId, *, version: int = 7) -> ChatPromptClient:
    """Langfuse가 모듈 참조를 해석해 반환한 chat prompt를 고정한다."""
    return ChatPromptClient(
        Prompt_Chat(
            name=f"hmda-review-ai/{stage_id}",
            version=version,
            prompt=[
                {"role": "system", "content": NATIVE_INSTRUCTION},
                {"type": "placeholder", "name": "history"},
                {"role": "system", "content": NATIVE_QUESTIONS[stage_id]},
            ],
            config={"model": "test-model", "max_tokens": 2048},
            labels=["production"],
            tags=["review-ai"],
        )
    )


class NativeObservation:
    def __init__(self, client: NativeClient, values: dict[str, Any]) -> None:
        self.client = client
        self.values = values
        self.updates: list[dict[str, Any]] = []
        self.active = False

    def __enter__(self):
        self.active = True
        return self

    def __exit__(self, *_):
        self.active = False

    def update(self, **values):
        assert self.active, "실제 호출을 포함한 관측 context 안에서 갱신한다"
        self.updates.append(values)


class NativeClient:
    def __init__(self) -> None:
        self.prompts = {stage_id: native_prompt(stage_id) for stage_id in STAGE_IDS}
        self.prompt_requests: list[tuple[str, dict[str, Any]]] = []
        self.observations: list[NativeObservation] = []

    def get_prompt(self, name, **kwargs):
        self.prompt_requests.append((name, kwargs))
        return self.prompts[name.rsplit("/", 1)[-1]]

    def start_as_current_observation(self, **values):
        observation = NativeObservation(self, values)
        self.observations.append(observation)
        return observation


@pytest.fixture(autouse=True)
def native_langfuse(monkeypatch: pytest.MonkeyPatch) -> NativeClient:
    """일반 pytest는 원격 prompt와 trace I/O만 대체하고 SDK compile은 실행한다."""
    from hmda_reliability.review_ai.staged import prompt, service

    client = NativeClient()
    monkeypatch.setattr(prompt, "get_client", lambda: client, raising=False)
    monkeypatch.setattr(service, "get_client", lambda: client, raising=False)
    return client


class NullSpikeReviewMaterial(NamedTuple):
    detection: DetectionResult
    draft: RemediationDraft


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
