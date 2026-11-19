"""관리형 ChatGPT 구독으로 새 임시 스레드에서 한 턴을 요청한다."""

from __future__ import annotations

import json
import math
import tempfile
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Literal

from pydantic import Field

from hmda_reliability.runtime_ai.codex_isolation import (
    PreflightError,
    server_command,
    start_thread,
    verify_server,
)
from hmda_reliability.runtime_ai.codex_rpc import (
    AppServer,
    Json,
    ProtocolError,
    RpcRejected,
)
from hmda_reliability.runtime_ai.contracts import (
    ChatMessage,
    CodexAttempt,
    NonEmptyStr,
    ProviderResponse,
    ProviderResponseMetadata,
    RuntimeAIContract,
    ToolCall,
    ToolCallFunction,
    ToolDefinition,
)
from hmda_reliability.runtime_ai.provider import (
    ProviderResponseTooLargeError,
    ProviderUnavailableError,
)


class CodexSettings(RuntimeAIContract):
    model: NonEmptyStr = "codex-default"
    max_output_bytes: int = Field(default=32_768, gt=0, le=1_048_576)
    max_retries: int = Field(default=1, ge=0, le=5)
    temperature: None = None
    max_output_tokens: None = None

    def sanitized_configuration(self) -> Json:
        return {
            "provider": "injected" if self.model == "injected" else "codex",
            "model": self.model,
            "max_output_bytes": self.max_output_bytes,
            "max_retries": self.max_retries,
        }


class _Proposal(RuntimeAIContract):
    id: NonEmptyStr
    name: NonEmptyStr
    arguments: str


class _Answer(RuntimeAIContract):
    content: str
    tool_calls: tuple[_Proposal, ...]


_OUTPUT_SCHEMA = _Answer.model_json_schema()


def decode_codex_response(response: ProviderResponse) -> ProviderResponse:
    """저장된 원문을 그래프의 보고서 또는 조회 제안으로 변환한다."""
    answer = _Answer.model_validate_json(response.content)
    if len({call.id for call in answer.tool_calls}) != len(answer.tool_calls):
        raise ValueError("duplicate Codex tool call id")
    return response.model_copy(
        update={
            "content": answer.content,
            "tool_calls": tuple(
                ToolCall(
                    id=call.id,
                    function=ToolCallFunction(name=call.name, arguments=call.arguments),
                )
                for call in answer.tool_calls
            ),
        }
    )


def _input(
    messages: tuple[ChatMessage, ...], tools: tuple[ToolDefinition, ...] | None
) -> Json:
    text = json.dumps(
        {
            "messages": [m.model_dump(mode="json") for m in messages],
            "tools": [t.model_dump(mode="json") for t in tools or ()],
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return {
        "input": [{"type": "text", "text": text, "text_elements": []}],
        "outputSchema": _OUTPUT_SCHEMA,
    }


class _Completion:
    def __init__(self, thread_id: str):
        self.thread_id = thread_id
        self.turn_id: str | None = None
        self.early: list[Json] = []
        self.status: str | None = None
        self.content: str | None = None

    def bind(self, turn_id: str) -> None:
        self.turn_id = turn_id
        for message in self.early:
            self.observe(message)
        self.early.clear()

    def observe(self, message: Json) -> None:
        if "method" in message and "id" in message:
            raise PreflightError("codex_unexpected_tool")
        method = message.get("method")
        if (
            method not in ("item/completed", "turn/completed")
            or self.status is not None
        ):
            return
        params = message["params"]
        if params.get("threadId") != self.thread_id:
            return
        if self.turn_id is None:
            if len(self.early) >= 32:
                raise ValueError("too many early events")
            self.early.append(message)
            return
        if method == "item/completed" and params["turnId"] == self.turn_id:
            self._item(params["item"])
        elif method == "turn/completed" and params["turn"]["id"] == self.turn_id:
            turn = params["turn"]
            for item in turn.get("items", []):
                self._item(item)
            self.status = turn["status"]

    def _item(self, item: Json) -> None:
        if item["type"] == "agentMessage" and item.get("phase") in (
            None,
            "final_answer",
        ):
            if not isinstance(item.get("text"), str):
                raise ValueError("invalid Codex message")
            self.content = item["text"]
        elif item["type"] not in (
            "userMessage",
            "agentMessage",
            "reasoning",
            "contextCompaction",
        ):
            raise PreflightError("codex_unexpected_tool")


class CodexAdapter:
    def __init__(
        self, settings: CodexSettings, *, clock: Callable[[], float] = time.monotonic
    ):
        self.settings = settings
        self.clock = clock
        self._server: AppServer | None = None
        self._directory: tempfile.TemporaryDirectory[str] | None = None

    @staticmethod
    def input_bytes(
        messages: tuple[ChatMessage, ...], tools: tuple[ToolDefinition, ...] | None
    ) -> bytes:
        return json.dumps(
            _input(messages, tools), ensure_ascii=False, separators=(",", ":")
        ).encode()

    def _session(self, deadline: float) -> tuple[AppServer, Path]:
        if self._server is None:
            self._directory = tempfile.TemporaryDirectory(prefix="hmda-codex-")
            cwd = Path(self._directory.name)
            self._server = AppServer(server_command(), cwd, self.clock)
            try:
                verify_server(self._server, cwd, deadline)
            except BaseException:
                self.close()
                raise
        assert self._directory is not None
        return self._server, Path(self._directory.name)

    def close(self) -> None:
        if self._server is not None:
            self._server.close()
            self._server = None
        if self._directory is not None:
            self._directory.cleanup()
            self._directory = None

    def invoke(
        self,
        messages: tuple[ChatMessage, ...],
        *,
        output_format: Literal["json_object", "text"] = "json_object",
        budget_seconds: float | None = None,
        tools: tuple[ToolDefinition, ...] | None = None,
        tool_choice: Literal["auto", "none"] | None = None,
    ) -> ProviderResponse:
        try:
            return self.invoke_for_turn(
                f"inv-{uuid.uuid4().hex}",
                0,
                messages,
                output_format=output_format,
                budget_seconds=budget_seconds,
                tools=tools,
                tool_choice=tool_choice,
            )
        finally:
            self.close()

    def invoke_for_turn(
        self,
        invocation_id: str,
        logical_turn: int,
        messages: tuple[ChatMessage, ...],
        *,
        output_format: Literal["json_object", "text"] = "json_object",
        budget_seconds: float | None = None,
        tools: tuple[ToolDefinition, ...] | None = None,
        tool_choice: Literal["auto", "none"] | None = None,
    ) -> ProviderResponse:
        started = self.clock()
        budget = 30.0 if budget_seconds is None else budget_seconds
        if not math.isfinite(budget) or budget < 0:
            raise ValueError("budget must be finite and non-negative")
        deadline = started + budget
        attempt: CodexAttempt | None = None
        awaiting_acceptance = False
        rejected: list[int] = []
        attempt_count = 0

        def latency() -> float:
            return max(0, self.clock() - started) * 1000

        def metadata(size: int = 0) -> ProviderResponseMetadata:
            return ProviderResponseMetadata(
                content_bytes=size,
                content_state="text" if size else "content_missing",
                codex_attempt=attempt,
            )

        try:
            if self.clock() >= deadline:
                raise TimeoutError
            server, cwd = self._session(deadline)
            payload = _input(messages, tools if tool_choice != "none" else None)
            while True:
                thread, model = start_thread(server, cwd, self.settings.model, deadline)
                if self.clock() >= deadline:
                    raise TimeoutError
                completion = _Completion(thread)
                attempt = CodexAttempt(
                    invocation_id=invocation_id,
                    logical_turn=logical_turn,
                    request_id=server.next_id,
                    thread_id=thread,
                    model=model,
                    rejected_requests=tuple(rejected),
                )
                attempt_count += 1
                awaiting_acceptance = True
                try:
                    result = server.rpc(
                        "turn/start",
                        {"threadId": thread, **payload},
                        deadline,
                        event=completion.observe,
                    )
                except RpcRejected as err:
                    awaiting_acceptance = False
                    rejected.append(attempt.request_id)
                    attempt = attempt.model_copy(
                        update={"rejected_requests": tuple(rejected)}
                    )
                    if err.code != -32001 or len(rejected) > self.settings.max_retries:
                        raise PreflightError("codex_request_rejected") from err
                    continue
                turn_id = result["turn"]["id"]
                if not isinstance(turn_id, str) or not turn_id:
                    raise ValueError("missing Codex turn id")
                awaiting_acceptance = False
                attempt = attempt.model_copy(update={"turn_id": turn_id})
                completion.bind(turn_id)
                break
            try:
                while completion.status is None:
                    completion.observe(server.read(deadline))
            except TimeoutError:
                grace = self.clock() + 0.5
                attempt = attempt.model_copy(update={"interrupt_requested": True})
                try:
                    server.rpc(
                        "turn/interrupt",
                        {"threadId": thread, "turnId": turn_id},
                        grace,
                        event=completion.observe,
                    )
                except (TimeoutError, EOFError, OSError, RpcRejected):
                    pass
                else:
                    attempt = attempt.model_copy(
                        update={"interrupt_acknowledged": True}
                    )
                try:
                    while completion.status is None:
                        completion.observe(server.read(grace))
                except (TimeoutError, EOFError, OSError):
                    pass
            attempt = attempt.model_copy(
                update={"terminated": completion.status is not None}
            )
            if completion.status != "completed" and not (
                attempt.interrupt_requested and completion.content is not None
            ):
                raise PreflightError(
                    "provider_budget_exhausted"
                    if attempt.interrupt_requested or self.clock() >= deadline
                    else "codex_turn_failed"
                )
            if completion.content is None:
                raise PreflightError("codex_response_missing")
            size = len(completion.content.encode())
            if size > self.settings.max_output_bytes:
                raise ProviderResponseTooLargeError(
                    attempt_count=attempt_count,
                    latency_ms=latency(),
                    actual_bytes=size,
                    max_bytes=self.settings.max_output_bytes,
                    usage=None,
                    trace_id=turn_id,
                    response_metadata=metadata(size),
                )
            return ProviderResponse(
                content=completion.content,
                attempt_count=attempt_count,
                latency_ms=latency(),
                trace_id=turn_id,
                response_metadata=metadata(size),
            )
        except PreflightError as err:
            code = str(err)
        except (OSError, EOFError, RpcRejected, ValueError, TypeError, KeyError) as err:
            if awaiting_acceptance:
                code = "codex_acceptance_unknown"
            elif isinstance(err, TimeoutError):
                code = "provider_budget_exhausted"
            elif attempt is not None and attempt.turn_id is None:
                code = "codex_thread_unavailable"
            elif isinstance(err, ProtocolError):
                code = "codex_protocol_invalid"
            elif attempt is not None:
                code = "codex_turn_disconnected"
            else:
                code = (
                    "codex_app_server_unavailable"
                    if isinstance(err, FileNotFoundError)
                    else "codex_isolation_unverified"
                )
        raise ProviderUnavailableError(
            failure_code=code,
            attempt_count=attempt_count,
            latency_ms=latency(),
            response_metadata=metadata(),
        ) from None
