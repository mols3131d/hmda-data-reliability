"""단계별 원문 수집, 코드 직렬화와 부분 실패 보존 계약."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

import pytest

from hmda_reliability.review_ai.settings import ReviewAISettings
from hmda_reliability.review_ai.staged import service as staged_service
from hmda_reliability.review_ai.store import (
    InvocationEvidenceWriteError,
    InvocationResponseStore,
)
from hmda_reliability.runtime_ai.contracts import (
    ChatMessage,
    ProviderResponse,
    ProviderResponseMetadata,
)
from hmda_reliability.runtime_ai.provider import ProviderUnavailableError
from hmda_reliability.runtime_ai.settings import RuntimeAISettings

from .conftest import NullSpikeReviewMaterial

TEXTS = (
    '  첫 검토: "수치"와 근거를 확인한다.\n{"형식": "JSON처럼 보여도 원문"}\n',
    "두 번째 검토: 초안의 검증 조치는 아직 계획이다.\n",
    "세 번째 검토: 원천 완전성 확인 결과에 따라 판단한다.\n",
)


def response(
    text: str, finish_reason: Literal["stop", "length"] = "stop"
) -> ProviderResponse:
    return ProviderResponse(
        content=text,
        attempt_count=1,
        latency_ms=1.0,
        response_metadata=ProviderResponseMetadata(
            finish_reason=finish_reason,
            content_state="text",
            content_bytes=len(text.encode("utf-8")),
        ),
    )


class TextProvider:
    def __init__(self, responses: list[ProviderResponse | Exception]) -> None:
        self.responses = responses
        self.calls: list[tuple[ChatMessage, ...]] = []

    def invoke(
        self, messages: tuple[ChatMessage, ...], *, output_format: str = "json_object"
    ) -> ProviderResponse:
        assert output_format == "text"
        self.calls.append(messages)
        item = self.responses[len(self.calls) - 1]
        if isinstance(item, Exception):
            raise item
        return item


def run_review(
    material: NullSpikeReviewMaterial,
    tmp_path: Path,
    provider: TextProvider,
    *,
    max_prompt_bytes: int = 65_536,
    workflow_id: str = "sr-unit",
):
    return staged_service.review_null_spike_staged(
        incident=material.detection.incident,
        evidence=[material.detection.evidence],
        draft=material.draft,
        project_revision="revision-under-test",
        settings=RuntimeAISettings(
            base_url="http://localhost:11434/v1",
            api_key="test-secret-key",
            model="test-model",
            max_retries=0,
        ),
        review_settings=ReviewAISettings(max_prompt_bytes=max_prompt_bytes),
        provider=provider,
        artifact_root=tmp_path,
        workflow_id_factory=lambda: workflow_id,
    )


@pytest.mark.component
def test_text_answers_are_collected_without_parsing_or_semantic_extraction(
    null_spike_review_material: NullSpikeReviewMaterial, tmp_path: Path
) -> None:
    provider = TextProvider([response(text) for text in TEXTS])
    original = null_spike_review_material.draft.model_dump(mode="json")
    result = run_review(null_spike_review_material, tmp_path, provider)

    assert result.status == "completed"
    assert result.output is not None and result.output_path is not None
    assert [stage.text for stage in result.output.stages] == list(TEXTS)
    assert [stage.stage_id for stage in result.output.stages] == [
        "evidence_review",
        "draft_critique",
        "synthesis",
    ]
    assert (
        result.output.incident_id
        == null_spike_review_material.detection.incident.incident_id
    )
    assert result.output.target_column == "income"
    assert result.output.deterministic_facts.current_null_rate == 0.21
    payload = json.loads(result.output_path.read_text(encoding="utf-8"))
    assert payload["stages"][0]["text"] == TEXTS[0]
    assert "findings" not in payload and "advisory_recommendation" not in payload
    assert null_spike_review_material.draft.model_dump(mode="json") == original
    assert len(provider.calls) == 3
    first_input = provider.calls[0][1].content
    for index, messages in enumerate(provider.calls):
        assert messages[1].content == first_input
        assert [
            message.content for message in messages if message.role == "assistant"
        ] == list(TEXTS[:index])
    assert result.workflow_path is not None
    manifest = json.loads(result.workflow_path.read_text(encoding="utf-8"))
    assert (
        manifest["output_digest"]
        == "sha256:"
        + hashlib.sha256(result.output_path.read_bytes().rstrip(b"\n")).hexdigest()
    )
    assert manifest["physical_attempts"] == 3
    assert "test-secret-key" not in result.workflow_path.read_text(encoding="utf-8")
    assert TEXTS[0] not in result.workflow_path.read_text(encoding="utf-8")
    for record, text in zip(result.stages, TEXTS, strict=True):
        assert record.response_path is not None and record.record_path is not None
        assert record.response_path.read_text(encoding="utf-8") == text
        assert record.record_path.is_file()
        assert (
            record.response_digest
            == "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()
        )


@pytest.mark.component
@pytest.mark.parametrize(
    ("second", "failure_code"),
    [
        (response(" \n\t"), "stage_response_empty"),
        (response("잘린 답변", "length"), "stage_response_incomplete"),
    ],
)
def test_invalid_second_answer_is_retained_and_stops_later_calls(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
    second: ProviderResponse,
    failure_code: str,
) -> None:
    provider = TextProvider([response(TEXTS[0]), second])
    result = run_review(null_spike_review_material, tmp_path, provider)
    assert result.status == "validation_failed" and result.failure_code == failure_code
    assert len(provider.calls) == 2
    assert result.output is None and result.output_path is None
    assert result.workflow_path is not None and result.workflow_path.is_file()
    assert result.stages[0].status == "completed"
    assert result.stages[1].response_path.read_text(encoding="utf-8") == second.content
    assert result.stages[0].response_path.read_text(encoding="utf-8") == TEXTS[0]


@pytest.mark.component
def test_provider_failure_records_attempts_and_preserves_prior_raw(
    null_spike_review_material: NullSpikeReviewMaterial, tmp_path: Path
) -> None:
    provider = TextProvider(
        [
            response(TEXTS[0]),
            ProviderUnavailableError(
                failure_code="provider_connection_error",
                attempt_count=1,
                latency_ms=2.0,
            ),
        ]
    )
    result = run_review(null_spike_review_material, tmp_path, provider)
    assert result.status == "unavailable" and len(provider.calls) == 2
    assert result.stages[1].response_path is None
    assert result.stages[1].attempt_count == 1
    assert result.stages[0].response_path.is_file()
    assert result.workflow_path.is_file()


@pytest.mark.component
def test_later_history_limit_is_checked_before_provider_call(
    null_spike_review_material: NullSpikeReviewMaterial, tmp_path: Path
) -> None:
    from hmda_reliability.review_ai.contracts import AgenticReviewInput, PromptIdentity
    from hmda_reliability.review_ai.prompt import build_canonical_input
    from hmda_reliability.review_ai.staged.prompt import render_stage_prompt

    material = null_spike_review_material
    review_input = AgenticReviewInput(
        incident=material.detection.incident,
        evidence=[material.detection.evidence],
        draft=material.draft,
        prompt_identity=PromptIdentity(),
        project_revision="revision-under-test",
    )
    first = render_stage_prompt(
        build_canonical_input(review_input),
        "evidence_review",
        (),
        max_prompt_bytes=65_536,
    )
    provider = TextProvider([response("가" * 1024)])
    result = run_review(
        material, tmp_path, provider, max_prompt_bytes=first.prompt_bytes + 16
    )
    assert len(provider.calls) == 1
    assert (
        result.status == "input_rejected" and result.failure_code == "prompt_too_large"
    )
    assert result.stages[-1].attempt_count == 0
    assert result.stages[0].response_path.read_text(encoding="utf-8") == "가" * 1024


@pytest.mark.component
def test_failed_raw_storage_stops_and_preserves_previous_stage(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = InvocationResponseStore.write

    def fail_second(self, invocation_id, content, *, max_response_bytes):
        if invocation_id.endswith("draft_critique"):
            raise InvocationEvidenceWriteError("storage failed")
        return original(
            self, invocation_id, content, max_response_bytes=max_response_bytes
        )

    monkeypatch.setattr(InvocationResponseStore, "write", fail_second)
    provider = TextProvider([response(TEXTS[0]), response(TEXTS[1])])
    result = run_review(null_spike_review_material, tmp_path, provider)
    assert result.status == "provenance_failed" and len(provider.calls) == 2
    assert result.stages[0].response_path.is_file()
    assert result.output_path is None


@pytest.mark.component
@pytest.mark.parametrize("operation", ["write_output", "write_manifest", "write_stage"])
def test_final_or_checkpoint_write_failure_does_not_return_completed(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
) -> None:
    def fail(*args, **kwargs):
        raise InvocationEvidenceWriteError("storage failed")

    monkeypatch.setattr(staged_service.StagedReviewStore, operation, fail)
    provider = TextProvider([response(text) for text in TEXTS])
    result = run_review(null_spike_review_material, tmp_path, provider)
    assert result.status == "provenance_failed"
    assert result.output is None
    assert result.stages[0].response_path.is_file()
    if operation == "write_manifest":
        assert result.output_path is not None and result.output_path.is_file()


@pytest.mark.component
def test_workflow_identity_collision_is_rejected_before_invocation(
    null_spike_review_material: NullSpikeReviewMaterial, tmp_path: Path
) -> None:
    first = run_review(
        null_spike_review_material,
        tmp_path,
        TextProvider([response(text) for text in TEXTS]),
    )
    assert first.status == "completed"
    second_provider = TextProvider([])
    second = run_review(null_spike_review_material, tmp_path, second_provider)
    assert second.status == "provenance_failed"
    assert second_provider.calls == []
    assert first.output_path.is_file()
