"""Bounded OpenAI-compatible provider adapter contract tests."""

from __future__ import annotations

import json
from functools import partial

import httpx
import pytest
from openai import OpenAI

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


class RecordingTransport:
    """Record requests while returning or raising each configured outcome."""

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
    """어댑터가 스트리밍/도구를 끄고 json_object 단일 요청을 보내는지 검증한다."""
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
    transport = RecordingTransport([transport_response])
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


def test_default_sdk_transport_maps_request_and_normalizes_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payloads: list[dict[str, object]] = []

    def respond(request: httpx.Request) -> httpx.Response:
        payloads.append(json.loads(request.content))
        return httpx.Response(
            200,
            headers={"x-request-id": "sdk-request"},
            json={
                "id": "completion-1",
                "object": "chat.completion",
                "created": 0,
                "model": "test-model",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": '{"ok":true}'},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 3,
                    "total_tokens": 13,
                },
            },
        )

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        monkeypatch.setattr(
            provider_module, "OpenAI", partial(OpenAI, http_client=client)
        )
        result = provider_module.OpenAICompatibleAdapter(
            _settings(max_output_tokens=17)
        ).invoke(_messages())

    assert payloads == [
        {
            "messages": [
                {"role": "system", "content": "Return one JSON object."},
                {"role": "user", "content": '{"value":1}'},
            ],
            "model": "test-model",
            "temperature": 0,
            "max_tokens": 17,
            "response_format": {"type": "json_object"},
            "stream": False,
        }
    ]
    assert result.content == '{"ok":true}'
    assert result.attempt_count == 1
    assert result.trace_id == "sdk-request"
    assert result.usage == runtime_contracts.ProviderUsage(
        prompt_tokens=10, completion_tokens=3, total_tokens=13
    )


@pytest.mark.parametrize(
    ("content", "finish_reason", "empty_choices", "expected_state", "expected_reason"),
    [
        ('{"ok":true}', "stop", False, "text", "stop"),
        ('{"ok":true}', "length", False, "text", "length"),
        (None, "length", False, "content_missing", "length"),
        ("", "stop", False, "text", "stop"),
        (None, "stop", True, "choices_empty", None),
        ("{}", "PRIVATE_PROVIDER_REASON", False, "text", "unknown"),
        ("{}", [], False, "text", "unknown"),
        ("{}", {}, False, "text", "unknown"),
    ],
)
def test_sdk_retains_only_allowlisted_completion_metadata(
    monkeypatch: pytest.MonkeyPatch,
    content: str | None,
    finish_reason: object,
    empty_choices: bool,
    expected_state: str,
    expected_reason: str | None,
) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "metadata-completion",
                "object": "chat.completion",
                "created": 0,
                "model": "test-model",
                "choices": []
                if empty_choices
                else [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": content},
                        "finish_reason": finish_reason,
                    }
                ],
            },
        )

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        monkeypatch.setattr(
            provider_module, "OpenAI", partial(OpenAI, http_client=client)
        )
        result = provider_module.OpenAICompatibleAdapter(_settings()).invoke(
            _messages()
        )

    assert result.attempt_count == 1
    assert result.response_metadata is not None
    assert result.response_metadata.content_state == expected_state
    assert result.response_metadata.finish_reason == expected_reason
    assert result.response_metadata.content_bytes == len(
        (content or "").encode("utf-8")
    )
    assert "PRIVATE" not in result.response_metadata.model_dump_json()


@pytest.mark.parametrize(
    ("status_code", "failure_code", "max_retries", "expected_attempts"),
    [
        (400, "provider_client_error", 0, 1),
        (500, "provider_server_error", 0, 1),
        (None, "provider_connection_error", 0, 1),
        (400, "provider_client_error", 1, 1),
        (500, "provider_server_error", 2, 3),
        (None, "provider_connection_error", 2, 3),
    ],
    ids=[
        "client-no-budget",
        "server-no-budget",
        "connection-no-budget",
        "client-positive-budget",
        "server-budget-exhausted",
        "connection-budget-exhausted",
    ],
)
def test_default_sdk_transport_obeys_retry_policy_for_errors(
    monkeypatch: pytest.MonkeyPatch,
    status_code: int | None,
    failure_code: str,
    max_retries: int,
    expected_attempts: int,
) -> None:
    calls = 0

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if status_code is None:
            raise httpx.ConnectError("injected connection failure", request=request)
        return httpx.Response(status_code, json={"error": {"message": "test failure"}})

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        monkeypatch.setattr(
            provider_module, "OpenAI", partial(OpenAI, http_client=client)
        )
        adapter = provider_module.OpenAICompatibleAdapter(
            _settings(max_retries=max_retries), sleep=lambda _: None
        )
        with pytest.raises(provider_module.ProviderUnavailableError) as error:
            adapter.invoke(_messages())

    assert calls == expected_attempts
    assert error.value.failure_code == failure_code
    assert error.value.attempt_count == expected_attempts


@pytest.mark.parametrize("status_code", [500, None], ids=["server", "connection"])
def test_default_sdk_transport_retries_transient_failure_then_succeeds(
    monkeypatch: pytest.MonkeyPatch,
    status_code: int | None,
) -> None:
    calls = 0

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            if status_code is None:
                raise httpx.ConnectError("injected connection failure", request=request)
            return httpx.Response(
                status_code, json={"error": {"message": "transient test failure"}}
            )
        return httpx.Response(
            200,
            json={
                "id": "retry-completion",
                "object": "chat.completion",
                "created": 0,
                "model": "test-model",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "{}"},
                        "finish_reason": "stop",
                    }
                ],
            },
        )

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        monkeypatch.setattr(
            provider_module, "OpenAI", partial(OpenAI, http_client=client)
        )
        adapter = provider_module.OpenAICompatibleAdapter(
            _settings(max_retries=1), sleep=lambda _: None
        )
        result = adapter.invoke(_messages())

    assert calls == 2
    assert result.attempt_count == 2
    assert result.content == "{}"


def test_adapter_owns_bounded_retry_for_retryable_transport_failures() -> None:
    """재시도 가능한 전송 오류(retryable=True) 시 한도까지 재시도하는지 검증한다."""
    transport = RecordingTransport(
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
    """재시도 불가능한 오류(4xx 등)는 재시도 없이 즉시 실패하는지 검증한다."""
    transport = RecordingTransport(
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


@pytest.mark.parametrize("content", ["x" * 33, "한" * 11])
def test_adapter_rejects_oversized_response_without_retry(content: str) -> None:
    """응답 크기가 max_output_bytes 초과 시 ProviderResponseTooLargeError를 낸다."""
    transport = RecordingTransport(
        [runtime_contracts.TransportResponse(content=content)]
    )
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
    """SDK 생성 시 max_retries=0으로 내부 재시도를 비활성화하는지 검증한다."""
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
    """로컬 및 클라우드 엔드포인트 모두 동일한 wire 규격을 사용하는지 검증한다."""
    messages = _messages()
    transport = RecordingTransport([runtime_contracts.TransportResponse(content="{}")])
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
