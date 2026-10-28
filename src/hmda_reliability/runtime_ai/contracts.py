"""Provider 중립적 AI 런타임 계약 모듈."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RuntimeAIContract(BaseModel):
    """Provider 중립적 AI 런타임 값을 위한 불변 기본 계약.

    알려지지 않은 추가 필드(`extra="forbid"`)를 엄격히 금지하고
    모델 불변성(`frozen=True`) 및 특수 부동소수점 금지(`allow_inf_nan=False`)를
    보장한다.
    """

    model_config = ConfigDict(allow_inf_nan=False, extra="forbid", frozen=True)


class ChatMessage(RuntimeAIContract):
    """단일 채팅 메시지 표현.

    LLM 제공자에게 전달되는 역할(`role`)과 비어있지 않은 내용(`content`)을 소유한다.
    """

    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)


class ProviderUsage(RuntimeAIContract):
    """LLM 제공자가 반환한 토큰 사용량 메트릭.

    누락된 경우 None일 수 있으며, 값이 있을 때는 음수가 될 수 없다.
    """

    prompt_tokens: int | None = Field(default=None, ge=0)
    completion_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)


class ProviderResponseMetadata(RuntimeAIContract):
    """본문이나 provider 자유 문자열 없이 완료 상태를 설명하는 metadata."""

    finish_reason: (
        Literal[
            "stop", "length", "content_filter", "tool_calls", "function_call", "unknown"
        ]
        | None
    ) = None
    content_state: Literal["text", "content_missing", "choices_empty"]
    content_bytes: int = Field(ge=0)


class TransportResponse(RuntimeAIContract):
    """전송(Transport) 계층에서 어댑터 계층으로 전달되는 1회 시도 응답 DTO.

    응답 본문 텍스트(`content`), 토큰 사용량(`usage`), 그리고 upstream 헤더나
    OpenAI 클라이언트로부터 캡처된 고유 요청 추적 ID(`trace_id`)를 보관한다.
    """

    content: str
    usage: ProviderUsage | None = None
    trace_id: str | None = None
    response_metadata: ProviderResponseMetadata | None = None


class ChatCompletionRequest(RuntimeAIContract):
    """OpenAI 호환 wire 규격에 맞춘 단일 Chat Completion 요청 페이로드 계약.

    스트리밍과 도구 호출(function call/tools)을 비활성화한다. 기본 JSON 응답은
    `response_format`으로 요청하고 일반 텍스트 응답에서는 이 설정을 생략한다.
    """

    messages: tuple[ChatMessage, ...]
    model: str
    temperature: int
    max_tokens: int = Field(gt=0)
    response_format: dict[str, str] | None
    stream: bool

    def wire_payload(self) -> dict[str, object]:
        """OpenAI SDK completions 또는 HTTP wire 호환 dict를 생성한다."""
        payload: dict[str, object] = {
            "messages": [message.model_dump(mode="json") for message in self.messages],
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if self.response_format is not None:
            payload["response_format"] = dict(self.response_format)
        payload["stream"] = self.stream
        return payload


class ProviderResponse(RuntimeAIContract):
    """어댑터 호출이 성공했을 때 반환되는 최종 provider 응답 계약.

    단일 완료 텍스트(`content`) 외에 바운디드 재시도 루프에서 기록된
    총 시도 횟수(`attempt_count`), 누적 소요 시간(`latency_ms`), 토큰 사용량(`usage`),
    그리고 요청 추적 식별자(`trace_id`)를 포함한다.
    """

    content: str
    attempt_count: int = Field(ge=1)
    latency_ms: float = Field(ge=0)
    usage: ProviderUsage | None = None
    trace_id: str | None = None
    response_metadata: ProviderResponseMetadata | None = None
