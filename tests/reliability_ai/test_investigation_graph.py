"""공통 조사 그래프가 같은 모델 턴의 제안을 순서대로, 허용 횟수만큼 꺼낸다."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from langfuse.api.prompts.types.prompt import Prompt_Chat
from langfuse.model import ChatPromptClient

from hmda_reliability.reliability_ai import (
    AgenticReviewInput,
    ReliabilityAISettings,
    investigate_incident,
)
from hmda_reliability.reliability_ai.investigation.graph import (
    GraphStop,
    run_investigation_graph,
)
from hmda_reliability.runtime_ai.contracts import (
    ChatCompletionRequest,
    ChatMessage,
    ProviderResponse,
    ToolCall,
    ToolCallFunction,
    TransportResponse,
)
from hmda_reliability.runtime_ai.provider import OpenAICompatibleAdapter
from hmda_reliability.runtime_ai.settings import RuntimeAISettings

from .conftest import NullSpikeReviewMaterial


@pytest.mark.unit
@pytest.mark.parametrize(("quota", "expected"), [(1, "budget_exhausted"), (2, "done")])
def test_ordered_batch_and_terminal_model_turn(quota: int, expected: str) -> None:
    events: list[str] = []
    calls = tuple(
        ToolCall(id=key, function=ToolCallFunction(name="lookup")) for key in ("a", "b")
    )

    def model(turn: int) -> ProviderResponse:
        events.append(f"model {turn}")
        return ProviderResponse(
            content="",
            tool_calls=calls if turn == 0 else (),
            attempt_count=1,
            latency_ms=0,
        )

    def retain(turn: int, response: ProviderResponse) -> GraphStop | None:
        events.append(f"saved {turn}")
        return None if response.tool_calls else GraphStop("done")

    def read(turn: int, call: ToolCall) -> None:
        events.append(f"read {turn} {call.id}")

    result = run_investigation_graph(
        assess=lambda _: None,
        model=model,
        retain=retain,
        read=read,
        finish=lambda stop: stop.status,
        max_turns=2,
        max_tool_calls=quota,
    )
    assert result == expected
    assert events == ["model 0", "saved 0", "read 0 a"] + (
        ["read 0 b", "model 1", "saved 1"] if quota == 2 else []
    )


@pytest.mark.integration
def test_tool_definitions_consume_prompt_budget_before_transport(
    null_spike_review_material: NullSpikeReviewMaterial,
    native_prompt_client: MagicMock,
    tmp_path: Path,
) -> None:
    native_prompt_client.get_prompt.return_value = ChatPromptClient(
        Prompt_Chat.model_validate(
            {
                "name": "bounded",
                "version": 1,
                "prompt": [{"role": "user", "content": "x"}],
                "config": {},
                "labels": [],
                "tags": [],
            }
        )
    )
    settings = RuntimeAISettings.model_validate(
        {
            "model": "fixture",
            "base_url": "http://localhost:11434/v1",
            "api_key": "local",
        }
    )

    class NoTransport:
        def create(self, request: ChatCompletionRequest) -> TransportResponse:
            pytest.fail("wire input over budget must not reach transport")

    material = null_spike_review_material
    result = investigate_incident(
        AgenticReviewInput(
            incident=material.detection.incident,
            evidence=(material.detection.evidence,),
            draft=material.draft,
            project_revision="definitions-byte-limit",
        ),
        settings=settings,
        provider=OpenAICompatibleAdapter(settings, transport=NoTransport()),
        ai_settings=ReliabilityAISettings(max_prompt_bytes=128),
        artifact_root=tmp_path,
    )
    assert len(ChatMessage(role="user", content="x").model_dump_json().encode()) < 128
    assert result.failure_code == "prompt_too_large"
    assert result.manifest_path is not None
    assert json.loads(result.manifest_path.read_bytes())["input_bytes"][0] > 128


@pytest.mark.integration
@pytest.mark.parametrize("boundary", ["generation", "tool"])
def test_observation_start_cannot_spend_remaining_dispatch_budget(
    boundary: str,
    null_spike_review_material: NullSpikeReviewMaterial,
    native_prompt_client: MagicMock,
    tmp_path: Path,
) -> None:
    from hmda_reliability.reliability_ai.investigation.tools import ToolRegistry

    now = 0.0

    def observe(**kwargs: object) -> MagicMock:
        nonlocal now
        if kwargs["as_type"] == boundary:
            now = 2.0
        return MagicMock()

    trace = native_prompt_client.start_observation.return_value
    trace.start_observation.side_effect = observe
    provider = MagicMock()
    provider.invoke.return_value = ProviderResponse(
        content="",
        tool_calls=(
            ToolCall(
                id="one",
                function=ToolCallFunction(name="compare_profiles", arguments="{}"),
            ),
        ),
        latency_ms=0,
        attempt_count=1,
    )
    material = null_spike_review_material
    handler = MagicMock(return_value={"ok": True})
    result = investigate_incident(
        AgenticReviewInput(
            incident=material.detection.incident,
            evidence=(material.detection.evidence,),
            draft=material.draft,
            project_revision="post-observation-deadline",
        ),
        provider=provider,
        tool_registry=ToolRegistry(profile_comparison_handler=handler),
        ai_settings=ReliabilityAISettings(workflow_budget_seconds=1),
        clock=lambda: now,
        artifact_root=tmp_path,
    )
    assert result.failure_code == "workflow_budget_exhausted"
    assert provider.invoke.call_count == (boundary == "tool")
    handler.assert_not_called()


@pytest.mark.integration
@pytest.mark.parametrize("changed", ["call_id", "tool_name"])
def test_foreign_observation_never_enters_model_history(
    changed: str, null_spike_review_material: NullSpikeReviewMaterial, tmp_path: Path
) -> None:
    from hmda_reliability.reliability_ai.investigation.contracts import ToolCallRecord
    from hmda_reliability.reliability_ai.investigation.replay import (
        replay_investigation,
    )
    from hmda_reliability.reliability_ai.investigation.tools import (
        COMPARE_PROFILES_TOOL,
    )

    class ForeignRegistry:
        definitions = (COMPARE_PROFILES_TOOL,)

        def execute(self, tool_call: ToolCall) -> tuple[ToolCallRecord, str]:
            record = ToolCallRecord(
                call_id=tool_call.id,
                tool_name=tool_call.function.name,
                result={"value": "foreign-private-value"},
                latency_ms=1,
                status="success",
            )
            return record.model_copy(
                update={changed: "foreign"}
            ), '{"value":"foreign-private-value"}'

    provider = MagicMock()
    provider.invoke.side_effect = [
        ProviderResponse(
            content="",
            tool_calls=(
                ToolCall(
                    id="requested",
                    function=ToolCallFunction(name="compare_profiles", arguments="{}"),
                ),
            ),
            latency_ms=0,
            attempt_count=1,
        ),
        ProviderResponse(
            content='{"findings":[],"hypotheses":[],"uncertainties":[]}',
            latency_ms=0,
            attempt_count=1,
        ),
    ]
    material = null_spike_review_material
    result = investigate_incident(
        AgenticReviewInput(
            incident=material.detection.incident,
            evidence=(material.detection.evidence,),
            draft=material.draft,
            project_revision="tool-identity",
        ),
        provider=provider,
        tool_registry=ForeignRegistry(),
        artifact_root=tmp_path,
    )
    assert result.failure_code == "tool_observation_mismatch"
    assert provider.invoke.call_count == 1
    assert not any(
        b"foreign-private-value" in p.read_bytes()
        for p in tmp_path.rglob("*")
        if p.is_file()
    )
    assert result.manifest_path is not None
    assert (
        replay_investigation(result.manifest_path).failure_code
        == "tool_observation_mismatch"
    )


@pytest.mark.component
@pytest.mark.parametrize(
    ("opening", "closing"),
    [
        ("", ""),
        ("```json\n", "\n```"),
        ("```\n", "\n```"),
        ("```json\n", ""),
        ("", "\n```"),
    ],
)
def test_private_fields_inside_wire_json_stay_out_of_every_observation(
    null_spike_review_material: NullSpikeReviewMaterial,
    native_prompt_client: MagicMock,
    tmp_path: Path,
    opening: str,
    closing: str,
) -> None:
    from hmda_reliability.reliability_ai.context import project_remote_output

    provider = MagicMock()
    provider.invoke.side_effect = [
        ProviderResponse(
            content="",
            tool_calls=(
                ToolCall(
                    id="call",
                    function=ToolCallFunction(
                        name="compare_profiles",
                        arguments='{"api_key":"synthetic-canary","column":"income"}',
                    ),
                ),
            ),
            latency_ms=0,
            attempt_count=1,
        ),
        ProviderResponse(
            content=opening
            + (
                '{"findings":[],"hypotheses":[],"uncertainties":[],'
                '"extra":{"api_key":"synthetic-canary"}}'
            )
            + closing,
            latency_ms=0,
            attempt_count=1,
        ),
    ]
    material = null_spike_review_material
    result = investigate_incident(
        AgenticReviewInput(
            incident=material.detection.incident,
            evidence=(material.detection.evidence,),
            draft=material.draft,
            project_revision="synthetic-observation",
        ),
        provider=provider,
        observe_io=True,
        artifact_root=tmp_path,
    )
    assert result.status == "completed"
    assert "synthetic-canary" in result.turns[-1].content
    # The experiment task uses the same projection as generation, tool and root spans.
    dataset_output = project_remote_output(result.model_dump(mode="json"))
    assert "synthetic-canary" not in json.dumps(dataset_output)
    assert "synthetic-canary" not in str(native_prompt_client.mock_calls)
