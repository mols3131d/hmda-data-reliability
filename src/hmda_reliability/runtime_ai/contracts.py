"""Provider 중립적 AI 런타임 계약 모듈."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    StringConstraints,
    model_serializer,
    model_validator,
)

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class RuntimeAIContract(BaseModel):
    """Provider 중립적 AI 런타임 값을 위한 불변 기본 계약.

    알려지지 않은 추가 필드(`extra="forbid"`)를 엄격히 금지하고
    모델 불변성(`frozen=True`) 및 특수 부동소수점 금지(`allow_inf_nan=False`)를
    보장한다.
    """

    model_config = ConfigDict(allow_inf_nan=False, extra="forbid", frozen=True)


class ToolFunctionDefinition(RuntimeAIContract):
    """모델에 노출할 읽기 전용 도구 함수 스키마 정의."""

    name: NonEmptyStr
    description: NonEmptyStr
    parameters: dict[str, Any]


class ToolDefinition(RuntimeAIContract):
    """OpenAI 호환 function tool 정의."""

    type: Literal["function"] = "function"
    function: ToolFunctionDefinition


class ToolCallFunction(RuntimeAIContract):
    """모델이 요청한 단일 도구 함수 호출 정보."""

    name: NonEmptyStr
    arguments: str = ""


class ToolCall(RuntimeAIContract):
    """모델이 반환한 단일 도구 호출 계약."""

    id: NonEmptyStr
    type: Literal["function"] = "function"
    function: ToolCallFunction


class ChatMessage(RuntimeAIContract):
    """단일 채팅 메시지 표현.

    LLM 제공자에게 전달되는 역할(`role`), 내용(`content`) 및 선택적 도구 호출
    메타데이터(`tool_calls`, `tool_call_id`, `name`)를 소유한다.
    """

    role: Literal["system", "user", "assistant", "tool"]
    content: str = ""
    tool_calls: tuple[ToolCall, ...] | None = None
    tool_call_id: NonEmptyStr | None = None
    name: NonEmptyStr | None = None

    @model_validator(mode="after")
    def validate_message_by_role(self) -> ChatMessage:
        has_content = len(self.content) > 0
        has_tool_calls = bool(self.tool_calls)
        if self.role == "tool":
            if self.tool_call_id is None:
                msg = "tool messages require tool_call_id"
                raise ValueError(msg)
            if not has_content:
                msg = "tool messages require non-empty content"
                raise ValueError(msg)
            if self.tool_calls is not None:
                msg = "tool messages cannot declare tool_calls"
                raise ValueError(msg)
            return self
        if self.role == "assistant":
            if not has_content and not has_tool_calls:
                msg = "assistant messages require non-empty content or tool_calls"
                raise ValueError(msg)
            if self.tool_call_id is not None:
                msg = "assistant messages cannot declare tool_call_id"
                raise ValueError(msg)
            return self
        if not has_content:
            msg = f"{self.role} messages require non-empty content"
            raise ValueError(msg)
        if self.tool_calls is not None or self.tool_call_id is not None:
            msg = f"{self.role} messages cannot declare tool_calls or tool_call_id"
            raise ValueError(msg)
        return self

    @model_serializer(mode="wrap")
    def _serialize_wire_message(
        self,
        handler: SerializerFunctionWrapHandler,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = handler(self)
        for optional_key in ("tool_calls", "tool_call_id", "name"):
            if payload.get(optional_key) is None:
                payload.pop(optional_key, None)
        return payload


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
    content_state: Literal[
        "text", "tool_calls", "invalid_tool_calls", "content_missing", "choices_empty"
    ]
    content_bytes: int = Field(ge=0)


class TransportResponse(RuntimeAIContract):
    """전송(Transport) 계층에서 어댑터 계층으로 전달되는 1회 시도 응답 DTO."""

    content: str
    tool_calls: tuple[ToolCall, ...] = ()
    raw_tool_calls: str | None = None
    usage: ProviderUsage | None = None
    trace_id: str | None = None
    response_metadata: ProviderResponseMetadata | None = None


class TransportTimeouts(RuntimeAIContract):
    """HTTP 전송의 각 대기 구간에 적용하며 wire 본문에는 넣지 않는 제한."""

    connect: float = Field(gt=0)
    read: float = Field(gt=0)
    write: float = Field(gt=0)
    pool: float = Field(gt=0)


class ChatCompletionRequest(RuntimeAIContract):
    """OpenAI 호환 wire 규격에 맞춘 단일 Chat Completion 요청 페이로드 계약.

    스트리밍을 비활성화하고, 기본 JSON 응답은 `response_format`으로 요청하며
    일반 텍스트나 도구 호출 요청에서는 선택적으로 생략한다.
    """

    messages: tuple[ChatMessage, ...]
    model: str
    temperature: int
    max_tokens: int = Field(gt=0)
    response_format: dict[str, str] | None
    stream: bool
    tools: tuple[ToolDefinition, ...] | None = None
    tool_choice: Literal["auto", "none"] | None = None
    timeout: TransportTimeouts | None = None

    @model_validator(mode="after")
    def validate_wire_profile(self) -> ChatCompletionRequest:
        if self.tools is not None and len(self.tools) == 0:
            msg = "tools must not be empty when provided"
            raise ValueError(msg)
        return self

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
        if self.tools is not None:
            payload["tools"] = [tool.model_dump(mode="json") for tool in self.tools]
        if self.tool_choice is not None:
            payload["tool_choice"] = self.tool_choice
        payload["stream"] = self.stream
        return payload


class ProviderResponse(RuntimeAIContract):
    """어댑터 호출이 성공했을 때 반환되는 최종 provider 응답 계약.

    단일 완료 텍스트(`content`) 및 도구 호출(`tool_calls`) 외에 바운디드 재시도
    루프에서 기록된 총 시도 횟수(`attempt_count`), 누적 소요 시간(`latency_ms`),
    토큰 사용량(`usage`), 그리고 요청 추적 식별자(`trace_id`)를 포함한다.
    """

    content: str
    tool_calls: tuple[ToolCall, ...] = ()
    raw_tool_calls: str | None = None
    attempt_count: int = Field(ge=1)
    latency_ms: float = Field(ge=0)
    usage: ProviderUsage | None = None
    trace_id: str | None = None
    response_metadata: ProviderResponseMetadata | None = None
