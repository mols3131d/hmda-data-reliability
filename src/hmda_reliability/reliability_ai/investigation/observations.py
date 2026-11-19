"""로컬 조사 ID에 실제 Langfuse span을 연결하고 명시한 입출력만 투영한다."""

from __future__ import annotations

from typing import Any, Literal

from hmda_reliability.reliability_ai.context import project_remote_output
from hmda_reliability.runtime_ai.contracts import ProviderResponse


class InvestigationTrace:
    def __init__(self, invocation_id: str, *, observe_io: bool) -> None:
        self.invocation_id = invocation_id
        self.observe_io = observe_io
        self.errors: list[str] = []
        self.observations: list[dict[str, Any]] = []
        self.root: Any = None

    @property
    def trace_id(self) -> str | None:
        value = getattr(self.root, "trace_id", None)
        return value if isinstance(value, str) else None

    def start(
        self,
        owner: Any,
        name: str,
        kind: Literal["agent", "generation", "tool"],
        *,
        metadata: dict[str, Any],
        inputs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        if owner is None:
            return None
        if self.observe_io and inputs is not None:
            projected = project_remote_output(inputs)
            kwargs["input"] = (
                projected["messages"] if "messages" in inputs else projected
            )
        try:
            span = owner.start_observation(
                name=name,
                as_type=kind,
                metadata={"invocation_id": self.invocation_id, **metadata},
                **kwargs,
            )
            span_id = getattr(span, "id", None)
            if isinstance(span_id, str):
                self.observations.append(
                    {
                        "id": span_id,
                        "kind": kind,
                        "name": name,
                        **{
                            key: metadata[key]
                            for key in ("turn", "call_id")
                            if key in metadata
                        },
                    }
                )
            if kind == "agent":
                self.root = span
            return span
        except Exception:
            self.errors.append("observation_start_failed")
            return None

    def update(
        self, span: Any, *, output: dict[str, Any] | None = None, **kwargs: Any
    ) -> None:
        if span is None:
            return
        try:
            if self.observe_io and output is not None:
                kwargs["output"] = project_remote_output(output)
            span.update(**kwargs)
        except Exception:
            self.errors.append("observation_update_failed")

    def end(self, span: Any) -> None:
        if span is None:
            return
        try:
            span.end()
        except Exception:
            self.errors.append("observation_end_failed")

    def retained_model(
        self, span: Any, turn: int, response: ProviderResponse, failure_code: str | None
    ) -> None:
        usage = response.usage
        self.update(
            span,
            output={
                "role": "assistant",
                "content": response.content,
                "tool_calls": [c.model_dump(mode="json") for c in response.tool_calls],
            }
            if self.observe_io
            else None,
            usage_details=(
                {
                    key: value
                    for key, value in (
                        ("input", usage.prompt_tokens),
                        ("output", usage.completion_tokens),
                        ("total", usage.total_tokens),
                    )
                    if value is not None
                }
                if usage is not None
                else None
            ),
            metadata={
                "turn": turn,
                "attempt_count": response.attempt_count,
                "latency_ms": response.latency_ms,
            },
            **(
                {"level": "ERROR", "status_message": failure_code}
                if failure_code
                else {}
            ),
        )
        self.end(span)
