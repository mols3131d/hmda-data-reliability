"""Thin OpenAI-compatible chat-completions adapter."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Protocol, cast

from openai import APIConnectionError, APIError, APIStatusError, OpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import Field

from hmda_reliability.reliability.agentic_review.prompt import (
    ChatMessage,
    RenderedPrompt,
)
from hmda_reliability.reliability.agentic_review.settings import (
    AgenticReviewSettings,
)
from hmda_reliability.reliability.contracts.base import ReliabilityContract


class ProviderUsage(ReliabilityContract):
    prompt_tokens: int | None = Field(default=None, ge=0)
    completion_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)


class TransportResponse(ReliabilityContract):
    content: str
    usage: ProviderUsage | None = None
    trace_id: str | None = None


class ChatCompletionRequest(ReliabilityContract):
    messages: tuple[ChatMessage, ...]
    model: str
    temperature: int
    max_tokens: int = Field(gt=0)
    response_format: dict[str, str]
    stream: bool

    def wire_payload(self) -> dict[str, object]:
        return {
            "messages": [message.model_dump(mode="json") for message in self.messages],
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "response_format": dict(self.response_format),
            "stream": self.stream,
        }


class ProviderResponse(ReliabilityContract):
    content: str
    attempt_count: int = Field(ge=1)
    latency_ms: float = Field(ge=0)
    usage: ProviderUsage | None = None
    trace_id: str | None = None


class ProviderTransportError(Exception):
    """Sanitized transport failure classified at the SDK boundary."""

    def __init__(self, *, failure_code: str, retryable: bool) -> None:
        super().__init__(failure_code)
        self.failure_code = failure_code
        self.retryable = retryable


class ProviderUnavailableError(Exception):
    """Bounded transport attempts ended without a provider response."""

    def __init__(
        self,
        *,
        failure_code: str,
        attempt_count: int,
        latency_ms: float,
    ) -> None:
        super().__init__("provider unavailable after bounded attempts")
        self.failure_code = failure_code
        self.attempt_count = attempt_count
        self.latency_ms = latency_ms


class ProviderResponseTooLargeError(Exception):
    """Provider content exceeded the configured response byte boundary."""

    def __init__(
        self,
        *,
        attempt_count: int,
        latency_ms: float,
        actual_bytes: int,
        max_bytes: int,
        usage: ProviderUsage | None,
        trace_id: str | None,
    ) -> None:
        super().__init__("provider response exceeds max_output_bytes")
        self.attempt_count = attempt_count
        self.latency_ms = latency_ms
        self.actual_bytes = actual_bytes
        self.max_bytes = max_bytes
        self.usage = usage
        self.trace_id = trace_id


class ChatCompletionTransport(Protocol):
    def create(self, request: ChatCompletionRequest) -> TransportResponse: ...


class OpenAICompatibleAdapter:
    """Apply one provider-neutral request profile with adapter-owned retries."""

    def __init__(
        self,
        settings: AgenticReviewSettings,
        *,
        transport: ChatCompletionTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._settings = settings
        self._sleep = sleep
        if transport is None:
            client = OpenAI(
                api_key=settings.api_key.get_secret_value(),
                base_url=str(settings.base_url),
                timeout=settings.timeout_seconds,
                max_retries=0,
            )
            transport = _OpenAIChatCompletionTransport(client)
        self._transport = transport

    def invoke(self, rendered: RenderedPrompt) -> ProviderResponse:
        request = ChatCompletionRequest(
            messages=rendered.messages,
            model=self._settings.model,
            temperature=self._settings.temperature,
            max_tokens=self._settings.max_output_tokens,
            response_format={"type": "json_object"},
            stream=False,
        )
        started = time.monotonic()
        attempt_count = 0
        while True:
            attempt_count += 1
            try:
                response = self._transport.create(request)
            except ProviderTransportError as error:
                can_retry = (
                    error.retryable and attempt_count <= self._settings.max_retries
                )
                if can_retry:
                    self._sleep(min(0.25 * (2 ** (attempt_count - 1)), 1.0))
                    continue
                raise ProviderUnavailableError(
                    failure_code=error.failure_code,
                    attempt_count=attempt_count,
                    latency_ms=_elapsed_ms(started),
                ) from None

            latency_ms = _elapsed_ms(started)
            output_bytes = len(response.content.encode("utf-8"))
            if output_bytes > self._settings.max_output_bytes:
                raise ProviderResponseTooLargeError(
                    attempt_count=attempt_count,
                    latency_ms=latency_ms,
                    actual_bytes=output_bytes,
                    max_bytes=self._settings.max_output_bytes,
                    usage=response.usage,
                    trace_id=response.trace_id,
                )
            return ProviderResponse(
                content=response.content,
                attempt_count=attempt_count,
                latency_ms=latency_ms,
                usage=response.usage,
                trace_id=response.trace_id,
            )


class _OpenAIChatCompletionTransport:
    """The only module surface that calls the OpenAI Python SDK."""

    def __init__(self, client: OpenAI) -> None:
        self._client = client

    def create(self, request: ChatCompletionRequest) -> TransportResponse:
        messages: list[ChatCompletionMessageParam] = [
            cast(
                ChatCompletionMessageParam,
                message.model_dump(mode="json"),
            )
            for message in request.messages
        ]
        try:
            response = self._client.chat.completions.create(
                messages=messages,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                response_format={"type": "json_object"},
                stream=False,
            )
        except APIConnectionError as error:
            raise ProviderTransportError(
                failure_code="provider_connection_error",
                retryable=True,
            ) from error
        except APIStatusError as error:
            is_server_error = error.status_code >= 500
            raise ProviderTransportError(
                failure_code=(
                    "provider_server_error"
                    if is_server_error
                    else "provider_client_error"
                ),
                retryable=is_server_error,
            ) from error
        except APIError as error:
            raise ProviderTransportError(
                failure_code="provider_error",
                retryable=False,
            ) from error

        content = ""
        if response.choices:
            content = response.choices[0].message.content or ""
        usage = None
        if response.usage is not None:
            usage = ProviderUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )
        return TransportResponse(
            content=content,
            usage=usage,
            trace_id=response._request_id,
        )


def _elapsed_ms(started: float) -> float:
    return max(0.0, (time.monotonic() - started) * 1000)
