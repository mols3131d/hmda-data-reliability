"""Provider-neutral AI runtime boundary."""

from hmda_reliability.runtime_ai.contracts import (
    ChatCompletionRequest,
    ChatMessage,
    ProviderResponse,
    ProviderUsage,
    RenderedPrompt,
    TransportResponse,
)
from hmda_reliability.runtime_ai.provider import (
    OpenAICompatibleAdapter,
    ProviderResponseTooLargeError,
    ProviderTransportError,
    ProviderUnavailableError,
)
from hmda_reliability.runtime_ai.settings import RuntimeAISettings

__all__ = [
    "ChatCompletionRequest",
    "ChatMessage",
    "OpenAICompatibleAdapter",
    "ProviderResponse",
    "ProviderResponseTooLargeError",
    "ProviderTransportError",
    "ProviderUnavailableError",
    "ProviderUsage",
    "RenderedPrompt",
    "RuntimeAISettings",
    "TransportResponse",
]
