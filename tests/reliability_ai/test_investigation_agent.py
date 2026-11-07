"""Tests for the dynamic single-agent investigation loop."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from hmda_reliability.reliability.contracts import Evidence, EvidenceSource
from hmda_reliability.reliability_ai import (
    AgenticReviewInput,
    ReliabilityAISettings,
    investigate_incident,
)
from hmda_reliability.reliability_ai.investigation.tools import ToolRegistry
from hmda_reliability.reliability_ai.store import InvocationEvidenceWriteError
from hmda_reliability.runtime_ai.contracts import (
    ChatCompletionRequest,
    ProviderResponseMetadata,
    ToolCall,
    ToolCallFunction,
    TransportResponse,
)
from hmda_reliability.runtime_ai.provider import OpenAICompatibleAdapter
from hmda_reliability.runtime_ai.settings import RuntimeAISettings

from .conftest import NullSpikeReviewMaterial

pytestmark = pytest.mark.unit

_EMPTY_REPORT = '{"findings":[],"hypotheses":[],"uncertainties":[]}'


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
    native_prompt_client: MagicMock,
) -> None:
    material = null_spike_review_material
    evidence = material.detection.evidence.model_copy(
        update={
            "payload": {
                **material.detection.evidence.payload,
                "credentials": "private-evidence-value",
                "local_path": "/home/private/raw.csv",
            }
        }
    )
    review_input = AgenticReviewInput(
        incident=material.detection.incident,
        evidence=[evidence],
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
            ToolCall(
                id="impact-call",
                function=ToolCallFunction(
                    name="inspect_dbt_impact",
                    arguments=json.dumps(
                        {"asset_name": review_input.incident.asset_name}
                    ),
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
    dbt_manifest = tmp_path / "manifest.json"
    dbt_results = tmp_path / "run_results.json"
    dbt_manifest.write_text(
        json.dumps(
            {
                "sources": {
                    "source.test.hmda_loans": {"name": "hmda_loans", "schema": "raw"}
                },
                "nodes": {
                    "model.test.staging": {
                        "name": "staging",
                        "depends_on": {"nodes": ["source.test.hmda_loans"]},
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    dbt_results.write_text("{}", encoding="utf-8")

    result = investigate_incident(
        review_input,
        settings=_settings(),
        provider=adapter,
        dbt_artifact_paths=(dbt_manifest, dbt_results),
        artifact_root=tmp_path,
    )

    assert result.status == "completed"
    assert len(result.tool_calls) == 2
    assert result.tool_calls[0].tool_name == "get_incident_evidence"
    assert result.tool_calls[0].status == "success"
    assert result.tool_calls[1].tool_name == "inspect_dbt_impact"
    assert result.tool_calls[1].status == "success"
    assert result.tool_calls[1].result["downstream_assets"] == ["staging"]
    assert len(result.findings) == 1
    assert result.findings[0].topic == "null_rate_spike"
    assert len(result.hypotheses) == 1
    assert result.hypotheses[0].status == "supported"
    assert len(result.uncertainties) == 1
    assert result.facts == {
        "target_column": "income",
        **review_input.deterministic_facts.model_dump(mode="json"),
    }
    messages = json.dumps(
        [request.model_dump(mode="json") for request in transport.requests]
    )
    assert "private-evidence-value" not in messages
    assert "/home/private" not in messages
    assert str(tmp_path) not in messages
    initial_input = json.loads(transport.requests[0].messages[1].content)
    assert initial_input["deterministic_facts"]["current_null_rate"] == 0.21
    assert initial_input["evidence"][0]["evidence_id"] == ev_id
    native_prompt_client.get_prompt.assert_called_once()
    assert result.manifest_path is not None
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["prompt"]["version"] == 7
    assert manifest["prompt"]["name"] == "hmda-reliability-ai/investigation"
    assert manifest["dbt_artifact_paths"] == [str(dbt_manifest), str(dbt_results)]
    assert len(manifest["compiled_message_digests"]) == 2
    assert transport.requests[1].messages[-1].role == "tool"
    assert json.loads(transport.requests[1].messages[-1].content)[
        "downstream_assets"
    ] == ["staging"]


def test_unavailable_native_prompt_never_invokes_provider(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
    native_prompt_client: MagicMock,
) -> None:
    native_prompt_client.get_prompt.side_effect = RuntimeError("private remote failure")
    material = null_spike_review_material
    transport = ScriptedTransport([])
    result = investigate_incident(
        AgenticReviewInput(
            incident=material.detection.incident,
            evidence=[material.detection.evidence],
            draft=material.draft,
            project_revision="prompt-failure",
        ),
        settings=_settings(),
        provider=OpenAICompatibleAdapter(_settings(), transport=transport),
        artifact_root=tmp_path,
    )
    assert result.status == "error"
    assert result.failure_code == "prompt_unavailable"
    assert transport.requests == []


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


@pytest.mark.parametrize("failure_point", ["parse", "serialization", "manifest"])
def test_finalization_expiry_preserves_budget_failure_not_completion(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_point: str,
) -> None:
    from hmda_reliability.reliability_ai import store as store_module
    from hmda_reliability.reliability_ai.investigation import service

    clock_time = 0.0
    parse = service._parse_investigation_payload
    dump = service.InvestigationResult.model_dump
    fsync = store_module._fsync_directory

    def expire_after_parse(content: str) -> dict[str, object]:
        nonlocal clock_time
        parsed = parse(content)
        clock_time = 2.0
        return parsed

    def expire_after_dump(
        result: service.InvestigationResult, *, mode: str = "python"
    ) -> dict[str, object]:
        nonlocal clock_time
        payload = dump(result, mode=mode)
        if result.status == "completed":
            clock_time = 2.0
        return payload

    def expire_during_manifest(directory: Path) -> None:
        nonlocal clock_time
        fsync(directory)
        if directory.name == "investigations":
            clock_time = 2.0

    if failure_point == "parse":
        monkeypatch.setattr(service, "_parse_investigation_payload", expire_after_parse)
    elif failure_point == "serialization":
        monkeypatch.setattr(
            service.InvestigationResult, "model_dump", expire_after_dump
        )
    else:
        monkeypatch.setattr(store_module, "_fsync_directory", expire_during_manifest)
    material = null_spike_review_material
    result = investigate_incident(
        AgenticReviewInput(
            incident=material.detection.incident,
            evidence=[material.detection.evidence],
            draft=material.draft,
            project_revision="finalization-budget-regression",
        ),
        settings=_settings(),
        ai_settings=ReliabilityAISettings(workflow_budget_seconds=1.0),
        provider=OpenAICompatibleAdapter(
            _settings(),
            transport=ScriptedTransport([TransportResponse(content=_EMPTY_REPORT)]),
        ),
        artifact_root=tmp_path,
        clock=lambda: clock_time,
    )
    assert result.status == "budget_exhausted"
    assert result.failure_code == "workflow_budget_exhausted"
    assert result.manifest_path is not None
    assert (
        json.loads(result.manifest_path.read_text())["result"]["status"]
        == "budget_exhausted"
    )
    assert result.response_paths[0].read_text() == _EMPTY_REPORT


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
            TransportResponse(content=_EMPTY_REPORT),
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
        "{}",
        '{"error":"unable to investigate"}',
        '{"findings":[],"hypotheses":[]}',
        '{"findings":{},"hypotheses":[],"uncertainties":[]}',
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
            TransportResponse(content=_EMPTY_REPORT),
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
        _EMPTY_REPORT,
    ]


@pytest.mark.parametrize("finish_reason", ["length", "content_filter"])
def test_known_incomplete_response_retains_raw_without_completion(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
    finish_reason: str,
) -> None:
    material = null_spike_review_material
    transport = ScriptedTransport(
        [
            TransportResponse(
                content="{}",
                response_metadata=ProviderResponseMetadata.model_validate(
                    {
                        "finish_reason": finish_reason,
                        "content_state": "text",
                        "content_bytes": 2,
                    }
                ),
            )
        ]
    )
    result = investigate_incident(
        AgenticReviewInput(
            incident=material.detection.incident,
            evidence=[material.detection.evidence],
            draft=material.draft,
            project_revision="incomplete-provider-regression",
        ),
        settings=_settings(),
        provider=OpenAICompatibleAdapter(_settings(), transport=transport),
        artifact_root=tmp_path,
    )

    assert result.status == "error"
    assert result.failure_code == "incomplete_provider_response"
    assert result.response_paths[0].read_text(encoding="utf-8") == "{}"
    assert len(transport.requests) == 1


def test_malformed_tool_arguments_with_observation_remain_tool_errors(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
) -> None:
    material = null_spike_review_material
    transport = ScriptedTransport(
        [
            TransportResponse(
                content="",
                tool_calls=(
                    ToolCall(
                        id="malformed",
                        function=ToolCallFunction(
                            name="compare_profiles", arguments="{broken"
                        ),
                    ),
                ),
            ),
            TransportResponse(content=_EMPTY_REPORT),
        ]
    )
    result = investigate_incident(
        AgenticReviewInput(
            incident=material.detection.incident,
            evidence=[material.detection.evidence],
            draft=material.draft,
            project_revision="malformed-observation-regression",
        ),
        settings=_settings(),
        provider=OpenAICompatibleAdapter(_settings(), transport=transport),
        artifact_root=tmp_path,
        observe_io=True,
    )

    assert result.status == "completed"
    assert result.tool_calls[0].status == "error"
    assert result.tool_calls[0].result == {"error": "invalid_arguments"}
    assert transport.requests[1].messages[-1].tool_call_id == "malformed"
    assert "invalid_arguments" in transport.requests[1].messages[-1].content


def test_oversized_context_is_retained_as_error_before_prompt_or_provider(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
    native_prompt_client: MagicMock,
) -> None:
    material = null_spike_review_material
    evidence = [
        material.detection.evidence,
        *[
            Evidence(
                evidence_id=f"metadata-{index}",
                source=EvidenceSource.TABLE_METADATA,
                asset_name=material.detection.incident.asset_name,
                partition=material.detection.incident.partition,
                observed_at=material.detection.evidence.observed_at,
                summary="관" * 1024,
                payload={
                    "columns": [f"field-{column}-" + "x" * 90 for column in range(30)]
                },
            )
            for index in range(7)
        ],
    ]
    refs = [item.evidence_id for item in evidence]
    transport = ScriptedTransport([])
    result = investigate_incident(
        AgenticReviewInput(
            incident=material.detection.incident.model_copy(
                update={"evidence_refs": refs}
            ),
            evidence=evidence,
            draft=material.draft.model_copy(update={"evidence_refs": refs}),
            project_revision="oversized-context-regression",
        ),
        settings=_settings(),
        provider=OpenAICompatibleAdapter(_settings(), transport=transport),
        artifact_root=tmp_path,
    )

    assert result.status == "error"
    assert result.failure_code == "context_too_large"
    assert result.manifest_path is not None
    assert result.response_paths == ()
    assert transport.requests == []
    native_prompt_client.get_prompt.assert_not_called()


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
    assert result.status == "error"
    assert result.failure_code == "prompt_too_large"
    assert transport.requests == []


def test_oversized_evidence_facts_return_context_failure_manifest(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
    native_prompt_client: MagicMock,
) -> None:
    material = null_spike_review_material
    payload: dict[str, object] = {
        key: [f"asset-{index:02d}-" + "x" * 21 for index in range(31)]
        for key in ("related_assets", "upstream_assets", "downstream_assets")
    }
    payload["lineage"] = [{"from": "u" * 24, "to": "d" * 24} for _ in range(15)]
    assert all(
        len(json.dumps(value, separators=(",", ":")).encode()) <= 1024
        for value in payload.values()
    )
    assert len(json.dumps(payload, separators=(",", ":")).encode()) > 4096
    evidence = [
        material.detection.evidence,
        Evidence(
            evidence_id="large-catalog",
            source=EvidenceSource.CATALOG,
            asset_name=material.detection.incident.asset_name,
            partition=material.detection.incident.partition,
            observed_at=material.detection.evidence.observed_at,
            summary="Catalog metadata",
            payload=payload,
        ),
    ]
    refs = [item.evidence_id for item in evidence]
    transport = ScriptedTransport([])
    result = investigate_incident(
        AgenticReviewInput(
            incident=material.detection.incident.model_copy(
                update={"evidence_refs": refs}
            ),
            evidence=evidence,
            draft=material.draft.model_copy(update={"evidence_refs": refs}),
            project_revision="oversized-evidence-regression",
        ),
        settings=_settings(),
        provider=OpenAICompatibleAdapter(_settings(), transport=transport),
        artifact_root=tmp_path,
    )
    assert result.status == "error"
    assert result.failure_code == "context_too_large"
    assert result.manifest_path is not None
    assert result.response_paths == ()
    assert transport.requests == []
    native_prompt_client.get_prompt.assert_not_called()


def test_unprojectable_context_identity_returns_failure_manifest(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
    native_prompt_client: MagicMock,
) -> None:
    material = null_spike_review_material
    contextual = material.detection.evidence.model_copy(
        update={"evidence_id": "long-identity", "asset_name": "x" * 257}
    )
    refs = [material.detection.evidence.evidence_id, contextual.evidence_id]
    transport = ScriptedTransport([])
    result = investigate_incident(
        AgenticReviewInput(
            incident=material.detection.incident.model_copy(
                update={"evidence_refs": refs}
            ),
            evidence=[material.detection.evidence, contextual],
            draft=material.draft.model_copy(update={"evidence_refs": refs}),
            project_revision="context-identity-regression",
        ),
        settings=_settings(),
        provider=OpenAICompatibleAdapter(_settings(), transport=transport),
        artifact_root=tmp_path,
    )
    assert result.status == "error"
    assert result.failure_code == "invalid_review_context"
    assert result.manifest_path is not None
    assert result.response_paths == ()
    assert transport.requests == []
    native_prompt_client.get_prompt.assert_not_called()


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
        content = json.dumps({**json.loads(_EMPTY_REPORT), "facts": {"number": number}})
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
        assert manifest["result"]["facts"]["current_null_rate"] == 0.21
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
            _settings(),
            transport=ScriptedTransport([TransportResponse(content=_EMPTY_REPORT)]),
        ),
        artifact_root=tmp_path,
    )
    assert result.status == "error"
    assert result.failure_code == f"{failed_store}_persistence_failed"
    if failed_store == "response":
        assert result.response_paths == ()
        assert result.manifest_path is not None
    else:
        assert result.response_paths[0].read_text(encoding="utf-8") == _EMPTY_REPORT
        assert result.manifest_path is None
    assert result.turns[0].content == _EMPTY_REPORT


@pytest.mark.parametrize("failure_point", [None, "start", "update", "end"])
def test_observations_surround_real_calls_and_follow_local_raw_retention(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
    native_prompt_client: MagicMock,
    failure_point: str | None,
) -> None:
    material = null_spike_review_material
    calls: list[tuple[str, dict[str, object]]] = []

    def start(**kwargs: object) -> MagicMock:
        if failure_point == "start":
            raise RuntimeError("observation unavailable")
        observation = MagicMock()
        observation.trace_id = "a" * 32
        observation.id = "b" * 16
        observation.start_observation.side_effect = start
        calls.append(("start", dict(kwargs)))

        def update(**values: object) -> None:
            if "output" in values:
                assert tuple((tmp_path / "reliability-ai" / "responses").glob("*.txt"))
            if failure_point == "update":
                raise RuntimeError("observation update failed")
            calls.append(("update", dict(values)))

        observation.update.side_effect = update
        if failure_point == "end":
            observation.end.side_effect = RuntimeError("observation end failed")
        return observation

    native_prompt_client.start_observation.side_effect = start
    content = json.dumps({**json.loads(_EMPTY_REPORT), "facts": {"delta": 0.9}})
    transport = ScriptedTransport([TransportResponse(content=content)])
    result = investigate_incident(
        AgenticReviewInput(
            incident=material.detection.incident,
            evidence=[material.detection.evidence],
            draft=material.draft,
            project_revision="observation-regression",
        ),
        settings=_settings(),
        provider=OpenAICompatibleAdapter(_settings(), transport=transport),
        artifact_root=tmp_path,
        observe_io=True,
    )
    assert result.status == "completed"
    assert result.facts["delta"] == pytest.approx(0.2)
    assert len(transport.requests) == 1
    assert result.response_paths[0].read_text(encoding="utf-8") == content
    assert result.manifest_path is not None
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert (
        manifest["canonical_input"]["deterministic_facts"]["current_null_rate"] == 0.21
    )
    assert manifest["result"]["turns"][0]["attempt_count"] == 1
    if failure_point is None:
        assert [values["as_type"] for event, values in calls if event == "start"] == [
            "agent",
            "generation",
        ]
    else:
        observation_record = json.loads(
            Path(manifest["observation_record_path"]).read_text(encoding="utf-8")
        )
        assert observation_record["errors"]


@pytest.mark.component
def test_native_sdk_records_sibling_generations_and_tool_history(
    null_spike_review_material: NullSpikeReviewMaterial,
    tmp_path: Path,
    native_prompt_client: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from langfuse import Langfuse
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
        InMemorySpanExporter,
    )

    from hmda_reliability.reliability_ai.investigation import service

    exporter = InMemorySpanExporter()
    tracer_provider = TracerProvider()
    client = Langfuse(
        public_key="pk-lf-offline-investigation",
        secret_key="offline",
        base_url="http://localhost:1",
        tracer_provider=tracer_provider,
        span_exporter=exporter,
    )
    monkeypatch.setattr(client, "get_prompt", native_prompt_client.get_prompt)
    monkeypatch.setattr(service, "get_client", lambda: client)
    material = null_spike_review_material
    transport = ScriptedTransport(
        [
            TransportResponse(
                content="Inspect /home/private/raw.csv",
                tool_calls=(
                    ToolCall(
                        id="profile",
                        function=ToolCallFunction(
                            name="compare_profiles", arguments="{}"
                        ),
                    ),
                ),
            ),
            TransportResponse(content=_EMPTY_REPORT),
        ]
    )
    try:
        result = investigate_incident(
            AgenticReviewInput(
                incident=material.detection.incident,
                evidence=[material.detection.evidence],
                draft=material.draft,
                project_revision="native-sdk-offline",
            ),
            settings=_settings(),
            artifact_root=tmp_path,
            observe_io=True,
            provider=OpenAICompatibleAdapter(_settings(), transport=transport),
        )
        client.flush()
        spans = exporter.get_finished_spans()
        assert result.status == "completed"
        root = next(span for span in spans if span.name == "investigate-incident")
        children = [span for span in spans if span.name != root.name]
        assert sorted(span.name for span in children) == [
            "compare_profiles",
            "investigate-model",
            "investigate-model",
        ]
        assert all(
            span.parent is not None and span.parent.span_id == root.context.span_id
            for span in children
        )
        generations = [span for span in children if span.name == "investigate-model"]
        inputs: list[str] = []
        for span in generations:
            assert span.attributes is not None
            assert span.attributes["langfuse.observation.prompt.version"] == 7
            observed_input = span.attributes["langfuse.observation.input"]
            assert isinstance(observed_input, str)
            inputs.append(observed_input)
        assert any('"role": "tool"' in value for value in inputs)
        assert all("/home/private" not in value for value in inputs)
        assert (
            result.response_paths[0].read_text(encoding="utf-8")
            == "Inspect /home/private/raw.csv"
        )
    finally:
        client.shutdown()
