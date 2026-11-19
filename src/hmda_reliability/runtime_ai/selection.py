"""공개 조사 API와 실험 CLI의 제공자 선택 경계."""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping
from typing import Literal, Protocol

from hmda_reliability.runtime_ai.codex import CodexAdapter
from hmda_reliability.runtime_ai.codex import CodexSettings as CodexSettings
from hmda_reliability.runtime_ai.contracts import (
    ChatMessage,
    ProviderResponse,
    ToolDefinition,
)
from hmda_reliability.runtime_ai.provider import OpenAICompatibleAdapter
from hmda_reliability.runtime_ai.settings import RuntimeAISettings


class InvestigationProvider(Protocol):
    def invoke(
        self,
        messages: tuple[ChatMessage, ...],
        *,
        output_format: Literal["json_object", "text"] = "json_object",
        budget_seconds: float | None = None,
        tools: tuple[ToolDefinition, ...] | None = None,
        tool_choice: Literal["auto", "none"] | None = None,
    ) -> ProviderResponse: ...


def resolve_investigation_provider(
    settings: RuntimeAISettings | CodexSettings | None,
    provider: InvestigationProvider | None,
    clock: Callable[[], float] = time.monotonic,
) -> tuple[RuntimeAISettings | CodexSettings, InvestigationProvider]:
    if settings is None and isinstance(
        provider, (CodexAdapter, OpenAICompatibleAdapter)
    ):
        settings = provider.settings
    active = settings or CodexSettings(
        model="injected" if provider is not None else "codex-default"
    )
    if provider is not None:
        return active, provider
    if isinstance(active, RuntimeAISettings):
        return active, OpenAICompatibleAdapter(active, clock=clock)
    return active, CodexAdapter(active, clock=clock)


def cli_provider_settings(
    provider: str | None,
    model: str | None,
    base_url: str | None,
    max_output_tokens: int | None,
    environ: Mapping[str, str],
) -> RuntimeAISettings | CodexSettings:
    url = base_url or environ.get("OPENAI_BASE_URL")
    selected = provider or ("compatible" if url else "codex")
    if selected == "codex":
        if base_url is not None:
            raise ValueError("--base-url requires a compatible provider")
        if max_output_tokens is not None:
            raise ValueError("--max-output-tokens is unavailable for Codex App Server")
        return CodexSettings(model=model or "codex-default")
    if selected == "ollama":
        url = base_url or "http://localhost:11434/v1"
        key = "local"
    elif selected == "compatible" and url:
        key = environ.get("OPENAI_API_KEY", "local")
    else:
        raise ValueError("--provider compatible requires a base URL")
    return RuntimeAISettings.model_validate(
        {
            "base_url": url,
            "api_key": key,
            "model": model or "qwen3.5:4b-8k-local",
            "max_output_tokens": max_output_tokens
            if max_output_tokens is not None
            else 4096,
            "connect_timeout_seconds": 10,
            "read_timeout_seconds": 300,
            "max_retries": 0,
        }
    )
