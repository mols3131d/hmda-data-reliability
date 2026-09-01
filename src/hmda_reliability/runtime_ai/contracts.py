"""Provider 중립적 AI 런타임 계약 모듈."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RuntimeAIContract(BaseModel):
    """Provider 중립적 AI 런타임 값을 위한 불변 기본 계약."""

    model_config = ConfigDict(allow_inf_nan=False, extra="forbid", frozen=True)


class ChatMessage(RuntimeAIContract):
    role: Literal["system", "user"]
    content: str = Field(min_length=1)


class ProviderUsage(RuntimeAIContract):
    prompt_tokens: int | None = Field(default=None, ge=0)
    completion_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)


class TransportResponse(RuntimeAIContract):
    content: str
    usage: ProviderUsage | None = None
    trace_id: str | None = None


class ChatCompletionRequest(RuntimeAIContract):
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


class ProviderResponse(RuntimeAIContract):
    content: str
    attempt_count: int = Field(ge=1)
    latency_ms: float = Field(ge=0)
    usage: ProviderUsage | None = None
    trace_id: str | None = None
