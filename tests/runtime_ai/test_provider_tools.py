"""Bounded tool-calling contract tests for the OpenAI-compatible adapter."""

from __future__ import annotations

import json
from functools import partial

import httpx
import pytest
from openai import OpenAI
from pydantic import ValidationError

from hmda_reliability.runtime_ai import contracts as runtime_contracts
from hmda_reliability.runtime_ai import provider as provider_module
from hmda_reliability.runtime_ai.settings import RuntimeAISettings

pytestmark = pytest.mark.unit

_TOOL = runtime_contracts.ToolDefinition(
    function=runtime_contracts.ToolFunctionDefinition(
        name="get_incident_evidence",
        description="Return bounded evidence.",
        parameters={"type": "object", "properties": {}, "additionalProperties": False},
    )
)


def _settings() -> RuntimeAISettings:
    return RuntimeAISettings.model_validate(
        {
            "base_url": "http://localhost:11434/v1",
            "api_key": "local-test-key",
            "model": "test-model",
        }
    )


def _messages() -> tuple[runtime_contracts.ChatMessage, ...]:
    return (
        runtime_contracts.ChatMessage(role="system", content="Investigate."),
        runtime_contracts.ChatMessage(role="user", content="incident"),
    )


def test_sdk_sends_tools_and_normalizes_tool_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payloads: list[dict[str, object]] = []

    def respond(request: httpx.Request) -> httpx.Response:
        payloads.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "id": "tool-completion",
                "object": "chat.completion",
                "created": 0,
                "model": "test-model",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call_1",
                                    "type": "function",
                                    "function": {
                                        "name": "get_incident_evidence",
                                        "arguments": "{}",
                                    },
                                }
                            ],
                        },
                        "finish_reason": "tool_calls",
                    }
                ],
            },
        )

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        monkeypatch.setattr(
            provider_module, "OpenAI", partial(OpenAI, http_client=client)
        )
        result = provider_module.OpenAICompatibleAdapter(_settings()).invoke(
            _messages(), output_format="text", tools=(_TOOL,), tool_choice="auto"
        )

    assert payloads[0]["tools"] == [_TOOL.model_dump(mode="json")]
    assert payloads[0]["tool_choice"] == "auto"
    assert "response_format" not in payloads[0]
    assert result.tool_calls == (
        runtime_contracts.ToolCall(
            id="call_1",
            function=runtime_contracts.ToolCallFunction(
                name="get_incident_evidence", arguments="{}"
            ),
        ),
    )
    assert result.response_metadata is not None
    assert result.response_metadata.content_state == "tool_calls"
    assert result.response_metadata.finish_reason == "tool_calls"


def test_tool_history_messages_serialize_to_the_wire_profile() -> None:
    call = runtime_contracts.ToolCall(
        id="call_1",
        function=runtime_contracts.ToolCallFunction(
            name="get_incident_evidence", arguments="{}"
        ),
    )
    assistant = runtime_contracts.ChatMessage(role="assistant", tool_calls=(call,))
    tool = runtime_contracts.ChatMessage(
        role="tool", tool_call_id="call_1", content='{"ok":true}'
    )

    assert assistant.model_dump(mode="json") == {
        "role": "assistant",
        "content": "",
        "tool_calls": [call.model_dump(mode="json")],
    }
    assert tool.model_dump(mode="json") == {
        "role": "tool",
        "content": '{"ok":true}',
        "tool_call_id": "call_1",
    }


@pytest.mark.parametrize(
    "values",
    [
        {"role": "tool", "content": "x"},
        {"role": "tool", "tool_call_id": "c", "content": ""},
        {"role": "assistant", "content": ""},
        {"role": "user", "content": "x", "tool_call_id": "c"},
        {"role": "system", "content": ""},
    ],
)
def test_invalid_role_shapes_are_rejected(values: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        runtime_contracts.ChatMessage.model_validate(values)


def test_tool_call_arguments_count_toward_output_byte_cap() -> None:
    class Transport:
        def create(
            self, request: runtime_contracts.ChatCompletionRequest
        ) -> runtime_contracts.TransportResponse:
            return runtime_contracts.TransportResponse(
                content="",
                tool_calls=(
                    runtime_contracts.ToolCall(
                        id="c",
                        function=runtime_contracts.ToolCallFunction(
                            name="get_incident_evidence", arguments="x" * 64
                        ),
                    ),
                ),
            )

    settings = _settings().model_copy(update={"max_output_bytes": 32})
    adapter = provider_module.OpenAICompatibleAdapter(settings, transport=Transport())

    with pytest.raises(provider_module.ProviderResponseTooLargeError):
        adapter.invoke(_messages(), tools=(_TOOL,))


def test_invalid_raw_tool_calls_count_toward_output_byte_cap() -> None:
    raw_calls = json.dumps(
        [{"id": "", "function": {"arguments": "x" * 64}}], separators=(",", ":")
    )

    class Transport:
        def create(
            self, request: runtime_contracts.ChatCompletionRequest
        ) -> runtime_contracts.TransportResponse:
            return runtime_contracts.TransportResponse(
                content="report", raw_tool_calls=raw_calls
            )

    settings = _settings().model_copy(update={"max_output_bytes": 32})
    adapter = provider_module.OpenAICompatibleAdapter(settings, transport=Transport())

    with pytest.raises(provider_module.ProviderResponseTooLargeError) as error:
        adapter.invoke(_messages(), tools=(_TOOL,))

    assert error.value.actual_bytes == len(("report" + raw_calls).encode("utf-8"))
    assert error.value.attempt_count == 1
