"""경량 OpenAI 호환 chat-completions 어댑터 모듈."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Protocol, cast

from openai import APIConnectionError, APIError, APIStatusError, OpenAI
from openai.types.chat import ChatCompletionMessageParam

from hmda_reliability.logger import get_logger
from hmda_reliability.runtime_ai.contracts import (
    ChatCompletionRequest,
    ChatMessage,
    ProviderResponse,
    ProviderUsage,
    TransportResponse,
)
from hmda_reliability.runtime_ai.settings import RuntimeAISettings

_LOGGER = get_logger(__name__)

# 재시도 간 지수 백오프 기본 단위 (0.25초) 및 최대 백오프 상한 (1.0초)
_INITIAL_BACKOFF_SECONDS = 0.25
_MAX_BACKOFF_SECONDS = 1.0


def _calculate_backoff_delay(attempt: int) -> float:
    """1-based 시도 횟수(attempt)에 따른 지수 백오프 지연(초)을 계산한다.

    1차 실패 후 attempt=1일 때 0.25s, attempt=2일 때 0.5s, 이후 최대 1.0s로 상한된다.
    """
    delay = _INITIAL_BACKOFF_SECONDS * (2 ** (attempt - 1))
    return min(delay, _MAX_BACKOFF_SECONDS)


class ProviderTransportError(Exception):
    """SDK 경계에서 분류된 정제된 전송(transport) 실패 예외.

    upstream OpenAI SDK 예외를 내부 실패 코드(`failure_code`)와
    재시도 가능 여부(`retryable`) 플래그로 캡슐화한다.
    """

    def __init__(self, *, failure_code: str, retryable: bool) -> None:
        super().__init__(failure_code)
        self.failure_code = failure_code
        self.retryable = retryable


class ProviderUnavailableError(Exception):
    """제한된 재시도 횟수 내에 응답을 받지 못했을 때 발생하는 예외.

    네트워크 단절, 서버 5xx 에러 또는 재시도 불가능한 클라이언트 4xx 에러 등으로 인해
    최종적으로 provider 호출이 불가능할 때 발생한다.
    """

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
    """Provider 응답 바이트 크기가 설정된 한도를 초과할 때 발생하는 예외.

    `max_output_bytes`를 초과하는 응답은 재시도 없이 즉시 이 예외로 차단된다.
    """

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
    """Chat Completion 요청을 전송 계층으로 위임하기 위한 내부 프로토콜."""

    def create(self, request: ChatCompletionRequest) -> TransportResponse: ...


class OpenAICompatibleAdapter:
    """어댑터 자체 재시도 로직이 포함된 provider 중립적 요청 어댑터.

    SDK의 숨겨진 재시도를 끄고(`max_retries=0`), 이 어댑터 클래스가
    지수 백오프 및 최대 재시도 제약(`max_retries`)을 단독으로 소유한다.
    """

    def __init__(
        self,
        settings: RuntimeAISettings,
        *,
        transport: ChatCompletionTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._settings = settings
        self._sleep = sleep
        if transport is None:
            # SDK 레벨의 내부 재시도를 끄고 어댑터가 재시도 불변식을 통제한다.
            client = OpenAI(
                api_key=settings.api_key.get_secret_value(),
                base_url=str(settings.base_url),
                timeout=settings.timeout_seconds,
                max_retries=0,
            )
            transport = _OpenAIChatCompletionTransport(client)
        self._transport = transport

    def invoke(self, messages: tuple[ChatMessage, ...]) -> ProviderResponse:
        """지수 백오프 재시도를 적용하여 chat completion 전송을 호출한다.

        설정된 모델, temperature=0, 토큰 제한 및 JSON 형식을 적용한다.
        전송 에러를 `ProviderUnavailableError`로 정제하고, 응답 바이트 크기를
        `max_output_bytes` 한도로 제한한다.
        """
        request = ChatCompletionRequest(
            messages=messages,
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
                _LOGGER.debug(
                    "provider 호출 시도",
                    extra={
                        "model": self._settings.model,
                        "attempt": attempt_count,
                        "message_count": len(messages),
                    },
                )
                response = self._transport.create(request)
            except ProviderTransportError as error:
                can_retry = (
                    error.retryable and attempt_count <= self._settings.max_retries
                )
                if can_retry:
                    _LOGGER.warning(
                        "provider 호출 재시도",
                        extra={
                            "attempt": attempt_count,
                            "failure_code": error.failure_code,
                            "max_retries": self._settings.max_retries,
                        },
                    )
                    self._sleep(_calculate_backoff_delay(attempt_count))
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
    """OpenAI Python SDK와 직접 통신하는 유일한 전송 어댑터 구현체."""

    def __init__(self, client: OpenAI) -> None:
        self._client = client

    def create(self, request: ChatCompletionRequest) -> TransportResponse:
        """SDK completions API를 동기 호출하고 예외 및 응답 형식을 정규화한다."""
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
    """단조 증가 타이머 기준 시작 시점 대비 경과 시간(밀리초)을 반환한다."""
    return max(0.0, (time.monotonic() - started) * 1000)
