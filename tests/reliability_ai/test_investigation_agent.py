"""Tests for the dynamic single-agent investigation loop."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hmda_reliability.reliability_ai import (
    AgenticReviewInput,
    ReliabilityAISettings,
    investigate_incident,
)
from hmda_reliability.runtime_ai.contracts import (
    ChatCompletionRequest,
    ToolCall,
    ToolCallFunction,
    TransportResponse,
)
from hmda_reliability.runtime_ai.provider import OpenAICompatibleAdapter
from hmda_reliability.runtime_ai.settings import RuntimeAISettings

from .conftest import NullSpikeReviewMaterial

pytestmark = pytest.mark.unit


def _settings() -> RuntimeAISettings:
    return RuntimeAISettings(
        base_url="http://localhost:11434/v1",
        api_key="test",
        model="test-model",
        max_retries=0,
    )


class ScriptedTransport:
    def __init__(self, responses: list[TransportResponse]) -> None:
        self.responses = list(responses)
        self.requests: list[ChatCompletionRequest] = []

    def create(self, request: ChatCompletionRequest) -> TransportResponse:
        self.requests.append(request)
        if not self.responses:
            raise RuntimeError("no more scripted responses")
        return self.responses.pop(0)


def test_investigate_incident_dynamic_tool_calling_loop(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
) -> None:
    material = null_spike_review_material
    review_input = AgenticReviewInput(
        incident=material.detection.incident,
        evidence=[material.detection.evidence],
        draft=material.draft,
        project_revision="rev-1",
    )

    ev_id = material.detection.evidence.evidence_id

    # 1차 응답: 도구 호출 요청
    r1 = TransportResponse(
        content="",
        tool_calls=(
            ToolCall(
                id="call_1",
                function=ToolCallFunction(
                    name="get_incident_evidence",
                    arguments=json.dumps({"evidence_id": ev_id}),
                ),
            ),
        ),
    )
    # 2차 응답: 조사 완료 JSON 보고서
    final_report = {
        "facts": {"column": "income", "delta": 0.2},
        "findings": [
            {
                "topic": "null_rate_spike",
                "description": "income 컬럼의 결측치가 20%p 급증함",
                "evidence_refs": [ev_id],
            }
        ],
        "hypotheses": [
            {
                "hypothesis": "원천 수집 단계 결측치 유입",
                "status": "supported",
                "rationale": "프로파일 증거와 일치",
            }
        ],
        "uncertainties": [
            {
                "topic": "upstream_pipeline",
                "description": "상위 파이프라인 에러 여부 미확인",
                "needed_evidence": "오케스트레이션 로그",
            }
        ],
    }
    r2 = TransportResponse(content=json.dumps(final_report, ensure_ascii=False))

    transport = ScriptedTransport([r1, r2])
    adapter = OpenAICompatibleAdapter(_settings(), transport=transport)

    result = investigate_incident(
        review_input,
        settings=_settings(),
        provider=adapter,
        artifact_root=tmp_path,
    )

    assert result.status == "completed"
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].tool_name == "get_incident_evidence"
    assert result.tool_calls[0].status == "success"
    assert len(result.findings) == 1
    assert result.findings[0].topic == "null_rate_spike"
    assert len(result.hypotheses) == 1
    assert result.hypotheses[0].status == "supported"
    assert len(result.uncertainties) == 1


def test_investigate_incident_detects_duplicate_tool_call_cycle(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
) -> None:
    material = null_spike_review_material
    review_input = AgenticReviewInput(
        incident=material.detection.incident,
        evidence=[material.detection.evidence],
        draft=material.draft,
        project_revision="rev-1",
    )

    ev_id = material.detection.evidence.evidence_id
    duplicate_call = ToolCall(
        id="call_dup",
        function=ToolCallFunction(
            name="get_incident_evidence",
            arguments=json.dumps({"evidence_id": ev_id}),
        ),
    )

    # 동일 도구 + 동일 인자 호출을 연속 2회 반환
    r1 = TransportResponse(content="", tool_calls=(duplicate_call,))
    r2 = TransportResponse(content="", tool_calls=(duplicate_call,))

    transport = ScriptedTransport([r1, r2])
    adapter = OpenAICompatibleAdapter(_settings(), transport=transport)

    result = investigate_incident(
        review_input,
        settings=_settings(),
        provider=adapter,
        artifact_root=tmp_path,
    )

    assert result.status == "tool_cycle_detected"
    assert result.failure_code == "duplicate_tool_call_cycle"


def test_investigate_incident_handles_budget_exhaustion(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
) -> None:
    material = null_spike_review_material
    review_input = AgenticReviewInput(
        incident=material.detection.incident,
        evidence=[material.detection.evidence],
        draft=material.draft,
        project_revision="rev-1",
    )

    transport = ScriptedTransport([])
    adapter = OpenAICompatibleAdapter(_settings(), transport=transport)

    ai_settings = ReliabilityAISettings(workflow_budget_seconds=10.0)

    clock_time = 0.0

    def fake_clock() -> float:
        nonlocal clock_time
        current = clock_time
        clock_time += 100.0  # 다음 호출 시 예산 초과
        return current

    result = investigate_incident(
        review_input,
        settings=_settings(),
        ai_settings=ai_settings,
        provider=adapter,
        artifact_root=tmp_path,
        clock=fake_clock,
    )

    assert result.status == "budget_exhausted"
    assert result.failure_code == "workflow_budget_exhausted"
