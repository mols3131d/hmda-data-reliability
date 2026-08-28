"""Bounded OpenAI-compatible provider adapter contract tests."""

from __future__ import annotations

import pytest

from hmda_reliability.runtime_ai import contracts as runtime_contracts
from hmda_reliability.runtime_ai import provider as provider_module
from hmda_reliability.runtime_ai.settings import RuntimeAISettings

pytestmark = pytest.mark.unit


def _messages() -> tuple[runtime_contracts.ChatMessage, ...]:
    return (
        runtime_contracts.ChatMessage(
            role="system",
            content="Return one JSON object.",
        ),
        runtime_contracts.ChatMessage(
            role="user",
            content='{"value":1}',
        ),
    )


def _settings(**updates: object) -> RuntimeAISettings:
    values: dict[str, object] = {
        "base_url": "http://localhost:11434/v1",
        "api_key": "local-test-key",
        "model": "test-model",
    }
    values.update(updates)
    return RuntimeAISettings.model_validate(values)


class FakeTransport:
    def __init__(
        self,
        outcomes: list[
            runtime_contracts.TransportResponse | provider_module.ProviderTransportError
        ],
    ) -> None:
        self.outcomes = list(outcomes)
        self.requests: list[runtime_contracts.ChatCompletionRequest] = []

    def create(
        self,
        request: runtime_contracts.ChatCompletionRequest,
    ) -> runtime_contracts.TransportResponse:
        self.requests.append(request)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, provider_module.ProviderTransportError):
            raise outcome
        return outcome


def test_adapter_uses_the_common_non_streaming_no_tools_wire_profile() -> None:
    messages = _messages()
    transport_response = runtime_contracts.TransportResponse(
        content='{"review_summary":"ok"}',
        usage=runtime_contracts.ProviderUsage(
            prompt_tokens=100,
            completion_tokens=20,
            total_tokens=120,
        ),
        trace_id="req-1",
    )
    transport = FakeTransport([transport_response])
    adapter = provider_module.OpenAICompatibleAdapter(
        _settings(), transport=transport, sleep=lambda _: None
    )

    response = adapter.invoke(messages)

    request = transport.requests[0]
    wire = request.wire_payload()
    assert wire["model"] == "test-model"
    assert wire["temperature"] == 0
    assert wire["max_tokens"] == 1024
    assert wire["response_format"] == {"type": "json_object"}
    assert wire["stream"] is False
    assert "tools" not in wire
    assert wire["messages"] == [message.model_dump(mode="json") for message in messages]
    assert response.content == transport_response.content
    assert response.attempt_count == 1
    assert response.usage == transport_response.usage


def test_adapter_owns_bounded_retry_for_retryable_transport_failures() -> None:
    transport = FakeTransport(
        [
            provider_module.ProviderTransportError(
                failure_code="provider_connection_error",
                retryable=True,
            ),
            runtime_contracts.TransportResponse(content="{}"),
        ]
    )
    adapter = provider_module.OpenAICompatibleAdapter(
        _settings(max_retries=1), transport=transport, sleep=lambda _: None
    )

    result = adapter.invoke(_messages())

    assert result.attempt_count == 2
    assert len(transport.requests) == 2


def test_adapter_does_not_retry_non_retryable_transport_failures() -> None:
    transport = FakeTransport(
        [
            provider_module.ProviderTransportError(
                failure_code="provider_client_error",
                retryable=False,
            )
        ]
    )
    adapter = provider_module.OpenAICompatibleAdapter(
        _settings(max_retries=5), transport=transport, sleep=lambda _: None
    )

    with pytest.raises(provider_module.ProviderUnavailableError) as error:
        adapter.invoke(_messages())

    assert error.value.attempt_count == 1
    assert error.value.failure_code == "provider_client_error"
    assert len(transport.requests) == 1


def test_adapter_rejects_oversized_response_without_retry() -> None:
    transport = FakeTransport([runtime_contracts.TransportResponse(content="x" * 33)])
    adapter = provider_module.OpenAICompatibleAdapter(
        _settings(max_output_bytes=32),
        transport=transport,
        sleep=lambda _: None,
    )

    with pytest.raises(provider_module.ProviderResponseTooLargeError):
        adapter.invoke(_messages())

    assert len(transport.requests) == 1


def test_adapter_disables_sdk_hidden_retry_and_passes_explicit_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeOpenAI:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)

    monkeypatch.setattr(provider_module, "OpenAI", FakeOpenAI)
    provider_module.OpenAICompatibleAdapter(_settings())

    assert captured == {
        "api_key": "local-test-key",
        "base_url": "http://localhost:11434/v1",
        "timeout": 30.0,
        "max_retries": 0,
    }


@pytest.mark.parametrize(
    "base_url",
    ["http://localhost:11434/v1", "https://api.openai.com/v1"],
)
def test_local_and_cloud_urls_use_the_same_adapter_request(base_url: str) -> None:
    messages = _messages()
    transport = FakeTransport([runtime_contracts.TransportResponse(content="{}")])
    adapter = provider_module.OpenAICompatibleAdapter(
        _settings(base_url=base_url), transport=transport, sleep=lambda _: None
    )

    adapter.invoke(messages)

    assert transport.requests[0].wire_payload() == {
        "messages": [message.model_dump(mode="json") for message in messages],
        "model": "test-model",
        "temperature": 0,
        "max_tokens": 1024,
        "response_format": {"type": "json_object"},
        "stream": False,
    }
