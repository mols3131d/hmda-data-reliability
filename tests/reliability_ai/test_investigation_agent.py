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
from hmda_reliability.reliability_ai.investigation.tools import ToolRegistry
from hmda_reliability.reliability_ai.store import InvocationEvidenceWriteError
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


def test_budget_expiring_during_preflight_never_starts_provider(
    null_spike_review_material: NullSpikeReviewMaterial, tmp_path: Path
) -> None:
    material = null_spike_review_material
    transport = ScriptedTransport([])
    clock_values = iter((0.0, 0.0, 2.0))

    result = investigate_incident(
        AgenticReviewInput(
            incident=material.detection.incident,
            evidence=[material.detection.evidence],
            draft=material.draft,
            project_revision="preflight-budget-regression",
        ),
        settings=_settings(),
        ai_settings=ReliabilityAISettings(workflow_budget_seconds=1.0),
        provider=OpenAICompatibleAdapter(_settings(), transport=transport),
        artifact_root=tmp_path,
        clock=lambda: next(clock_values),
    )

    assert result.status == "budget_exhausted"
    assert result.failure_code == "workflow_budget_exhausted"
    assert transport.requests == []


def test_batched_tool_calls_cannot_exceed_limit(
    null_spike_review_material: NullSpikeReviewMaterial, tmp_path: Path
) -> None:
    material = null_spike_review_material
    review_input = AgenticReviewInput(
        incident=material.detection.incident,
        evidence=[material.detection.evidence],
        draft=material.draft,
        project_revision="limit-regression",
    )
    calls = tuple(
        ToolCall(
            id=f"call-{index}",
            function=ToolCallFunction(
                name="get_incident_evidence",
                arguments=json.dumps({"evidence_id": evidence_id}),
            ),
        )
        for index, evidence_id in enumerate(
            [material.detection.evidence.evidence_id, "missing"]
        )
    )
    transport = ScriptedTransport([TransportResponse(content="", tool_calls=calls)])
    result = investigate_incident(
        review_input,
        settings=_settings(),
        ai_settings=ReliabilityAISettings(max_tool_calls=1),
        provider=OpenAICompatibleAdapter(_settings(), transport=transport),
        artifact_root=tmp_path,
    )
    assert result.status == "budget_exhausted"
    assert result.failure_code == "tool_call_budget_exhausted"
    assert len(result.tool_calls) == 1
    assert len(transport.requests) == 1


def test_budget_expiring_during_argument_preflight_never_starts_tool(
    null_spike_review_material: NullSpikeReviewMaterial, tmp_path: Path
) -> None:
    material = null_spike_review_material
    called: list[dict[str, object]] = []
    registry = ToolRegistry(
        profile_comparison_handler=lambda arguments: (
            called.append(arguments) or {"comparison": "observed"}
        )
    )
    call = ToolCall(
        id="expired-dispatch",
        function=ToolCallFunction(
            name="compare_profiles", arguments='{"column":"income"}'
        ),
    )
    transport = ScriptedTransport([TransportResponse(content="", tool_calls=(call,))])
    clock_values = iter((0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.0))

    result = investigate_incident(
        AgenticReviewInput(
            incident=material.detection.incident,
            evidence=[material.detection.evidence],
            draft=material.draft,
            project_revision="dispatch-budget-regression",
        ),
        settings=_settings(),
        ai_settings=ReliabilityAISettings(workflow_budget_seconds=1.0),
        provider=OpenAICompatibleAdapter(_settings(), transport=transport),
        tool_registry=registry,
        artifact_root=tmp_path,
        clock=lambda: next(clock_values),
    )

    assert result.status == "budget_exhausted"
    assert result.failure_code == "workflow_budget_exhausted"
    assert result.tool_calls == ()
    assert called == []


@pytest.mark.parametrize("output_kind", ["arguments", "report"])
def test_deeply_nested_json_returns_error_with_preserved_response(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
    output_kind: str,
) -> None:
    material = null_spike_review_material
    depth = 16000
    nested_json = "[" * depth + "0" + "]" * depth
    assert len(nested_json.encode("utf-8")) < _settings().max_output_bytes
    response = (
        TransportResponse(
            content="",
            tool_calls=(
                ToolCall(
                    id="nested-arguments",
                    function=ToolCallFunction(
                        name="get_incident_evidence", arguments=nested_json
                    ),
                ),
            ),
        )
        if output_kind == "arguments"
        else TransportResponse(content=nested_json)
    )

    result = investigate_incident(
        AgenticReviewInput(
            incident=material.detection.incident,
            evidence=[material.detection.evidence],
            draft=material.draft,
            project_revision="nested-json-regression",
        ),
        settings=_settings(),
        provider=OpenAICompatibleAdapter(
            _settings(), transport=ScriptedTransport([response])
        ),
        artifact_root=tmp_path,
    )

    assert result.status == "error"
    assert result.failure_code == "invalid_investigation_output"
    assert result.manifest_path is not None
    assert result.response_paths[0].read_text(encoding="utf-8") == response.content


def test_final_synthesis_has_no_tools_after_limit(
    null_spike_review_material: NullSpikeReviewMaterial, tmp_path: Path
) -> None:
    material = null_spike_review_material
    call = ToolCall(
        id="only-call",
        function=ToolCallFunction(
            name="get_incident_evidence",
            arguments=json.dumps(
                {"evidence_id": material.detection.evidence.evidence_id}
            ),
        ),
    )
    transport = ScriptedTransport(
        [
            TransportResponse(content="", tool_calls=(call,)),
            TransportResponse(content="{}"),
        ]
    )
    result = investigate_incident(
        AgenticReviewInput(
            incident=material.detection.incident,
            evidence=[material.detection.evidence],
            draft=material.draft,
            project_revision="limit-regression",
        ),
        settings=_settings(),
        ai_settings=ReliabilityAISettings(max_tool_calls=1),
        provider=OpenAICompatibleAdapter(_settings(), transport=transport),
        artifact_root=tmp_path,
    )
    assert result.status == "completed"
    assert transport.requests[1].tools is None
    assert transport.requests[1].tool_choice == "none"


@pytest.mark.parametrize(
    "content",
    [
        '{"facts":',
        "not a JSON report",
        "[]",
        '{"facts":{"nested":' + "[" * 300 + "0" + "]" * 300 + "}}",
    ],
)
def test_invalid_report_returns_json_safe_error_and_evidence(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
    content: str,
) -> None:
    material = null_spike_review_material
    result = investigate_incident(
        AgenticReviewInput(
            incident=material.detection.incident,
            evidence=[material.detection.evidence],
            draft=material.draft,
            project_revision="invalid-report-regression",
        ),
        settings=_settings(),
        provider=OpenAICompatibleAdapter(
            _settings(),
            transport=ScriptedTransport([TransportResponse(content=content)]),
        ),
        artifact_root=tmp_path,
    )
    assert result.status == "error"
    assert result.failure_code == "invalid_investigation_output"
    assert result.facts == {}
    assert result.model_dump(mode="json")["status"] == "error"
    assert result.manifest_path is not None
    assert result.response_paths[0].read_text(encoding="utf-8") == content


@pytest.mark.parametrize("unsafe_field", ["arguments", "result"])
def test_unserializable_tool_record_preserves_safe_error_and_raw_turns(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
    unsafe_field: str,
) -> None:
    material = null_spike_review_material
    nested_json = "[" * 300 + "0" + "]" * 300
    arguments = (
        '{"evidence_id":"example","extra":' + nested_json + "}"
        if unsafe_field == "arguments"
        else "{}"
    )
    call = ToolCall(
        id="unsafe-record",
        function=ToolCallFunction(
            name=(
                "get_incident_evidence"
                if unsafe_field == "arguments"
                else "compare_profiles"
            ),
            arguments=arguments,
        ),
    )
    transport = ScriptedTransport(
        [
            TransportResponse(content="", tool_calls=(call,)),
            TransportResponse(content="{}"),
        ]
    )
    result = investigate_incident(
        AgenticReviewInput(
            incident=material.detection.incident,
            evidence=[material.detection.evidence],
            draft=material.draft,
            project_revision="unsafe-tool-record-regression",
        ),
        settings=_settings(),
        provider=OpenAICompatibleAdapter(_settings(), transport=transport),
        tool_registry=ToolRegistry(
            profile_comparison_handler=lambda _: {"nested": json.loads(nested_json)}
        ),
        artifact_root=tmp_path,
    )

    assert result.status == "error"
    assert result.failure_code == "invalid_investigation_output"
    exported = result.model_dump(mode="json")
    assert exported["tool_calls"][0]["call_id"] == "unsafe-record"
    assert exported["tool_calls"][0]["result"]["error"] == "unserializable_tool_record"
    assert result.turns[0].tool_calls[0]["function"]["arguments"] == arguments
    assert result.turns[1].tool_call_id == "unsafe-record"
    assert result.manifest_path is not None
    assert (
        json.loads(result.manifest_path.read_text(encoding="utf-8"))["result"]
        == exported
    )
    assert [path.read_text(encoding="utf-8") for path in result.response_paths] == [
        "",
        "{}",
    ]


def test_oversized_prompt_is_rejected_before_provider_call(
    null_spike_review_material: NullSpikeReviewMaterial, tmp_path: Path
) -> None:
    material = null_spike_review_material
    transport = ScriptedTransport([])
    result = investigate_incident(
        AgenticReviewInput(
            incident=material.detection.incident,
            evidence=[material.detection.evidence],
            draft=material.draft,
            project_revision="limit-regression",
        ),
        settings=_settings(),
        ai_settings=ReliabilityAISettings(max_prompt_bytes=1),
        provider=OpenAICompatibleAdapter(_settings(), transport=transport),
        artifact_root=tmp_path,
    )
    assert result.failure_code == "prompt_budget_exhausted"
    assert transport.requests == []


def test_same_clock_investigations_preserve_distinct_responses(
    null_spike_review_material: NullSpikeReviewMaterial, tmp_path: Path
) -> None:
    material = null_spike_review_material
    review_input = AgenticReviewInput(
        incident=material.detection.incident,
        evidence=[material.detection.evidence],
        draft=material.draft,
        project_revision="persistence-regression",
    )
    results = []
    for number in (1, 2):
        content = json.dumps({"facts": {"number": number}})
        result = investigate_incident(
            review_input,
            settings=_settings(),
            provider=OpenAICompatibleAdapter(
                _settings(),
                transport=ScriptedTransport([TransportResponse(content=content)]),
            ),
            artifact_root=tmp_path,
            clock=lambda: 10.0,
        )
        assert result.status == "completed"
        assert result.response_paths[0].read_text(encoding="utf-8") == content
        assert result.manifest_path is not None
        manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
        assert manifest["result"]["facts"] == {"number": number}
        assert manifest["project_revision"] == "persistence-regression"
        results.append(result)
    assert results[0].invocation_id != results[1].invocation_id
    assert results[0].response_paths != results[1].response_paths


@pytest.mark.parametrize("failed_store", ["response", "manifest"])
def test_evidence_write_failure_cannot_be_completed(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failed_store: str,
) -> None:
    from hmda_reliability.reliability_ai.investigation import service

    def fail_write(*args: object, **kwargs: object) -> Path:
        raise InvocationEvidenceWriteError("synthetic storage failure")

    if failed_store == "response":
        monkeypatch.setattr(service.InvocationResponseStore, "write", fail_write)
    else:
        monkeypatch.setattr(service, "write_review_json", fail_write)
    material = null_spike_review_material
    result = investigate_incident(
        AgenticReviewInput(
            incident=material.detection.incident,
            evidence=[material.detection.evidence],
            draft=material.draft,
            project_revision="persistence-regression",
        ),
        settings=_settings(),
        provider=OpenAICompatibleAdapter(
            _settings(), transport=ScriptedTransport([TransportResponse(content="{}")])
        ),
        artifact_root=tmp_path,
    )
    assert result.status == "error"
    assert result.failure_code == f"{failed_store}_persistence_failed"
    if failed_store == "response":
        assert result.response_paths == ()
        assert result.manifest_path is not None
    else:
        assert result.response_paths[0].read_text(encoding="utf-8") == "{}"
        assert result.manifest_path is None
    assert result.turns[0].content == "{}"
